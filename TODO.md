# TODO

## Now

- [x] Pure scheduler: backtime tasks into free slots (24/7, buffer, chunking, unplaced report)
- [x] SQLite storage for events and tasks
- [x] Google OAuth + read busy times from all calendars
- [x] Create/reuse the dedicated `backtiming` calendar and write allocations to it
- [x] FastAPI routes: events, tasks, preview allocation, confirm/push
- [x] Minimal `index.html` to drive the flow

## Next

- [x] Reusable task templates per event type (e.g. wedding, move, launch, exam)
- [ ] Edit a template's tasks directly (today: apply, tweak, save under the same name)
- [ ] Re-run allocation when the calendar changes; update or remove stale blocks
- [ ] Settings page:
  - [x] Sleep hours (default 02:00–09:00, can be turned off)
  - [ ] Weekly blocked times (e.g. work, commute, gym), per weekday
  - [ ] Daily cap on prep time (e.g. at most 3h/day)
  - [ ] Buffer size and minimum chunk length
  - [ ] Timezone (today: the machine's local time)
  - [ ] Which Google calendars count as busy
  - [ ] Scheduling style: as late as possible vs. spread out evenly

## Later

- [ ] One-command install for non-developers (e.g. Docker or a packaged app)
- [ ] Shareable / community template library
- [ ] Suggest prep tasks for a new event type with an LLM
- [ ] Other calendar providers (iCloud, Outlook)
- [ ] Hosted multi-user version

## Verify

- [ ] Test the Google flow end to end with a real credentials.json
