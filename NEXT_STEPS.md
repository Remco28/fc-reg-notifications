# Next Steps for Fencing Club Registration Notifications

## Phase 1: User Accounts & Tracked Clubs (Complete)
- [x] Ship username/password authentication with bcrypt hashing and persisted sessions.
- [x] Provide user-facing dashboard, tracked club management UI, and weapon filters.
- [x] Deliver daily digest generation plus CLI helpers (`digest-scheduler`, `send-user-digest`).
- [x] Add admin panel for user oversight and CLI bootstrap command (`create-admin`).

## Phase 2: Fencer Tracking (COMPLETE ✅)
- [x] Finalize functional spec for tracked fencers and search UX (`comms/tasks/archive/2025-10-05-tracked-fencer-backend-spec.md`).
- [x] Extend schema with `tracked_fencers` and fencer identifiers from fencingtracker profiles (migrations applied).
- [x] Update scraper/digest logic to populate the "Tracked Fencers" digest section (hash caching + dedupe live).
- [x] Add UI workflows for adding, editing, and deactivating tracked fencers (`comms/tasks/archive/2025-10-06-tracked-fencer-ui-session-flow.md`).
- [x] Expand tests to cover fencer lookups and digest de-duplication across club/fencer sections (`comms/tasks/archive/2025-10-06-phase2-testing-verification.md`).
  - [x] Added service-level tests for scraper cooldown and digest generation (`tests/services/`).
  - [x] Added CRUD and validation regression tests (`tests/test_crud_tracked_fencers.py`, `tests/services/test_fencer_validation_service.py`).
  - [x] Added UI tests for dashboard rendering and form submissions (`tests/test_tracked_fencer_routes.py`).
  - [x] Added E2E smoke test for the complete fencer tracking flow (`tests/e2e/test_tracked_fencer_flow.py`).
  - [x] Created testing documentation (`docs/TESTING.md`).
- [x] **End-to-end production readiness testing** (`comms/tasks/2025-10-03-phase2-end-to-end-testing.md`)
  - [x] Fixed database schema migration issues
  - [x] Fixed fencer profile URL generation (slug handling)
  - [x] Simplified fencer tracking to URL-only input
  - [x] Fixed scraper to exclude Results tables
  - [x] Added DELETE functionality for tracked fencers
  - [x] Verified digest delivery with correct data

## Operational Follow-Ups
- [x] Document Mailgun configuration, domain verification, and bounce/complaint handling playbook (`docs/mailgun-ops.md`).
- [x] Add environment documentation for `ADMIN_EMAIL`, digest scheduler process management, and secure cookie settings in deployment notes.
- [x] End-to-end testing of digest flow completed successfully (2025-10-03).

## Production Deployment (Next Priority)
- [ ] Deploy to production environment with HTTPS enabled
- [ ] Set `SESSION_COOKIE_SECURE=true` in production .env
- [ ] Verify all environment variables configured
- [ ] Run post-deploy validation checklist (see `comms/tasks/2025-10-03-phase2-end-to-end-testing.md`)
- [ ] Monitor initial user signups and digest delivery

## Documentation & Tooling
- [ ] Publish initial API/UI usage doc (FastAPI docs or internal runbook) summarizing auth, club management, and admin endpoints.
- [x] Introduce automated schema migrations (Alembic) before Phase 2 to manage future model changes (`comms/tasks/archive/2025-10-05-alembic-adoption-spec.md`).

## Future Enhancements & Technical Backlog
*Items extracted from the Phase 1 code review. These are desirable but non-blocking improvements for future phases.*

### Core Application
- [ ] **Password Reset:** Implement a self-service password reset flow.
- [ ] **Email Verification:** Add an email verification step at registration to ensure users are reachable.
- [ ] **Data Cleanup:** Add automated, periodic cleanup of old tournament data (e.g., registrations for tournaments that ended more than 30 days ago).
- [ ] **Per-User Timezones:** Allow users to set their own timezone for daily digests.

### Technical Debt & Refinements
- [ ] **Deprecation Warnings:** Replace `datetime.utcnow()` with `datetime.now(datetime.UTC)` throughout the codebase to resolve Python 3.12 warnings.
- [ ] **SQLAlchemy 2.0 Migration:** Update `declarative_base()` usage to the modern `sqlalchemy.orm.declarative_base()` pattern.
- [ ] **HTML Emails:** Upgrade the plain-text digest emails to use styled HTML templates.

### Security & Hardening
- [ ] **CSRF Tokens:** Add CSRF tokens to all state-changing forms as a defense-in-depth measure alongside SameSite cookies.
- [ ] **Rate Limiting:** Implement rate limiting on authentication endpoints (`/auth/login`, `/auth/register`) to protect against brute-force attacks.
