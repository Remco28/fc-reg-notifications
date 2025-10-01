# Next Steps for Fencing Club Registration Notifications

## Phase 1: User Accounts & Tracked Clubs (Complete)
- [x] Ship username/password authentication with bcrypt hashing and persisted sessions.
- [x] Provide user-facing dashboard, tracked club management UI, and weapon filters.
- [x] Deliver daily digest generation plus CLI helpers (`digest-scheduler`, `send-user-digest`).
- [x] Add admin panel for user oversight and CLI bootstrap command (`create-admin`).

## Phase 2: Fencer Tracking (In Planning)
- [ ] Finalize functional spec for tracked fencers and search UX.
- [ ] Extend schema with `tracked_fencers` and fencer identifiers from fencingtracker profiles.
- [ ] Update scraper/digest logic to populate the "Tracked Fencers" digest section.
- [ ] Add UI workflows for adding, editing, and deactivating tracked fencers.
- [ ] Expand tests to cover fencer lookups and digest de-duplication across club/fencer sections.

## Operational Follow-Ups
- [ ] Configure domain-based Mailgun sending (SPF/DKIM/DMARC) and verify delivery from the new templates.
- [ ] Capture bounce/complaint handling approach (manual for now) and document the playbook.
- [ ] Add environment documentation for `ADMIN_EMAIL`, digest scheduler process management, and secure cookie settings in deployment notes.
- [ ] Schedule live end-to-end test of digest flow once production Mailgun sender is active.

## Documentation & Tooling
- [ ] Publish initial API/UI usage doc (FastAPI docs or internal runbook) summarizing auth, club management, and admin endpoints.
- [ ] Introduce automated schema migrations (Alembic) before Phase 2 to manage future model changes.
