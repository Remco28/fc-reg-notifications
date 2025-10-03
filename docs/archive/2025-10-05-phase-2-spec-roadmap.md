# Phase 2 Spec Roadmap
**Date:** 2025-10-05
**Status:** Drafting specs for next implementation phase

## Goal
Establish an actionable sequence for Phase 2 (Tracked Fencers) work while locking in prerequisite tooling/ops tasks. This roadmap guides spec authoring so we can pause/resume safely if interrupted.

## Context & Decisions (Recap)
- Manual fencer ID entry is acceptable for the first release; no in-app search UX required yet.
- Scraping cadence must remain gentle: club checks run first, followed by rate-limited fencer page fetches with jitter, caching, and automatic slowdown on fencingtracker errors.
- Adopt Alembic migrations before new schema changes land.
- Mailgun is configured; we need lightweight documentation of the required env vars plus a manual bounce/complaint playbook.

## Planned Specs & Sequencing
1. **Alembic Adoption Playbook**
   - Scope: introduce Alembic config, create baseline migration reflecting current schema, document `alembic upgrade` usage.
   - Dependencies: none; unlocks future DB changes.
2. **Mailgun Ops Notes**
   - Scope: document `MAILGUN_*` env expectations and define a simple manual process for handling bounces/complaints (dashboard checks + user flagging).
   - Output: short ops doc update; no code.
3. **Tracked Fencer Backend Foundations**
   - Scope: schema additions (`tracked_fencers`, associations), CRUD/service updates, scraper adjustments with throttled fencer fetch cycle, digest integration rules and deduping.
   - Depends on: Alembic migration workflow.
4. **Tracked Fencer UI & Session Flow**
   - Scope: dashboard forms/pages for adding/removing fencer IDs, weapon filters, validation, and user feedback.
   - Depends on: backend foundations.
5. **Testing & Verification Plan**
   - Scope: expand unit/integration coverage (scraper parsing, digest dedupe, UI form validation), detail manual test checklist.
   - Runs alongside backend/UI specs once foundations are drafted.

## Near-Term Actions
- [x] Author Spec #1 (Alembic Adoption) with step-by-step tasks and fallback guidance (`comms/tasks/archive/2025-10-05-alembic-adoption-spec.md`).
- [x] Author Spec #2 (Mailgun Ops Notes) and mark Spec Ready (`comms/tasks/2025-10-05-mailgun-ops-notes.md`).
- [x] Complete Spec #3 (Tracked Fencer Backend Foundations) and archive after implementation (`comms/tasks/archive/2025-10-05-tracked-fencer-backend-spec.md`).
- [x] Draft Spec #4 (Tracked Fencer UI & Session Flow) for upcoming implementation (`comms/tasks/2025-10-06-tracked-fencer-ui-session-flow.md`).
- [x] Draft Spec #5 (Phase 2 Testing & Verification) outlining required coverage (`comms/tasks/2025-10-06-phase2-testing-verification.md`).

## Open Questions to Track
- Do we foresee the need for per-user scrape limits or is global pacing sufficient? (Revisit after initial load testing.)
- Should we capture fencer display names at add-time or sync them from first scrape? (Decide in backend spec.)

*Document owner: Architect*
