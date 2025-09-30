# Task Specification: Scraper Enhancements for Fencing Tracker

**Date:** 2025-09-30
**Author:** Architect
**Status:** Ready for Implementation

## Objective

Fix the fencingtracker.com scraper to successfully fetch and parse registration data. Current implementation fails with HTTP/2 protocol errors and has incorrect table structure assumptions.

## User Story

As a fencing club administrator, I want the scraper to reliably fetch registration data from fencingtracker.com club pages so that I can monitor tournament registrations without manual checking.

## Background / Problem Statement

Current scraper implementation has multiple issues:
1. **HTTP Errors:** Server returns "Connection aborted" / "HTTP/2 PROTOCOL_ERROR" when attempting to fetch pages
2. **Wrong Table Structure:** Code expects columns [Fencer|Tournament|Date|Events] but actual table has [Name|Event|Status|Date]
3. **Data Model Mismatch:** Current implementation assumes registrations link to tournament entities, but fencingtracker shows individual event registrations
4. **URL Inflexibility:** Only accepts full `/registrations` URLs, not club home page URLs

## Scope

### In Scope
- Fix HTTP connection issues with proper headers and retry logic
- Update table parsing to match actual HTML structure
- Add URL normalization to accept both club and registration page URLs
- Improve error messages for debugging
- Test against real fencingtracker.com URLs

### Out of Scope
- Data model changes (current model can accommodate with field reinterpretation)
- CSV download feature (site offers it, but we scrape HTML)
- Multi-club monitoring in single command
- Authentication/login (site appears to be public)
- Handling of paginated results (assuming single page for now)

## Technical Approach

### Root Cause Analysis

**HTTP Issues:**
- Fencingtracker.com has unstable HTTP/2 implementation
- Missing User-Agent header may trigger bot detection
- No retry logic for transient failures

**Parsing Issues:**
- Table structure on actual site: `<table>` with columns: Name | Event | Status | Date
- "Event" field contains what we're calling "tournament" (e.g., "Youth 12 Men's Epee")
- "Status" field indicates registration state (e.g., "Registered", "Pending")
- No separate tournament name/date fields - event name IS the tournament

### Solution Design

**Approach:** Enhance existing scraper with defensive HTTP practices and correct parsing logic, without changing data model.

**Field Mapping Strategy:**
```
fencingtracker.com          →  Our Database Model
---------------------------------------------------
Name column                 →  Fencer.name
Event column                →  Tournament.name
Date column                 →  Tournament.date
Status column               →  Registration.events (repurpose field)
```

**Rationale for mapping "Status" to "events" field:**
- Preserves existing data model without migrations
- "Status" information is valuable (tracks registration state)
- Field is already a string type, suitable for status values
- Future enhancement can add proper Status enum if needed

## Implementation Requirements

### 1. HTTP Request Improvements

**File:** `app/services/scraper_service.py`

**Add request configuration:**
```python
# Add at top of scrape_and_persist function
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}
timeout = 10  # seconds
```

**Retry Logic:**
- Implement exponential backoff: 1s, 2s, 4s delays between 3 attempts
- Use `requests.Session()` for connection pooling
- Catch `requests.exceptions.RequestException` and retry on transient errors
- Fail permanently on 4xx status codes (client errors)
- Retry on 5xx status codes (server errors) and connection errors

**Implementation pattern:**
```python
session = requests.Session()
max_retries = 3
for attempt in range(max_retries):
    try:
        response = session.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        break  # Success
    except requests.exceptions.RequestException as e:
        if attempt == max_retries - 1:
            raise Exception(f"Failed after {max_retries} attempts: {e}")
        time.sleep(2 ** attempt)  # Exponential backoff
```

### 2. URL Normalization

**File:** `app/services/scraper_service.py`

**Add function:**
```python
def normalize_club_url(url: str) -> str:
    """
    Normalize fencingtracker.com club URLs to registration page URLs.

    Accepts:
    - https://fencingtracker.com/club/123/Name
    - https://fencingtracker.com/club/123/Name/registrations

    Returns:
    - https://fencingtracker.com/club/123/Name/registrations

    Raises:
    - ValueError if URL doesn't match expected pattern
    """
```

**Expected behavior:**
- If URL ends with `/registrations`, return as-is
- If URL matches `/club/{id}/{name}` pattern, append `/registrations`
- Raise `ValueError` with helpful message for invalid URLs
- Handle trailing slashes gracefully

**URL Validation:**
- Must contain `/club/` path segment
- Must be https scheme
- Domain must be `fencingtracker.com` or `www.fencingtracker.com`

### 3. Table Parsing Update

**File:** `app/services/scraper_service.py`

**Current parsing (WRONG):**
```python
fencer_name = cells[0].get_text(strip=True)      # Correct
tournament_name = cells[1].get_text(strip=True)  # WRONG - this is Event
tournament_date = cells[2].get_text(strip=True)  # WRONG - this is Status
events = cells[3].get_text(strip=True)           # WRONG - this is Date
```

**New parsing (CORRECT):**
```python
fencer_name = cells[0].get_text(strip=True)        # Name column
event_name = cells[1].get_text(strip=True)         # Event column → tournament_name
registration_status = cells[2].get_text(strip=True) # Status column → events field
event_date = cells[3].get_text(strip=True)         # Date column → tournament_date
```

**Field assignments:**
```python
# Use event_name as tournament_name (e.g., "Youth 12 Men's Epee")
tournament = get_or_create_tournament(db, event_name, event_date)

# Store status in events field (repurpose existing field)
registration, is_new = update_or_create_registration(db, fencer, tournament, registration_status)
```

**Validation:**
- Skip rows where `fencer_name` or `event_name` is empty
- Log warning for unexpected cell counts (not 4 columns)
- Continue processing other rows if one row fails

### 4. Error Handling & Logging

**Improve error messages:**
- Include full URL in error messages
- Log HTTP status codes
- Log retry attempts with attempt number
- Distinguish between network errors, HTTP errors, and parsing errors

**Add structured logging:**
```python
logger = logging.getLogger(__name__)
logger.info(f"Fetching registrations from {url} (attempt {attempt + 1}/{max_retries})")
logger.error(f"HTTP error {response.status_code}: {response.reason}")
logger.warning(f"Skipping row with {len(cells)} columns (expected 4)")
```

### 5. Dependencies

**Add to imports (if not present):**
```python
import time
import logging
from urllib.parse import urlparse
```

No new external dependencies required.

## Acceptance Criteria

### Functional Requirements
1. [ ] Scraper successfully fetches https://fencingtracker.com/club/100261977/Elite%20FC/registrations
2. [ ] URL normalization accepts club URLs without `/registrations` suffix
3. [ ] URL normalization rejects invalid URLs with clear error message
4. [ ] Table parsing correctly extracts: Name → Fencer, Event → Tournament, Status → events field, Date → tournament date
5. [ ] Registrations persist to database with correct field mappings
6. [ ] New registrations trigger email notifications as before

### Non-Functional Requirements
7. [ ] Retry logic handles transient connection failures (test by introducing network delays)
8. [ ] HTTP requests include proper User-Agent header (verify in logs/network capture)
9. [ ] Scraper completes within 30 seconds for pages with <50 registrations
10. [ ] Error messages are actionable (include URL, HTTP status, attempt count)

### Code Quality
11. [ ] URL normalization has docstring with examples
12. [ ] Retry logic follows exponential backoff pattern (1s, 2s, 4s)
13. [ ] All exception types caught and logged appropriately
14. [ ] No hardcoded magic numbers (use constants for timeouts, retries, delays)

## Testing Guidance

### Manual Testing

**Test Case 1: Valid registration URL**
```bash
source fc-reg_env/bin/activate
python -m app.main scrape "https://fencingtracker.com/club/100261977/Elite%20FC/registrations"
# Expected: Success, registrations persisted
```

**Test Case 2: Club URL without /registrations**
```bash
python -m app.main scrape "https://fencingtracker.com/club/100261977/Elite%20FC"
# Expected: Success, URL normalized automatically
```

**Test Case 3: Invalid URL**
```bash
python -m app.main scrape "https://example.com/invalid"
# Expected: Clear error message about invalid URL pattern
```

**Test Case 4: Verify data in DB**
```bash
# After successful scrape, check UI
curl http://localhost:8000/registrations/json | python3 -m json.tool
# Expected: JSON with registrations showing:
# - fencer_name from Name column
# - tournament_name from Event column
# - tournament_date from Date column
# - events field containing Status values
```

**Test Case 5: Network retry**
```bash
# Simulate by running during network instability or using network throttling
# Expected: Retry attempts logged, eventual success or clear failure message
```

### Automated Testing (Optional)

Create `tests/test_scraper_enhancements.py`:
- Test `normalize_club_url()` with valid/invalid inputs
- Mock `requests.get()` to test retry logic
- Test table parsing with sample HTML snippets
- Verify field mappings to database

## Constraints & Considerations

### Performance
- Retry logic adds latency (up to ~7 seconds on failures)
- Acceptable tradeoff for reliability

### Security
- User-Agent spoofing is ethical for public data scraping
- Respect robots.txt (check /robots.txt before scraping in production)
- Add rate limiting if scraping multiple clubs frequently

### Data Quality
- "Status" values in events field is semantic mismatch but acceptable short-term
- Future enhancement: Add proper `status` column to Registration model

### Backwards Compatibility
- Existing scraper CLI command signature unchanged
- Existing database records unaffected (field meanings shift but no migration needed)

## Related Files
- Scraper service: `app/services/scraper_service.py` (primary changes)
- Models: `app/models.py` (no changes)
- CRUD: `app/crud.py` (no changes)
- Notification service: `app/services/notification_service.py` (no changes)

## Questions for Implementer
- If fencingtracker.com continues to have HTTP/2 issues, consider forcing HTTP/1.1 via custom adapter
- If table structure varies by club, may need more robust column detection

## Future Enhancements
- Add `Registration.status` field for proper semantic storage
- Support pagination if clubs have >100 registrations
- Add CSV download parsing as alternative to HTML scraping
- Schedule periodic scraping with APScheduler
- Add support for askfred.net (different site, different parser)

## Revision History
- 2025-09-30: Initial specification created