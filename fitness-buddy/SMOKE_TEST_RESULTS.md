# Smoke test results

Run date: October 22, 2026.

## Netlify update: 15/15 additional checks passed

Command: `node --test tests/test_netlify.cjs`, Node.js v24.19.0.

Actual result: 15 tests, 15 passed, 0 failed; duration 113.215901 ms. Syntax checks for `netlify-site/app.js` and `netlify-site/store.js` also passed.

Coverage: initial fictional matches, profile persistence/reranking, rejected profile changes, meetup creation/persistence, repeat join/leave behavior, capacity, expiry/missing events, invalid fields, independent browser stores, corrupt/blocked/full storage handling, static asset references, Netlify form declarations, and absence of a Python API dependency.

These checks use isolated browser-storage substitutes and inspect static deployment files. They are not browser rendering tests and do not verify Netlify's hosted processing. The site has not been deployed and the real form submission flow remains unverified. Follow NETLIFY_DEPLOY.md after uploading. The original Python test results below apply to the Python version only.

## Executed: 16/16 HTTP smoke tests passed

Environment: Python 3.12.14 on Linux. Every test used a running HTTP server and a separate temporary SQLite database.

Command: `python3 -m unittest discover -s tests -v`

Actual runner summary: `Ran 16 tests in 8.782s` / `OK`.

| Check | Result |
| --- | --- |
| Health endpoint and HTML/JS/CSS delivery | PASS |
| Fictional partner ranking and explanations | PASS |
| Profile changes affect matching | PASS |
| Invalid profile does not overwrite stored values | PASS |
| Meetup creation includes creator attendance | PASS |
| Repeat join/leave requests preserve correct attendance | PASS |
| Full meetup rejects an additional participant | PASS |
| Unknown meetup returns 404 | PASS |
| Invalid dates, times, capacities, and blank fields rejected | PASS |
| Interest emails are deduplicated and excluded from public state | PASS |
| Invalid email or missing consent rejected | PASS |
| Malformed JSON, oversized body, and wrong content type rejected | PASS |
| Private files and unknown routes unavailable | PASS |
| Cross-origin browser write rejected | PASS |
| Server restart preserves saved data without duplicate seeds | PASS |
| Expired meetup rejects joining | PASS |

## Executed: JavaScript syntax check passed

Command: `node --check static/app.js`, with Node.js v24.19.0. Exit status 0.

## Not executed successfully: browser checks

The optional `tests/browser_smoke.cjs` suite was attempted but could not launch because the Playwright Chromium executable was absent. A browser installation attempt failed when the download did not produce a valid archive. The browser checks therefore have **no passing result** from this environment.

The script covers initial rendering, profile save and reranking, availability filtering, meetup creation, join/leave, interest submission, reload persistence, literal handling of user text, mobile overflow, and JavaScript runtime errors. Follow the optional browser instructions in README.md to run it with an installed browser. Visual layout and browser interactions remain unverified here.

## Scope of evidence

The successful checks establish a basic local HTTP/data smoke-test baseline. They do not establish production security, performance, accessibility compliance, cross-browser behavior, multi-user reliability, or customer demand. No real participants were recruited, no emails were sent, and no customer traction was measured.
