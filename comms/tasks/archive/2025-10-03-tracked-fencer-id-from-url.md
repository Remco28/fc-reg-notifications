# Task Spec: Parse Tracked Fencer Profile URLs
**Date:** 2025-10-03
**Owner:** Architect
**Status:** SPEC READY

## Objective
Allow users to paste a fencingtracker profile URL when adding a tracked fencer; the application should extract the numeric ID server-side so people are no longer required to copy the ID manually.

## Scope & Deliverables
1. **Input Normalization Helper**
   - Extend `app/services/fencer_validation_service.py` with a helper that accepts the raw form input (numeric string or profile URL) and returns a normalized numeric ID.
   - Preserve `validate_fencer_id` as the low-level numeric check; have it called by the new helper after extraction.
   - Supported URL formats must include `https://www.fencingtracker.com/p/<id>`, `https://fencingtracker.com/p/<id>/<slug>`, optional trailing slashes, and lowercase/uppercase scheme variants. Treat plain hostnames without a scheme (`www.fencingtracker.com/p/<id>`) and bare paths (`/p/<id>/<slug>`) as valid inputs as well. Ignore any slug/extra path segments after the numeric portion.
   - Return informative error messages when parsing fails ("Could not find a numeric ID in that profile URL" or similar). Keep empty-input validation consistent with current behaviour.

2. **Tracked Fencer Create Flow**
   - Update `app/api/tracked_fencers.py` (`create_tracked_fencer`) to call the new normalization helper so that duplicates are still checked against the numeric ID and database writes store the clean numeric string.
   - Ensure the error responses from the helper propagate back to the template exactly once (avoid rendering both old and new messages simultaneously).
   - Confirm reactivation and success redirects still function when a URL is provided.

3. **Template & UX Copy**
   - Adjust `app/templates/partials/tracked_fencers_card.html` so the add form no longer rejects URLs:
     * Update the field label/description to mention that both numeric IDs and full profile URLs are accepted.
     * Remove or update the `pattern="[0-9]+"` attribute so URLs pass client-side validation.
     * Adjust the placeholder/example text accordingly.
   - If the dashboard card reuses this partial elsewhere, verify the copy works in all contexts.

4. **Documentation Update**
   - Update the tracked fencer instructions in `README.md` to note that users can paste the full profile URL instead of extracting the ID themselves.

5. **Automated Tests**
   - Extend `tests/services/test_fencer_validation_service.py` with coverage for the new helper: valid numeric input, valid profile URL variants (with/without scheme, with slug), and representative failure cases.
   - Add or update route-level tests in `tests/test_tracked_fencer_routes.py` to confirm that submitting a profile URL results in a tracked fencer record for the expected numeric ID and triggers the existing success flow.

## Acceptance Criteria
- Users can submit any documented URL format (or a bare numeric ID) and successfully create or reactivate tracked fencers; the resulting DB record stores the numeric ID.
- Invalid inputs (non-numeric strings that do not contain a fencingtracker profile ID) surface a clear error message and preserve previously entered display name / weapon filter values on the form as today.
- Client-side form validation no longer blocks profile URLs while still providing basic guidance.
- Unit and route tests cover both numeric and URL inputs and pass.
- README instructions reflect the new UX.

## Implementation Notes
- Consider using a simple regex anchored on `/p/<digits>` after stripping the domain/scheme; avoid over-engineering URL parsing.
- Keep helper return signatures consistent with existing validation patterns (e.g., `(normalized_id, error_msg)` or `(is_valid, id, error)`); document the chosen contract in the code docstring.
- Ensure logging (if any) does not leak full URLs beyond what is already stored; no additional persistence changes are required.

## Out of Scope
- Auto-discovery or search for fencers.
- UI changes beyond copy/validation adjustments described above.
- Any scraper or digest logic updates (existing flows already rely on the numeric ID).
