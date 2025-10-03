# Task Spec: Phase 2 Testing & Verification
**Date:** 2025-10-06
**Owner:** Architect
**Status:** Spec Ready

## Objective
Define the expanded automated and manual testing coverage required before Phase 2 (tracked fencers) can ship, ensuring scraper stability, digest correctness, and UI regression protection.

## Scope
This spec coordinates test additions across services, database layers, and the new UI. It complements the backend/UI specs by making explicit which behaviors must be exercised and how to structure fixtures/mocks for reliability.

## Deliverables

1. **Service-Level Tests**
   - Extend `tests/services/test_fencer_scraper_service.py` with integration-style tests that:
     - Use a temporary SQLite DB to verify registrations persist with correct club URL preservation when both club and fencer scrapes run.
     - Simulate cooldown expiry by advancing time (monkeypatch `datetime.utcnow`) to confirm scrapes resume after cooldown window.
     - Validate logging side-effects via caplog (e.g., retries, cooldown messages) to guard against silent failures.
   - Add tests for `app/services/digest_service.py` covering:
     - Mixed weapon filter scenarios (club vs fencer filters combining).
     - Email body formatting when both sections present vs fencer-only digests.

2. **CRUD & Validation Regression Tests**
   - Ensure `tests/test_crud_tracked_fencers.py` includes cases for:
     - Attempting to create duplicate tracked fencers for same user raising appropriate exception.
     - Deactivation workflow updates timestamps and active flag without deleting rows.
   - Expand `tests/services/test_fencer_validation_service.py` to cover edge weapon filter inputs (extra commas, uppercase, mixed whitespace).

3. **UI / Route Tests**
   - Use FastAPI TestClient to render tracked fencer dashboard view and assert presence of existing fencers in HTML (IDs, display names, badges).
   - POST form submissions for add/edit/deactivate flows verifying redirects and flash messages.
   - Snapshot or string-match digest to keep templating stable (guard against accidental heading changes).

4. **End-to-End Smoke Script**
   - Add a script or pytest marked scenario (`tests/e2e/test_tracked_fencer_flow.py`) that:
     - Seeds a test user, tracked club, and tracked fencer.
     - Runs club scrape + fencer scrape job functions directly.
     - Invokes `send_user_digest` and asserts only one notification with deduped entries is enqueued.
     - Cleans up database afterwards.

5. **Documentation Updates**
   - Update `docs/TESTING.md` (create if missing) outlining how to run the expanded suite, required env vars, and tips for deterministic scraper tests (e.g., monkeypatch jitter/delay to zero).
   - Add a checklist to `NEXT_STEPS.md` linking to the new testing assets once landed.

## Acceptance Criteria
- New test files run as part of `pytest` without network calls or flakiness.
- Coverage reports (if enabled) show new lines exercised in scraper/digest/UI modules.
- E2E smoke test validates combined flow and runs under CI time budgets (<30s).
- Testing documentation clearly describes how to simulate scraper retries and cooldowns locally.
- `NEXT_STEPS.md` updated to reflect testing milestones.

## Validation Plan
- Execute `pytest -k fencer` and full suite to ensure runtime remains acceptable.
- Run e2e test multiple times to confirm determinism.
- Peer review from Developer to confirm tests match implementation details.

## Follow-Up
- Future phase may add playwright/browser tests once UI stabilizes.
- Consider GitHub Actions integration for nightly scraper simulations when infrastructure ready.
