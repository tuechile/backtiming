# TODO

## Now

- [x] Pure scheduler: backtime tasks into free slots (24/7, buffer, chunking, unplaced report)
- [x] SQLite storage for events and tasks
- [x] Google OAuth + read busy times from all calendars
- [x] Create/reuse the dedicated `backtiming` calendar and write allocations to it
- [x] FastAPI routes: events, tasks, preview allocation, confirm/push
- [x] Minimal `index.html` to drive the flow

## Next

- [ ] Reusable task templates per event type (e.g. wedding, move, launch, exam)
- [ ] Re-run allocation when the calendar changes; update or remove stale blocks
- [ ] Settings page:
  - [ ] Available hours per weekday (default 24/7)
  - [ ] Blocked times (e.g. sleep, commute)
  - [ ] Buffer size and minimum chunk length
  - [ ] Timezone

## Later

- [ ] One-command install for non-developers (e.g. Docker or a packaged app)
- [ ] Shareable / community template library
- [ ] Suggest prep tasks for a new event type with an LLM
- [ ] Other calendar providers (iCloud, Outlook)
- [ ] Hosted multi-user version

## Verify

- [ ] Test the Google flow end to end with a real credentials.json
