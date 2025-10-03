# Task Spec: Tracked Fencer URL Parsing & Auto-Naming Fixes
**Date:** 2025-10-03
**Owner:** Architect
**Status:** SPEC READY

## Objective
Resolve the regression where fencingtracker profile URLs without a trailing name segment fail validation, and automatically derive a sensible display name when users leave that field blank.

## Scope & Deliverables
1. **Input Normalization Fixes**
   - Adjust `app/services/fencer_validation_service.normalize_tracked_fencer_id` so that URLs like `https://fencingtracker.com/p/100265260` (no slug, optional trailing slash/query/fragment) normalize successfully.
   - Add explicit unit coverage for these cases and keep prior behaviours (bare numeric strings, slugged URLs) intact.
   - Ensure the helper still emits "Could not find a numeric ID…" for malformed fencingtracker URLs and "Fencer ID must be numeric" for non-URL garbage.

2. **Automatic Display Name Derivation**
   - When a user omits `display_name` in `/fencers` POST:
     * Try to extract a human-friendly name from the URL slug (split on `/`, decode hyphens, title-case words while respecting apostrophes etc.).
     * If no slug is present, look for an existing `Fencer` row via `crud.get_fencer_by_fencingtracker_id` and reuse its `name`.
     * As a final fallback, call a lightweight helper (new in `app/services/fencer_scraper_service.py`) that fetches the profile page once and scrapes the name using the existing BeautifulSoup logic; timeout quickly and swallow/ log errors so the create flow still succeeds without a name.
   - Never overwrite a user-specified display name, and do not change the display name of existing tracked fencers on reactivation.
   - Wire the chosen display name through `crud.create_tracked_fencer` so the DB stores it immediately.

3. **User Feedback & Copy**
   - Restore the success flash to the original copy `Fencer tracked successfully` so redirects/tests stay green.
   - Update `app/templates/partials/tracked_fencers_card.html` helper text to mention that the system now attempts to auto-fill the name when left blank.
   - Refresh the README tracked-fencer section to highlight the auto-name behaviour and note that URLs without a slug are supported.

4. **Automated Tests**
   - Extend `tests/services/test_fencer_validation_service.py` with assertions for slugless URLs, URLs containing query strings/fragments, and the new slug-to-name utility if it lives there.
   - Add coverage for the auto-name flow in `tests/test_tracked_fencer_routes.py` by submitting:
     * A slugged URL with blank display name (result should store the prettified slug).
     * A slugless URL with blank display name while a mock scraper helper returns a name (use monkeypatching to avoid real HTTP).
   - Ensure existing tests continue to pass, including the flash-message regression guard.

## Acceptance Criteria
- Users can add tracked fencers using either slugged or slugless fencingtracker URLs; both persist the correct numeric ID.
- Submissions without a display name now store an inferred name when one can be determined; otherwise they behave as before (blank display name, no failure).
- Success messages and README/UI copy reflect the auto-name behaviour.
- All updated/new tests pass locally (`pytest` focused modules are sufficient if full suite is prohibitive).

## Implementation Notes
- Factor the slug parsing into a reusable helper so both the view and tests stay tidy.
- Keep the scraper fallback fast: set a short timeout (~3s) and catch `requests.RequestException` to avoid blocking the request cycle.
- Log at debug/warning level when fallback fetch fails, but avoid leaking full URLs in error messages.
- When deriving names from slugs, handle tokens like `macdonald` or `o-connor` sensibly (basic title-case is acceptable, but avoid double-spacing or empty tokens).

## Out of Scope
- Broader refactors of the tracked fencer CRUD or scraper scheduler.
- Persisting the auto-derived name back onto existing tracked fencers during background scrapes (that can be a future enhancement).
