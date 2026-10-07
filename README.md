# backtiming

Plan backwards from the big days.

When a big event is coming up (a wedding, a launch, a move, an exam), the prep usually has to start well before the date. backtiming takes the event and the list of things you think you'll need to do, then works backwards from the deadline and books that prep time into the free gaps of your Google Calendar. Prep blocks go into a separate `backtiming` calendar, so you can show or hide them with one click and your own events are never touched.

backtiming is open source and self-hosted: you run it on your own machine with your own Google account.

## How it works

1. **Add an event** — title, date/time, and how far ahead you want to start preparing. Pick a template (wedding, move, exam, interview, trip, launch) to prefill the prep list.
2. **List the prep tasks** — each with an estimated duration and an optional "must be done by" offset (e.g. "buy suit — 2h — at least 7 days before").
3. **Read your calendar** — backtiming pulls your busy times between now and the event.
4. **Allocate** — tasks are placed into free slots, latest-deadline-first working backwards, with a small buffer around existing events. By default any time is fair game (24/7).
5. **Reuse** — save any event's tasks as a template for next time.
6. **Review and push** — you see the proposed blocks, adjust if needed, then write them to the `backtiming` calendar.

## Stack

- Backend: Python 3.12+, FastAPI, SQLite
- Calendar: Google Calendar API (read free/busy, write prep blocks)
- Frontend: a single static HTML page with plain JavaScript, served by the backend

## Getting started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open http://localhost:8000 (use `--port 8765` if 8000 is taken).

Without a `credentials.json`, backtiming runs in **demo mode**: busy times are simulated (weekdays 9–17, dinner 19–20) and pushing to Google is disabled. It's the quickest way to try it out.

Run the tests with `pytest`.

### Google Calendar access

1. Create a project in Google Cloud Console and enable the Google Calendar API.
2. Create an OAuth client ID (Desktop app) and download it as `credentials.json` in the project root.
3. On first run you'll be asked to sign in; a `token.json` is saved locally.

Both files are gitignored — never commit them.

## Status

Early. Backend first, then the minimal frontend. See [TODO.md](TODO.md) for the roadmap.

## License

[MIT](LICENSE)
