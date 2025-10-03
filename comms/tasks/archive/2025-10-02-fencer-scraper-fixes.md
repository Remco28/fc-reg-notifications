# Task: Fix Fencer Scraper Regressions and Gaps
**Date:** 2025-10-02
**Status:** SPEC READY

## 1. Objective
Address the three blocking issues identified during the review of the "Tracked Fencer Backend" implementation (`[2025-10-05T18:30Z]`). This involves fixing a data overwrite regression, adding missing test coverage, and correcting documentation.

## 2. Background
The initial implementation of the fencer tracking backend was blocked from release due to three issues:
1.  A high-priority regression where the fencer scraper overwrites the `Registration.club_url`, which breaks club-based digests.
2.  A high-priority testing gap where required tests for scraper resilience (caching, backoff) and digest deduplication were not implemented.
3.  A medium-priority documentation gap where new environment variables were not documented and the README pointed to a non-existent `.env.example` file.

This specification details the work required to resolve these issues.

## 3. Deliverables

### Task 1: Fix `Registration.club_url` Overwrite Regression

*   **File to Modify:** `app/services/fencer_scraper_service.py`
*   **Problem:** When the scraper processes a fencer's profile page, it finds registrations and persists them. In doing so, it sets the `Registration.club_url` to the fencer's profile URL, even if the registration was originally found via a club page and already has a `club_url`. This breaks the digest generation for users tracking that club.
*   **Required Change:** Modify the registration processing logic within `scrape_fencer_profile`. When creating or updating a `Registration` entity, the `club_url` field **must not** be overwritten if it already has a value. It should only be set when a `Registration` is being created for the very first time.

### Task 2: Add Missing Test Coverage

*   **Files to Create/Modify:**
    *   `tests/services/test_fencer_scraper_service.py` (new file)
    *   `tests/test_digest_service.py` (update existing file)

*   **Problem:** Critical logic in the fencer scraper and digest service is untested, violating the acceptance criteria of the original spec.

*   **Required Changes:**
    1.  **Fencer Scraper Service Tests:**
        *   Create `tests/services/test_fencer_scraper_service.py`.
        *   Using mocks for `requests`, `time.sleep`, and the `crud` layer, add tests to verify the following behaviors in `scrape_all_tracked_fencers`:
            *   **Caching:** A fencer profile scrape is skipped if the computed registration hash matches the `last_registration_hash` on the `TrackedFencer` model.
            *   **Request Throttling:** A delay (e.g., `FENCER_SCRAPE_DELAY_SEC`) is respected between requests.
            *   **Error Backoff:** The service performs exponential backoff retries on 5xx HTTP errors.
            *   **Failure Cooldown:** A fencer is skipped for the configured cooldown period (`FENCER_FAILURE_COOLDOWN_MIN`) after reaching the max failure count (`FENCER_MAX_FAILURES`).
    2.  **Digest Deduplication Tests:**
        *   In `tests/test_digest_service.py`, add a new test case for `send_user_digest`.
        *   This test must verify that if a registration is included in a "Tracked Clubs" section of a digest, it is **not** included in a "Tracked Fencers" section of the same digest.
        *   Set up the test data to ensure a fencer registration from a tracked club also appears on that fencer's profile, who is also tracked by the user.

### Task 3: Update Documentation and Environment

*   **Files to Create/Modify:**
    *   `.env.example` (new file)
    *   `README.md` (update existing file)

*   **Problem:** The project is missing a sample environment file, and new configuration variables are undocumented.

*   **Required Changes:**
    1.  **Create `.env.example`:**
        *   Create a new `.env.example` file in the project root.
        *   Populate it with all environment variables required to run the application, including `MAILGUN_*`, `DATABASE_URL`, `SESSION_COOKIE_SECURE`, and the new `FENCER_*` variables.
        *   Include comments explaining what each variable does.
        ```env
        # Mailgun API Configuration
        MAILGUN_API_KEY=
        MAILGUN_DOMAIN=
        MAILGUN_SENDER=
        MAILGUN_DEFAULT_RECIPIENTS=

        # Database URL
        DATABASE_URL=sqlite:///./fc_registration.db

        # --- Security & Session ---
        # Set to "true" in production to ensure cookies are only sent over HTTPS
        SESSION_COOKIE_SECURE=false
        ADMIN_EMAIL=

        # --- Fencer Scraper Settings ---
        # Enable/disable the fencer scraper job
        FENCER_SCRAPE_ENABLED=true
        # Base delay (seconds) between fencer profile requests
        FENCER_SCRAPE_DELAY_SEC=5
        # Random jitter (seconds) to add/subtract from the base delay
        FENCER_SCRAPE_JITTER_SEC=2
        # Number of consecutive failures before a fencer is skipped
        FENCER_MAX_FAILURES=3
        # Cooldown period (minutes) before retrying a failed fencer
        FENCER_FAILURE_COOLDOWN_MIN=60
        ```
    2.  **Update `README.md`:**
        *   Search for the section that mentions environment setup.
        *   Replace the instruction to copy a non-existent file with: "Copy the sample environment file `.env.example` to `.env` and fill in the required values."

## 4. Acceptance Criteria
- [ ] The `fencer_scraper_service` no longer overwrites an existing `Registration.club_url`.
- [ ] A new test file, `tests/services/test_fencer_scraper_service.py`, is created with coverage for caching, backoff, and failure handling logic.
- [ ] `tests/test_digest_service.py` is updated with a test case confirming registration deduplication between club and fencer sections.
- [ ] The `.env.example` file exists in the root directory and contains all required variables with explanatory comments.
- [ ] The `README.md` file is updated to instruct users to copy `.env.example`.
- [ ] All 59 existing tests plus all new tests pass successfully.
