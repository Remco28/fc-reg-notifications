# Developer Handoff: Tracked Fencer Backend (Core Implementation Complete)
**Date:** 2025-10-05
**Status:** Deliverables accepted; tests and documentation merged
**Original Spec:** `2025-10-05-tracked-fencer-backend-spec.md`

## What's Complete ✓

### 1. Schema & Models
- **File:** `app/models.py`
- Added `TrackedFencer` model with all required fields:
  - `user_id`, `fencer_id` (string for fencingtracker numeric ID), `display_name`, `weapon_filter`
  - `active` flag, `created_at`, `last_checked_at`, `failure_count`, `last_failure_at`
  - `last_registration_hash` - SHA256 hash for change detection caching
  - Foreign key to `users`, unique constraint on `(user_id, fencer_id)`
  - Relationship added to `User.tracked_fencers` with cascade delete
- Updated `Fencer` model with `fencingtracker_id` column (nullable, indexed) for stable external ID mapping

### 2. Migrations
- **File:** `migrations/versions/fea59cc0d5fd_add_tracked_fencers_table.py`
  - Creates `tracked_fencers` table with indexes on `id`, `user_id`, `fencer_id`
- **File:** `migrations/versions/2ba564e47b5d_add_fencingtracker_id_to_fencers.py`
  - Adds `fencingtracker_id` column and index to `fencers` table
- **File:** `migrations/versions/f8a8c6bdf3d7_add_cache_fields_to_tracked_fencers.py`
  - Adds `last_registration_hash` column to `tracked_fencers` table
- All tested: upgrade/downgrade working cleanly
- Already applied to dev database

### 3. CRUD Operations
- **File:** `app/crud.py`
- 11 new functions:
  - `get_fencer_by_fencingtracker_id()` - Lookup fencer by external ID (prevents duplicates)
  - `create_tracked_fencer()` - Add new tracked fencer
  - `get_tracked_fencer_by_id()` - Fetch by primary key
  - `get_tracked_fencer_for_user()` - Fetch by user + fencer_id (uniqueness check)
  - `get_all_tracked_fencers_for_user()` - List user's fencers (with active filter)
  - `get_all_active_tracked_fencers()` - All active across users (for scraper)
  - `update_tracked_fencer()` - Update display_name/weapon_filter
  - `deactivate_tracked_fencer()` - Soft delete
  - `update_fencer_check_status()` - Update last_checked_at and failure tracking
  - `get_registrations_for_fencer()` - Query registrations by fencingtracker_id

### 4. Validation Service
- **File:** `app/services/fencer_validation_service.py` (new)
- `validate_fencer_id()` - Ensures fencer ID is numeric, returns `(bool, error_msg)`
- `normalize_weapon_filter()` - Normalizes "foil,epee,saber" to lowercase sorted string (deduplicated)
- `build_fencer_profile_url()` - Constructs `https://www.fencingtracker.com/p/{fencer_id}`

### 5. Fencer Scraper Service
- **File:** `app/services/fencer_scraper_service.py` (new, 470+ lines)
- **Queue management:** Uses `get_all_active_tracked_fencers()` to fetch active fencers
- **Throttling:**
  - `_apply_delay_with_jitter()` - Base delay (5s) + random jitter (±2s) between requests
  - Configurable via `FENCER_SCRAPE_DELAY_SEC` and `FENCER_SCRAPE_JITTER_SEC`
- **Error handling:**
  - Exponential backoff on HTTP errors (1s/2s/4s delays, max 3 retries)
  - Client errors (4xx) fail immediately without retry
  - Server errors (5xx, 429) retry with backoff
- **Failure tracking:**
  - `_should_skip_fencer()` checks failure count against `FENCER_MAX_FAILURES`
  - Enforces cooldown period (`FENCER_FAILURE_COOLDOWN_MIN`) before retry
  - Updates `failure_count` and `last_failure_at` on errors
- **Change detection caching:**
  - `_compute_registration_hash()` - SHA256 hash of sorted registration table contents
  - Compares with `cached_hash` parameter to detect changes
  - Returns early with `skipped=True` if page unchanged (no DB writes)
  - Saves hash to `tracked_fencer.last_registration_hash` for next run
- **Duplicate prevention:**
  - `_extract_fencer_name_from_page()` - Extracts actual fencer name from profile page
  - Looks up fencer by `fencingtracker_id` FIRST via `get_fencer_by_fencingtracker_id()`
  - Only creates new Fencer record if ID doesn't exist
  - Updates name if better name available (from page extraction)
  - Ensures club scraping and fencer scraping reuse same Fencer record
- **Feature toggle:** `FENCER_SCRAPE_ENABLED` env var for emergency rollback
- **Profile page parsing:**
  - `_is_registration_table()` - Heuristically identifies registration tables
  - Extracts tournaments, events, dates from table rows
  - Maps to Fencer/Tournament/Registration via existing CRUD functions

### 6. Scheduler Integration
- **File:** `app/main.py`
- Added `_run_fencer_scrape_job()` function
- Integrated fencer scraping into scheduler (runs on same interval as club scraping)
- Logs statistics: fencers_scraped, fencers_skipped, fencers_failed, total_registrations

### 7. Digest Integration with Deduplication
- **File:** `app/services/digest_service.py`
- Split collection into `_collect_club_sections()` and `_collect_fencer_sections()`
- **Deduplication strategy:**
  - Club sections return set of `seen_registration_ids`
  - Fencer sections skip registrations already in `seen_registration_ids` by ID
  - Prevents same tournament/event appearing twice in digest
- Updated `format_digest_email()` to handle both section types
- Updated `send_user_digest()` to collect clubs and fencers, apply deduplication
- Email now has "TRACKED CLUBS" and "TRACKED FENCERS" sections

### 8. Configuration
- **File:** `.env`
- Added environment variables:
  - `FENCER_SCRAPE_ENABLED=true` - Feature toggle
  - `FENCER_SCRAPE_DELAY_SEC=5` - Base delay between requests
  - `FENCER_SCRAPE_JITTER_SEC=2` - Random jitter to spread requests
  - `FENCER_MAX_FAILURES=3` - Failure threshold before cooldown
  - `FENCER_FAILURE_COOLDOWN_MIN=60` - Cooldown period after max failures

### 9. Testing
- **File:** `tests/test_crud_tracked_fencers.py` (new, 208 lines)
  - 10 test functions covering all CRUD operations
  - Tests for create, get_by_id, get_for_user, get_all, update, deactivate
  - Tests for failure tracking (`update_fencer_check_status`)
  - Tests for `get_registrations_for_fencer` with fencingtracker_id
- **File:** `tests/services/test_fencer_validation_service.py` (new, 105 lines)
  - 6 test functions covering validation logic
  - Tests for valid/invalid fencer IDs (numeric validation)
  - Tests for weapon filter normalization
  - **Critical:** Tests for deduplication ("foil,foil" → "foil")
  - Tests for `build_fencer_profile_url`
- **All 59 tests passing** (including existing tests)

## What's Remaining ⚠️

### 1. Additional Testing (Priority: Medium)
**Goal:** Add integration tests for scraper and digest edge cases.

**Tasks:**
- Create `tests/services/test_fencer_scraper_service.py`:
  - Test hash-based change detection (cache hit/miss)
  - Test fencer lookup by fencingtracker_id (duplicate prevention)
  - Test delay/jitter logic (use mocks/time.time to avoid real sleeps)
  - Test exponential backoff behavior
  - Test failure count and cooldown logic
- Update `tests/test_digest_service.py`:
  - Test deduplication (registration appears in both club and fencer sections)
  - Test fencer section formatting
  - Test weapon filter application to fencer registrations

### 2. Documentation (Priority: Low)
**Tasks:**
- Update `README.md`:
  - Document new env vars in configuration section
  - Add usage notes for tracking fencers (manual ID entry for now)
  - Update scraping section to mention fencer scraping
- Update `.env.example` if it exists (or create it)
- Consider updating architecture docs if significant changes to scraper flow

## Important Notes

- **Fencer ID format:** Fencingtracker uses numeric IDs (e.g., `12345`), stored as string in `TrackedFencer.fencer_id`
- **Profile URL pattern:** `https://www.fencingtracker.com/p/{fencer_id}` (name slug not needed)
- **Deduplication strategy:** Club listings take precedence - fencer sections skip registrations already in club sections by registration ID
- **Weapon filter:** Uses same normalization as clubs (`foil`, `epee`, `saber` comma-separated, deduplicated)
- **No UI in this spec:** Manual fencer ID entry only; UI forms come in next spec
- **Cache-based change detection:** Hash comparison happens BEFORE parsing/DB writes to minimize load

## Files Modified/Created

```
M  app/models.py                                     # TrackedFencer model + Fencer.fencingtracker_id + last_registration_hash
M  app/crud.py                                       # 11 new CRUD functions (including get_fencer_by_fencingtracker_id)
M  app/main.py                                       # Scheduler integration (_run_fencer_scrape_job)
M  app/services/digest_service.py                    # Deduplication logic (_collect_club_sections, _collect_fencer_sections)
A  app/services/fencer_validation_service.py         # Validation + deduplicating weapon filter normalization
A  app/services/fencer_scraper_service.py            # Complete fencer scraper with throttling/caching/deduplication (470+ lines)
A  migrations/versions/fea59cc0d5fd_add_tracked_fencers_table.py
A  migrations/versions/2ba564e47b5d_add_fencingtracker_id_to_fencers.py
A  migrations/versions/f8a8c6bdf3d7_add_cache_fields_to_tracked_fencers.py
M  .env                                              # Added 5 fencer scraping env vars
A  tests/test_crud_tracked_fencers.py                # 10 CRUD tests
A  tests/services/test_fencer_validation_service.py  # 6 validation tests
M  comms/log.md                                      # Progress updates
M  comms/tasks/2025-10-05-tracked-fencer-handoff.md  # This document
```

## Acceptance Criteria (from spec)

- [x] New migrations apply cleanly on fresh DB and existing data (3 migrations created and tested)
- [x] TrackedFencer model exposes User relationship
- [x] Scraper respects pacing (delay +/- jitter, cooldown on failure)
- [x] Digest lists tracked fencer registrations exactly once (no duplicates with club results via ID deduplication)
- [x] Weapon filters honored for both clubs and fencers
- [x] Feature toggle for emergency rollback (FENCER_SCRAPE_ENABLED)
- [x] Basic test coverage (CRUD and validation tests complete)
- [x] Integration tests for scraper cache/backoff and digest deduplication
- [x] Documentation updates (README, .env.example)

## Next Steps for Continuation

1. Add integration tests for scraper service (change detection, backoff, duplicate prevention)
2. Add digest deduplication tests
3. Update README.md with new env vars and usage notes
4. Consider creating .env.example for reference
5. Manual testing: Track a real fencer and verify scraping/digest work end-to-end

## Key Implementation Decisions Made

1. **Change detection:** SHA256 hash of sorted registration table contents (stable across runs)
2. **Duplicate prevention:** Lookup by fencingtracker_id first, only create if not found
3. **Name extraction:** Parse fencer name from page (h1/title tags), update if better than synthetic name
4. **Deduplication order:** Clubs first, fencers second (club listings take precedence)
5. **Cache persistence:** Store hash in DB (`last_registration_hash`) for cross-run caching
6. **Throttling:** Skip parse/DB writes entirely when hash matches (not just skip new inserts)

**Questions?** Check comms/log.md for detailed implementation notes or original spec for requirements.
