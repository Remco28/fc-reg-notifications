# Task Spec: Tracked Fencer UI & Session Flow
**Date:** 2025-10-06
**Owner:** Architect
**Status:** Spec Ready

## Objective
Deliver the user-facing experience for managing tracked fencers, wiring the new backend capabilities into fastapi routes, templates, and session handling so authenticated users can add, edit, and deactivate tracked fencers without impacting existing club workflows.

## Background
Backend support (schema, scraper, digest integration) for tracked fencers is live (`2025-10-05-tracked-fencer-backend-spec.md`). We now need a minimal but robust UI that mirrors the tracked club management experience, enforces validation, and keeps users informed about scrape status and throttling limits.

## Deliverables

1. **Dashboard Integration**
   - Add a "Tracked Fencers" management card to the authenticated dashboard (`templates/dashboard.html` or equivalent component).
   - Display each tracked fencer with: display name (or fallback to fencer ID), weapon filter, status badges (`Active`, `Cooling Down`, `Disabled`), last checked timestamp, and last failure reason if available.
   - Provide inline actions:
     - "Edit" (opens modal or inline form to change display name / weapon filter).
     - "Deactivate" (POST to disable tracking, with confirmation prompt).
   - Ensure responsive layout matches existing Tailwind/utility classes.

2. **Create & Edit Forms**
   - New modal or dedicated page for adding a tracked fencer. Capture fields:
     - `fencer_id` (numeric string, required).
     - `display_name` (optional, defaults to scraped name).
     - `weapon_filter` (optional comma-separated list; reuse existing helper text from clubs form).
   - Edit form should allow changing `display_name` and `weapon_filter` only (ID immutable).
   - Client-side hints for numeric ID requirement; server-side validation remains authoritative.

3. **API / Route Layer**
   - Create a new FastAPI router module (e.g., `app/routes/tracked_fencers.py`) or extend existing dashboard routes.
   - Endpoints (all require authenticated session):
     - `GET /fencers` – render management view with current tracked fencers.
     - `POST /fencers` – create new tracked fencer; on success redirect back with flash message.
     - `POST /fencers/{id}/edit` – update display name/weapon filter.
     - `POST /fencers/{id}/deactivate` – mark inactive.
   - Use CSRF/session protections consistent with club management flows.
   - Hook validation through `app.services.fencer_validation_service` for ID and weapon filter normalization.

4. **Flash Messaging & Error Handling**
   - Reuse existing flash infrastructure to surface success/failure messages (e.g., duplicate fencer ID, invalid weapon filter, cooldown status updates).
   - Present actionable error text ("Fencer ID must be numeric", "Fencer already tracked").

5. **Navigation & Docs**
   - Update site navigation/sidebar to include "Tracked Fencers" link where appropriate.
   - Update README usage section with short instructions for adding tracked fencers and notes about manual ID entry and scraper pacing.

6. **Tests**
   - Template rendering smoke tests (if existing test harness checks HTML pieces).
   - Route tests (using FastAPI TestClient) covering:
     - Successful creation of a tracked fencer.
     - Duplicate/validation error path.
     - Editing weapon filter normalizes and persists values.
     - Deactivating hides fencer from active list but keeps historical data.
   - Ensure tests reset DB state between cases.

## Constraints & Assumptions
- No fencingtracker search/autocomplete in this phase; users paste numeric ID.
- Keep parity with tracked club UX (same button styles, messaging).
- Scraper cadence info should be hinted (e.g., tooltip or copy reminding users that updates may take several minutes).
- Non-admin users can only manage their own fencers; admins see all via existing admin UI (future work if needed).

## Acceptance Criteria
- Authenticated user can add a valid fencer ID, optionally set display name/weapon filter, and see it on the dashboard.
- Duplicate fencer IDs for the same user are gracefully rejected with inline error.
- Editing a tracked fencer updates display name/weapon filter and reflects immediately.
- Deactivated fencers disappear from active list and are marked inactive in DB.
- README documents manual ID entry workflow and referencing numeric IDs from fencingtracker profiles.
- Automated tests cover create/edit/deactivate happy paths and validation failures.

## Validation Plan
- Manual walk-through in dev environment: add fencer, simulate failed scrape (manually bump failure count) to check status badges, deactivate, and re-add.
- Run entire pytest suite; new tests must pass without flakiness.
- Review UI with Designer Lead once forms in place to confirm consistency.

## Follow-Up
- Future spec will cover admin overview for tracked fencers if demand arises.
- Revisit copy and tooltip text post-user feedback.
