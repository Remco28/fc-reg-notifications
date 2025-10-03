# Task Spec: Tracked Fencer Backend Foundations
**Date:** 2025-10-05
**Owner:** Architect
**Status:** Implemented

## Objective
Implement backend support for user-managed fencer tracking, including schema changes, CRUD/service logic, scraper updates with throttled fencer fetches, and digest integration that merges club and fencer updates without duplicates.

## Scope & Deliverables
1. **Schema & Migrations**
   - Alembic migration adding `tracked_fencers` table (user association, fencingtracker ID, display name, weapon filter, active flag, created_at, optional last_checked_at).
   - Optional supporting indexes/unique constraints (e.g., `uq_tracked_fencers_user_fencer_id`).
   - Update SQLAlchemy models (`TrackedFencer` + relationships) and CRUD helpers.
2. **Service Layer**
   - CRUD: add/create/update/deactivate tracked fencers, weapon filter normalization, uniqueness enforcement.
   - Validation: fencingtracker ID format (numeric) and optional name slug for logging.
   - Integration with digest service: query tracked fencer registrations, merge with club results, dedupe by registration ID.
3. **Scraper Enhancements**
   - Introduce fencer scrape queue: fetch club pages first, enqueue fencer pages, process with configurable delay/jitter.
   - Cache last registration hash/timestamp per tracked fencer to skip unchanged pages.
   - Handle fencingtracker errors (HTTP 429/5xx) with exponential backoff and circuit-breaker (skip fencer for N hours after repeated failures).
4. **Configuration & Monitoring**
   - New env vars: `FENCER_SCRAPE_DELAY_SEC`, `FENCER_SCRAPE_JITTER_SEC`, `FENCER_MAX_FAILURES`, `FENCER_FAILURE_COOLDOWN_MIN` (document defaults).
   - Logging for fencer scrape outcomes (info on new registrations, warnings on throttling, errors on failure).
5. **Digest Integration**
   - Extend digest templates/data assembly to include “Tracked Fencers” section grouped by user.
   - Deduplicate entries that appear via both tracked club and tracked fencer (prefer club listing with note, or merge into combined entry—decide rule).
   - Ensure weapon filters apply consistently across clubs/fencers.
6. **Testing Requirements**
   - Unit tests for new CRUD operations, validation, weapon filter normalization.
   - Scraper: tests for queueing logic, delay/backoff (use fakes/mocks to avoid real sleeps), and skip-on-cache behavior.
   - Digest: tests verifying deduping and section formatting.
   - Migration smoke test (fresh DB can upgrade + downgrade cleanly).

Out of scope: UI changes (covered in later spec), automated fencer discovery/search UX (manual ID entry only).

## Acceptance Criteria
- New migration applies on fresh DB and against existing data with no loss.
- `TrackedFencer` model exposes relationships to `User` and optional prefetch of registrations.
- Scraper respects pacing: no more than one fencer request every `delay +/- jitter` seconds; on repeated failure it pauses according to cooldown.
- Digest output lists tracked fencer registrations exactly once (no duplicates when the same registration is also covered by a tracked club).
- Weapon filters honored for both clubs and fencers.
- Feature toggle: ability to disable fencer scraping via env (e.g., set delay to 0 or dedicated flag) for emergency rollback.
- Tests cover queue/backoff logic and digest dedupe.

## Implementation Notes
- Consider storing `fencer_profile_url` alongside `fencer_id` for easier logging/debugging.
- Cache layer can be simple in-memory dict keyed by fencer ID during a single run; persist `last_checked_at` in DB for cross-run pacing.
- Digest dedupe strategy: build set of registration IDs when compiling club results, skip/add notation for fencers hitting duplicates.
- Ensure existing CLI commands (`scrape`, scheduler) adopt the new flow without breaking.
- Update documentation references (README migrations note, new env vars, architecture diagram if necessary).

## Risks & Mitigations
- **Fencingtracker rate limits:** Mitigated by delay/jitter/backoff; add logging to tune values.
- **Cache staleness:** Use `last_checked_at` to enforce periodic refresh even if no change detected.
- **Complexity creep:** Keep this spec UI-free; push any UI/API concerns to next spec.
- **Digest confusion:** Document dedupe rule clearly; consider user-facing note when a registration is suppressed/merged.

## Validation Plan
- Run migration upgrade/downgrade on fresh database.
- Execute scraper in a controlled test (fencer with known registrations) to ensure queue/backoff works and entries land in DB.
- Trigger digest generation for a user with overlapping club/fencer tracking to verify dedupe.
- Review logs to confirm rate limiting messages behave as expected.

## Follow-Up
- Coordinate with UI spec for forms to add/remove tracked fencers after backend is ready.
- Evaluate if a future spec should persist per-fencer scrape stats (success count, failure count, last status).
