# Fitness Buddy — starter prototype

## Deploy on Netlify

The package now includes a ready-to-upload **`netlify-site`** folder. Extract this ZIP and upload that folder to https://app.netlify.com/drop. It contains `index.html` at its top level. No Python or build command is required for this version.

Read **NETLIFY_DEPLOY.md** for form activation, where to find pilot-interest submissions, local preview, and post-deployment smoke tests. The original Python version and its instructions remain below. Netlify uses browser storage for demo progress, and Netlify Forms for submitted pilot interest; it does not use the Python database.

A small local prototype based on your fitness-social-app presentation and the three supplied interviews. **Fitness Buddy is a working title**, not a company name taken from the slides. The interviews suggest schedule compatibility and beginner confidence are worth testing; they do not establish broad demand.

## Run it on Windows

1. Extract the ZIP, then open the `fitness-buddy` folder.
2. In that folder, open a terminal (File Explorer address bar: type `powershell`, press Enter).
3. Check Python: `py --version`. Use Python 3.10 or newer.
4. Start the app:

```powershell
py app.py
```

5. Open **http://127.0.0.1:8000** in your browser. Keep the terminal open.
6. Stop with **Ctrl+C**.

If `py` is not recognized but Python is installed, try `python app.py`. If neither command exists, install Python 3, reopen the terminal, and retry. macOS/Linux: `python3 app.py`.

No pip install, API keys, database service, or internet connection is needed to run the app. Do not open `index.html` directly: the Python server supplies the API.

If port 8000 is occupied: `py app.py --port 8001`, then open http://127.0.0.1:8001.

## Run the smoke tests

From the same folder:

```powershell
py -m unittest discover -s tests -v
```

Expected final output: `Ran 16 tests` followed by `OK`.

You do not need to start the app first. Each test starts its own HTTP server on an available port and uses a temporary SQLite database. Tests do not change your demo data.

These check startup, static assets, matching, profile changes, meetup creation, joining/leaving, capacity, expired events, invalid input, consent, duplicate interest records, database persistence, and private-file protection. See `SMOKE_TEST_RESULTS.md` for the actual execution results.

## What you can try

1. Save a profile with Running / Weekend mornings / Intermediate / Downtown. Sam should rank first, with 4/4 matching preferences.
2. Select “Shared availability only.” Only matching schedules should remain.
3. Create a meetup for a future day. It should show 1 attendee: you.
4. Leave it, then join it again. Reload the page: your attendance should remain.
5. Submit a test email with consent. Submit it again: the local count should not increase twice.

## Files and how they fit together

| File | Purpose |
| --- | --- |
| `app.py` | HTTP server, API routes, validation, SQLite storage, matching rules |
| `static/index.html` | Page structure and forms |
| `static/style.css` | Responsive styling |
| `static/app.js` | Form requests, partner and meetup rendering |
| `tests/test_smoke.py` | 16 repeatable HTTP smoke tests; standard library only |
| `tests/browser_smoke.cjs` | Optional Playwright browser-flow checks |
| `CUSTOMER_SMOKE_TEST_PLAN.md` | Small experiment to test customer interest |
| `customer-test-log.csv` | Blank participant observation sheet |
| `SMOKE_TEST_RESULTS.md` | Recorded software test results and limitations |

Browser → `fetch()` → Python API → SQLite database → JSON response → updated page.

Matching is intentionally simple: one point each for matching activity, availability, experience level, and area. There is no AI model or claimed probability of compatibility. Reasons appear on each card. Filter by shared availability when timing is essential.

## API reference

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Server/database check |
| GET | `/api/state` | Profile, ranked demo partners, meetups, local interest count |
| POST | `/api/profile` | Save name, activity, slot, level, area |
| POST | `/api/meetups` | Save title, activity, location, day, time, capacity |
| POST | `/api/meetups/{id}/join` | Join; repeated requests do not add extra attendance |
| POST | `/api/meetups/{id}/leave` | Leave |
| POST | `/api/interest` | Record email with boolean consent; deduplicate case-insensitively |

POST requests use `Content-Type: application/json`. Meetup dates must be after today; capacity is an integer from 2 to 20. Date/time use the server computer's local timezone. Broad availability labels are placeholders for a future real scheduling system.

## Data and scope

The server listens only on `127.0.0.1`. This is a **single-user local demo**, with one shared editable profile and four fictional partners. There are no accounts, real invitations, messaging, calendar bookings, location services, moderation, or email sending. The local interest counter is not verified traction.

Your changes persist in `fitness.db`, created on first run. The ZIP contains no database or test email addresses. To start a separate demonstration without changing your saved data, use `py app.py --db another-demo.db`. To reset a disposable demo, stop the server and delete only its chosen database file.

The interest form stores consented email addresses on your computer. Prefer dummy emails during software testing. For participant sessions, explain local storage and delete their details when the exercise is complete. Do not publish this server as a multi-user service; a public version needs authentication, separate user records, deployment infrastructure, and appropriate data handling.

## Optional automated browser checks

These require Node.js, Playwright, and its Chromium browser; the Python tests do not.

```powershell
npm install --no-save playwright
npx playwright install chromium
py app.py --port 8002 --db browser-test.db
```

In a second terminal in this folder:

```powershell
$env:TEST_URL = 'http://127.0.0.1:8002'
node tests/browser_smoke.cjs
```

Use a fresh disposable database each time; browser checks intentionally save test data. After stopping that test server, you may delete `browser-test.db`. On macOS/Linux the second command is `TEST_URL=http://127.0.0.1:8002 node tests/browser_smoke.cjs`.

## Suggested next implementation step

Use the customer test plan to find out whether people will commit to a session. If the signal is useful, replace fictional profiles with separate authenticated users and introduce connection requests before adding a social feed.
