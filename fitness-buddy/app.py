"""Local fitness-buddy prototype. Python standard library only."""
import argparse
import json
import re
import sqlite3
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
ACTIVITIES = ('Gym', 'Running', 'Fitness classes')
SLOTS = ('Weekday mornings', 'Weekday evenings', 'Weekend mornings')
LEVELS = ('Beginner', 'Intermediate', 'Experienced')
AREAS = ('Campus', 'Downtown', 'West Ottawa')


def connect(path):
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    return db


def initialize(path):
    with connect(path) as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, activity TEXT NOT NULL,
            slot TEXT NOT NULL, level TEXT NOT NULL, area TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS meetups (
            id INTEGER PRIMARY KEY, title TEXT NOT NULL, activity TEXT NOT NULL,
            location TEXT NOT NULL, day TEXT NOT NULL, time TEXT NOT NULL,
            capacity INTEGER NOT NULL CHECK(capacity BETWEEN 2 AND 20),
            seeded INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS attendance (
            meetup_id INTEGER REFERENCES meetups(id),
            profile_id INTEGER REFERENCES profiles(id),
            PRIMARY KEY(meetup_id, profile_id));
        CREATE TABLE IF NOT EXISTS interest (
            email TEXT PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT);
        ''')
        if not db.execute("SELECT 1 FROM metadata WHERE key='seeded'").fetchone():
            people = [
                (1, 'You', 'Gym', 'Weekday evenings', 'Beginner', 'Campus'),
                (2, 'Alex (demo)', 'Gym', 'Weekday evenings', 'Beginner', 'Campus'),
                (3, 'Sam (demo)', 'Running', 'Weekend mornings', 'Intermediate', 'Downtown'),
                (4, 'Jordan (demo)', 'Fitness classes', 'Weekday evenings', 'Beginner', 'Campus'),
                (5, 'Casey (demo)', 'Gym', 'Weekday mornings', 'Experienced', 'West Ottawa'),
            ]
            db.executemany('INSERT INTO profiles VALUES (?, ?, ?, ?, ?, ?)', people)
            db.execute('INSERT INTO meetups(title,activity,location,day,time,capacity,seeded) VALUES (?,?,?,?,?,?,1)',
                       ('First gym session', 'Gym', 'Campus recreation lobby (demo)',
                        (date.today() + timedelta(days=3)).isoformat(), '18:00', 4))
            db.execute('INSERT INTO attendance VALUES (1,2)')
            db.execute("INSERT INTO metadata VALUES ('seeded','yes')")


def required_text(data, key, limit=80):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise ValueError(f'{key}: enter 1–{limit} characters.')
    return value.strip()


def choice(data, key, options):
    value = required_text(data, key)
    if value not in options:
        raise ValueError(f'{key}: choose one of the listed options.')
    return value


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass  # Do not log request bodies or email addresses.

    def reply(self, status, payload, content_type='application/json; charset=utf-8'):
        body = json.dumps(payload).encode() if content_type.startswith('application/json') else payload
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        assets = {'/': ('index.html', 'text/html; charset=utf-8'),
                  '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                  '/style.css': ('style.css', 'text/css; charset=utf-8')}
        if path in assets:
            filename, mime = assets[path]
            return self.reply(200, (ROOT / 'static' / filename).read_bytes(), mime)
        with connect(self.server.db_path) as db:
            if path == '/api/health':
                db.execute('SELECT 1')
                return self.reply(200, {'status': 'ok'})
            if path == '/api/state':
                me = dict(db.execute('SELECT * FROM profiles WHERE id=1').fetchone())
                matches = []
                for row in db.execute('SELECT * FROM profiles WHERE id<>1'):
                    person = dict(row)
                    reasons = [label for key, label in [('activity', 'Same activity'), ('slot', 'Shared availability'),
                               ('area', 'Same area'), ('level', 'Same experience level')] if person[key] == me[key]]
                    person.update(score=len(reasons), reasons=reasons)
                    matches.append(person)
                matches.sort(key=lambda p: (-p['score'], p['name']))
                events = [dict(row) for row in db.execute('''
                    SELECT m.*, (SELECT count(*) FROM attendance a WHERE a.meetup_id=m.id) AS attendees,
                    EXISTS(SELECT 1 FROM attendance a WHERE a.meetup_id=m.id AND a.profile_id=1) AS joined
                    FROM meetups m ORDER BY day, time, id''')]
                return self.reply(200, {'profile': me, 'matches': matches, 'meetups': events,
                                       'interest_count': db.execute('SELECT count(*) FROM interest').fetchone()[0]})
        self.reply(404, {'error': 'Not found.'})

    def do_POST(self):
        # JSON-only local API; reject cross-origin browser writes.
        origin = self.headers.get('Origin')
        if origin and origin != 'http://' + self.headers.get('Host', ''):
            return self.reply(403, {'error': 'Cross-origin requests are not allowed.'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.reply(415, {'error': 'Send application/json.'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 8192:
                raise ValueError('Request body must be between 1 and 8192 bytes.')
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError('Request body must be an object.')
            with connect(self.server.db_path) as db:
                self.mutate(db, urlsplit(self.path).path, data)
        except (ValueError, UnicodeDecodeError) as exc:
            self.reply(400, {'error': str(exc)})
        except sqlite3.Error:
            self.reply(500, {'error': 'Database operation failed.'})

    def mutate(self, db, path, data):
        if path == '/api/profile':
            values = (required_text(data, 'name', 40), choice(data, 'activity', ACTIVITIES),
                      choice(data, 'slot', SLOTS), choice(data, 'level', LEVELS), choice(data, 'area', AREAS))
            db.execute('UPDATE profiles SET name=?, activity=?, slot=?, level=?, area=? WHERE id=1', values)
            db.commit()
            return self.reply(200, {'message': 'Profile saved. Matches updated.'})
        if path == '/api/meetups':
            title = required_text(data, 'title')
            activity = choice(data, 'activity', ACTIVITIES)
            location = required_text(data, 'location', 120)
            day = required_text(data, 'day', 10)
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', day) or date.fromisoformat(day) <= date.today():
                raise ValueError('Choose a date after today.')
            time = required_text(data, 'time', 5)
            if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', time):
                raise ValueError('Enter a valid 24-hour time.')
            capacity = data.get('capacity')
            if type(capacity) is not int or not 2 <= capacity <= 20:
                raise ValueError('Capacity must be a whole number from 2 to 20.')
            cursor = db.execute('INSERT INTO meetups(title,activity,location,day,time,capacity) VALUES (?,?,?,?,?,?)',
                                (title, activity, location, day, time, capacity))
            db.execute('INSERT INTO attendance VALUES (?,1)', (cursor.lastrowid,))
            db.commit()
            return self.reply(201, {'id': cursor.lastrowid, 'message': 'Meetup created. You are attending.'})
        action = re.fullmatch(r'/api/meetups/(\d+)/(join|leave)', path)
        if action:
            event_id, verb = int(action[1]), action[2]
            db.execute('BEGIN IMMEDIATE')  # Capacity check and insert are one write transaction.
            event = db.execute('SELECT * FROM meetups WHERE id=?', (event_id,)).fetchone()
            if not event:
                return self.reply(404, {'error': 'Meetup not found.'})
            if verb == 'leave':
                db.execute('DELETE FROM attendance WHERE meetup_id=? AND profile_id=1', (event_id,))
            else:
                if datetime.fromisoformat(event['day'] + 'T' + event['time']) <= datetime.now():
                    return self.reply(409, {'error': 'This meetup has ended.'})
                joined = db.execute('SELECT 1 FROM attendance WHERE meetup_id=? AND profile_id=1', (event_id,)).fetchone()
                count = db.execute('SELECT count(*) FROM attendance WHERE meetup_id=?', (event_id,)).fetchone()[0]
                if not joined and count >= event['capacity']:
                    return self.reply(409, {'error': 'This meetup is full.'})
                db.execute('INSERT OR IGNORE INTO attendance VALUES (?,1)', (event_id,))
            db.commit()
            return self.reply(200, {'message': 'Joined meetup.' if verb == 'join' else 'Left meetup.'})
        if path == '/api/interest':
            if data.get('consent') is not True:
                raise ValueError('Please consent before saving your email.')
            email = required_text(data, 'email', 254).lower()
            if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
                raise ValueError('Enter a valid email address.')
            cursor = db.execute('INSERT OR IGNORE INTO interest(email) VALUES (?)', (email,))
            created = cursor.rowcount == 1
            db.commit()
            return self.reply(201 if created else 200, {'message': 'Interest saved locally. No email was sent.'})
        self.reply(404, {'error': 'Not found.'})


def make_server(path, port=8000):
    initialize(path)
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.db_path = str(path)
    return server


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--db', default=str(ROOT / 'fitness.db'))
    args = parser.parse_args()
    server = make_server(args.db, args.port)
    print(f'Fitness Buddy: http://127.0.0.1:{server.server_port} (Ctrl+C to stop)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
