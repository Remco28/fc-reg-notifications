# Task Specification: Tournament Grouping Parser Fix

**Date:** 2025-09-30
**Author:** Architect
**Status:** Ready for Implementation

## Objective

Fix the scraper to correctly parse tournament-grouped registrations. Currently the scraper only processes the first table and misidentifies event names as tournament names. It should parse all tournament sections on the page and correctly associate registrations with their parent tournaments.

## User Story

As a fencing club administrator, I want the scraper to detect all tournaments on the registration page so that I can track which fencers are registered for which specific tournaments (not just which events).

## Background / Problem Statement

### Current Behavior (WRONG)
- Scraper calls `soup.find('table')` which finds only the FIRST table
- Treats each table row as a separate "tournament"
- Stores "Junior Women's Epee" (event name) as tournament name
- Only processes 6 registrations from first tournament
- Ignores remaining 15 tournaments on the page

**Example of current wrong data:**
```
Tournament: "Junior Women's Epee"  ❌ (this is an event, not tournament)
Events: "" ❌ (empty - should be the event name)
```

### Expected Behavior (CORRECT)
- Find all tournament sections (16 on Elite FC page)
- Extract tournament name from `<h3>` heading (e.g., "October NAC")
- Parse the table following each heading
- Store event name in the events field (e.g., "Junior Women's Epee")

**Example of correct data:**
```
Tournament: "October NAC" ✓
Events: "Junior Women's Epee" ✓
Fencer: "Sheth, Anayaà" ✓
Date: "Sat, Oct 4" ✓
```

## Page Structure Analysis

### HTML Pattern (from WebFetch)
```html
<h3>October NAC</h3>
<p>Location: City, State [Add Link]</p>
<p>6 entries by 4 club members</p>

<table>
  <thead>
    <tr><th>Name</th><th>Event</th><th>Status</th><th>Date</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><a href="/profile">Sheth, Anayaà</a></td>
      <td><a href="/event">Junior Women's Epee</a></td>
      <td></td>
      <td>Sat, Oct 4</td>
    </tr>
    ...
  </tbody>
</table>

<h3>Duel of the East Coast ROC/RJCC/RYC</h3>
<table>
  ...
</table>
```

### Key Observations
1. Tournament name in `<h3>` tag
2. Location/metadata in `<p>` tags between heading and table
3. Table immediately follows metadata
4. Multiple tournament sections per page
5. No explicit container divs wrapping tournament+table

## Scope

### In Scope
- Parse all tournament sections on the page (not just first table)
- Extract tournament name from `<h3>` heading
- Associate each table with its preceding tournament heading
- Store event name (from table column 1) in Registration.events field
- Process all registrations across all tournaments

### Out of Scope
- Changes to database schema
- Location parsing (can be added later)
- Tournament metadata beyond name and date
- Handling of missing tournament headings (fail gracefully)

## Technical Approach

### Parsing Strategy: "Find Headings, Then Tables"

**Algorithm:**
1. Find all `<h3>` tags (tournament headings)
2. For each `<h3>`:
   - Extract tournament name from heading text
   - Find the next `<table>` sibling
   - Parse all rows in that table
   - Associate rows with the tournament name from heading

**BeautifulSoup pattern:**
```python
# Find all tournament headings
headings = soup.find_all('h3')

for heading in headings:
    tournament_name = heading.get_text(strip=True)

    # Find the next table after this heading
    table = heading.find_next('table')

    if not table:
        logger.warning(f"No table found for tournament: {tournament_name}")
        continue

    # Process rows...
```

### Data Mapping (Corrected)

```
HTML Element              → Database Field
----------------------------------------------
<h3>October NAC</h3>     → Tournament.name
<td>Sat, Oct 4</td>       → Tournament.date
<td>Sheth, Anayaà</td>    → Fencer.name
<td>Junior Women's Epee</td> → Registration.events
<td></td> (Status)        → (ignore for now)
```

**Note:** Status column appears empty on Elite FC page, so we'll ignore it for now. Can be re-added later if needed.

## Implementation Requirements

### 1. Modify Parsing Logic

**File:** `app/services/scraper_service.py`

**Replace lines 143-155 (current single-table logic):**
```python
# OLD (WRONG)
table = soup.find('table')
if not table:
    raise Exception("No registration table found on the page")
```

**With tournament-grouped parsing:**
```python
# NEW (CORRECT)
# Find all tournament headings
headings = soup.find_all('h3')

if not headings:
    logger.error("No tournament headings (<h3>) found on the page")
    raise Exception("No tournament sections found on the page")

logger.info(f"Found {len(headings)} tournament sections")
```

### 2. Process Each Tournament Section

**Add nested loop structure:**
```python
new_count = 0
updated_count = 0
total_count = 0

for heading_idx, heading in enumerate(headings, start=1):
    tournament_name = heading.get_text(strip=True)
    logger.info(f"Processing tournament {heading_idx}/{len(headings)}: {tournament_name}")

    # Find the next table after this heading
    table = heading.find_next('table')

    if not table:
        logger.warning(f"No table found for tournament: {tournament_name}, skipping")
        continue

    # Parse rows in this tournament's table
    rows = table.find_all('tr')[1:]  # Skip header row
    logger.info(f"Found {len(rows)} registrations for {tournament_name}")

    for row_idx, row in enumerate(rows, start=1):
        # Parse row (see section 3 below)
```

### 3. Update Row Parsing

**Modify field extraction (inside row loop):**

**Current (WRONG):**
```python
event_name = cells[1].get_text(strip=True)  # Used as tournament name ❌
tournament = get_or_create_tournament(db, event_name, event_date)
registration, is_new = update_or_create_registration(db, fencer, tournament, registration_status)
```

**New (CORRECT):**
```python
fencer_name = cells[0].get_text(strip=True)
event_name = cells[1].get_text(strip=True)  # This is the EVENT, not tournament
# Skip cells[2] (Status) - appears to be empty
event_date = cells[3].get_text(strip=True)

# Use tournament_name from heading, not from table
tournament = get_or_create_tournament(db, tournament_name, event_date)

# Store event_name in the events field where it belongs
registration, is_new = update_or_create_registration(db, fencer, tournament, event_name)
```

### 4. Update Logging

**Add tournament context to log messages:**
```python
logger.info(f"  [{tournament_name}] Processing row {row_idx}/{len(rows)}")
logger.info(f"  [{tournament_name}] New registration: {fencer_name} -> {event_name}")
logger.error(f"  [{tournament_name}] Error processing row {row_idx}: {e}")
```

### 5. Handle Edge Cases

**Missing tournament date:**
- Some rows may have empty date cells
- Use empty string or "TBD" as fallback
- Log warning but continue processing

**Duplicate registrations:**
- Same fencer + tournament + event = update existing
- Different event for same fencer in same tournament = separate registration

**Missing tables:**
- Log warning and skip tournament
- Continue processing remaining tournaments

## Acceptance Criteria

### Functional Requirements
1. [ ] Scraper processes all 16 tournaments on Elite FC page (not just 1)
2. [ ] Tournament names extracted from `<h3>` headings (e.g., "October NAC")
3. [ ] Event names stored in Registration.events field (e.g., "Junior Women's Epee")
4. [ ] All registrations across all tournaments persisted to database
5. [ ] Database query shows correct tournament names (not event names)
6. [ ] Web UI displays registrations with correct tournament names

### Data Validation
7. [ ] `Tournament.name` = "October NAC" (from heading), not "Junior Women's Epee"
8. [ ] `Registration.events` = "Junior Women's Epee" (from table column), not empty
9. [ ] Total registration count = sum of all rows across all tables (~40+ expected for Elite FC)

### Non-Functional Requirements
10. [ ] Logging shows tournament name in each log message for traceability
11. [ ] Performance acceptable for pages with 20+ tournaments
12. [ ] Missing tables logged but don't crash scraper

### Code Quality
13. [ ] Nested loop structure clear and readable (tournament loop → row loop)
14. [ ] Error handling continues to next tournament on failure
15. [ ] Comments explain heading→table association logic

## Testing Guidance

### Manual Testing

**Test Case 1: Full scrape of Elite FC**
```bash
source fc-reg_env/bin/activate
# Clear existing data to see fresh results
python -m app.main scrape "https://fencingtracker.com/club/100261977/Elite%20FC"
# Expected output: "Total: 40+, New: 40+, Updated: 0"
```

**Test Case 2: Verify tournament names in database**
```bash
python -c "
from app.database import get_db
from app.models import Tournament
db = next(get_db())
tournaments = db.query(Tournament).all()
print(f'Total tournaments: {len(tournaments)}')
for t in tournaments[:5]:
    print(f'  - {t.name}')
db.close()
"
# Expected: Multiple tournament names like "October NAC", not event names
```

**Test Case 3: Verify events field populated**
```bash
python -c "
from app.database import get_db
from app.models import Registration, Fencer, Tournament
db = next(get_db())
reg = db.query(Registration).join(Fencer).join(Tournament).first()
print(f'Fencer: {reg.fencer.name}')
print(f'Tournament: {reg.tournament.name}')
print(f'Event: {reg.events}')
db.close()
"
# Expected:
#   Fencer: Sheth, Anayaà
#   Tournament: October NAC
#   Event: Junior Women's Epee
```

**Test Case 4: Check web UI**
```bash
curl http://localhost:8000/registrations/json | python3 -m json.tool | head -30
# Expected: tournament_name shows "October NAC", events shows "Junior Women's Epee"
```

### Edge Case Testing

**Missing table:**
- Manually edit HTML response to remove a table
- Verify scraper logs warning and continues

**Empty date:**
- Check if any tournaments have missing dates
- Verify scraper handles gracefully

## Constraints & Considerations

### Performance
- Nested loops (tournaments × rows) acceptable for current scale (<100 tournaments)
- Each tournament processed sequentially to maintain logging clarity

### Data Migration
- Existing wrong data in DB will remain until re-scraped
- Consider clearing DB before testing: `rm fc_registration.db && python -m app.main db-init`

### Notification Behavior
- Notifications still sent per registration (not per tournament)
- May result in multiple emails if many new registrations detected

### Future Enhancements
- Parse location from `<p>` tags
- Extract "X entries by Y members" metadata
- Group notifications by tournament

## Related Files
- Scraper service: `app/services/scraper_service.py` (primary changes)
- Models: `app/models.py` (no changes)
- CRUD: `app/crud.py` (no changes)
- Web UI: should automatically show correct data after fix

## Questions for Implementer
- If a tournament has multiple dates (multi-day event), which date to use? → Use first date encountered
- If event name is empty, skip row or use placeholder? → Skip row

## Revision History
- 2025-09-30: Initial specification created