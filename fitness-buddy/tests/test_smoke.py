"""End-to-end HTTP smoke checks using a fresh temporary database per test."""
import json
import sqlite3
import sys
import tempfile
import threading
import unittest
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import initialize, make_server


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'test.db'
        self.server = make_server(self.db, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, path, data=None, raw=None, headers=None):
        body = raw if raw is not None else json.dumps(data).encode() if data is not None else None
        request = Request(self.url + path, body, headers or ({'Content-Type': 'application/json'} if body is not None else {}))
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            content = response.read()
            return response.status, json.loads(content) if response.headers.get_content_type() == 'application/json' else content

    def state(self):
        status, data = self.request('/api/state')
        self.assertEqual(status, 200)
        return data

    def event(self):
        return dict(title='Beginner workout', activity='Gym', location='Public lobby',
                    day=(date.today()+timedelta(days=2)).isoformat(), time='18:30', capacity=3)

    def test_01_health_and_static_assets(self):
        self.assertEqual(self.request('/api/health'), (200, {'status': 'ok'}))
        for path, expected in [('/', b'Fitness Buddy'), ('/app.js', b'renderMatches'), ('/style.css', b'@media')]:
            status, body = self.request(path)
            self.assertEqual(status, 200)
            self.assertIn(expected, body)

    def test_02_seeded_matches_are_explained_and_ranked(self):
        state = self.state()
        self.assertEqual(len(state['matches']), 4)
        self.assertEqual(state['matches'][0]['name'], 'Alex (demo)')
        self.assertEqual(state['matches'][0]['score'], 4)
        self.assertIn('Shared availability', state['matches'][0]['reasons'])
        self.assertEqual(state['interest_count'], 0)

    def test_03_profile_change_updates_matching(self):
        profile = dict(name='Tester', activity='Running', slot='Weekend mornings', level='Intermediate', area='Downtown')
        self.assertEqual(self.request('/api/profile', profile)[0], 200)
        state = self.state()
        self.assertEqual(state['profile']['name'], 'Tester')
        self.assertEqual(state['matches'][0]['name'], 'Sam (demo)')
        self.assertEqual(state['matches'][0]['score'], 4)

    def test_04_invalid_profile_does_not_change_saved_data(self):
        profile = self.state()['profile']
        self.assertEqual(self.request('/api/profile', {**profile, 'activity':'Invalid'})[0], 400)
        self.assertEqual(self.state()['profile'], profile)

    def test_05_create_meetup_and_enroll_creator(self):
        status, result = self.request('/api/meetups', self.event())
        self.assertEqual(status, 201)
        event = next(e for e in self.state()['meetups'] if e['id'] == result['id'])
        self.assertEqual((event['attendees'], event['joined'], event['seeded']), (1,1,0))

    def test_06_join_is_idempotent_and_leave_works(self):
        for _ in range(2):
            self.assertEqual(self.request('/api/meetups/1/join', {})[0], 200)
        self.assertEqual(self.state()['meetups'][0]['attendees'], 2)
        for _ in range(2):
            self.assertEqual(self.request('/api/meetups/1/leave', {})[0], 200)
        self.assertEqual(self.state()['meetups'][0]['attendees'], 1)

    def test_07_full_meetup_rejects_join(self):
        with sqlite3.connect(self.db) as db:
            db.execute('UPDATE meetups SET capacity=2 WHERE id=1')
            db.execute('INSERT INTO attendance VALUES (1,3)')
        self.assertEqual(self.request('/api/meetups/1/join', {})[0], 409)
        self.assertEqual(self.state()['meetups'][0]['attendees'], 2)

    def test_08_unknown_meetup(self):
        self.assertEqual(self.request('/api/meetups/999/join', {})[0], 404)

    def test_09_bad_meetup_inputs_leave_database_unchanged(self):
        for change in [{'title':''}, {'day':'2000-01-01'}, {'day':'2027-02-30'}, {'capacity':0},
                       {'capacity':2.5}, {'capacity':True}, {'time':'25:00'}, {'location':''}]:
            with self.subTest(change=change):
                self.assertEqual(self.request('/api/meetups', {**self.event(), **change})[0], 400)
        self.assertEqual(len(self.state()['meetups']), 1)

    def test_10_interest_is_unique_and_persisted(self):
        self.assertEqual(self.request('/api/interest', {'email':'Tester@example.com','consent':True})[0], 201)
        self.assertEqual(self.request('/api/interest', {'email':'tester@example.com','consent':True})[0], 200)
        self.assertEqual(self.state()['interest_count'], 1)
        self.assertNotIn('tester@example.com', json.dumps(self.state()))

    def test_11_interest_requires_email_and_consent(self):
        for data in [{'email':'bad','consent':True}, {'email':'a@example.com','consent':False},
                     {'email':'a@example.com','consent':'true'}]:
            self.assertEqual(self.request('/api/interest', data)[0], 400)
        self.assertEqual(self.state()['interest_count'], 0)

    def test_12_malformed_json_and_wrong_content_type(self):
        self.assertEqual(self.request('/api/profile', raw=b'{')[0], 400)
        self.assertEqual(self.request('/api/profile', [1,2])[0], 400)
        self.assertEqual(self.request('/api/profile', raw=b'{}', headers={'Content-Type':'text/plain'})[0], 415)
        self.assertEqual(self.request('/api/profile', raw=b'x'*8193)[0], 400)

    def test_13_private_files_and_unknown_routes_are_not_served(self):
        for path in ['/app.py', '/fitness.db', '/../app.py', '/missing', '/api/missing']:
            self.assertEqual(self.request(path)[0], 404)
        self.assertEqual(self.request('/api/missing', {})[0], 404)

    def test_14_cross_origin_write_is_blocked(self):
        self.assertEqual(self.request('/api/interest', {'email':'x@example.com', 'consent':True},
                         headers={'Content-Type':'application/json','Origin':'https://example.com'})[0], 403)

    def test_15_restart_retains_changes_without_reseeding(self):
        profile = {**self.state()['profile'], 'name':'Saved tester'}
        self.request('/api/profile', profile)
        self.request('/api/meetups', self.event())
        self.request('/api/interest', {'email':'saved@example.com','consent':True})
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        self.server = make_server(self.db, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start(); self.url = f'http://127.0.0.1:{self.server.server_port}'
        state = self.state()
        self.assertEqual(state['profile']['name'], 'Saved tester')
        self.assertEqual(len(state['meetups']), 2)
        self.assertEqual(state['interest_count'], 1)
        self.assertEqual(len(state['matches']), 4)

    def test_16_expired_meetup_cannot_be_joined(self):
        with sqlite3.connect(self.db) as db:
            db.execute("UPDATE meetups SET day='2000-01-01' WHERE id=1")
        self.assertEqual(self.request('/api/meetups/1/join', {})[0], 409)


if __name__ == '__main__':
    unittest.main(verbosity=2)
