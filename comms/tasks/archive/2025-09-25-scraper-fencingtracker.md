# Task: Implement Core Data Pipeline for fencingtracker.com

**Objective:** Create the core data models and a service that scrapes, persists, and detects changes in registration data from `fencingtracker.com`.

## Technical Specification

### 1. Database Models (`app/models.py`)

- Implement the following SQLAlchemy models based on the project's data model:
  - `Tournament(id, name, date)`
  - `Fencer(id, name)`
  - `Registration(id, fencer_id, tournament_id, events, last_seen_at)`
- Ensure `name` is unique for `Tournament` and `Fencer`.
- Ensure `(fencer_id, tournament_id)` is a unique composite key for `Registration`.

### 2. Database CRUD (`app/crud.py`)

- Implement helper functions to interact with the database:
  - `get_or_create_fencer(db: Session, name: str) -> Fencer`
  - `get_or_create_tournament(db: Session, name: str, date: str) -> Tournament`
  - `update_or_create_registration(db: Session, fencer: Fencer, tournament: Tournament, events: str) -> tuple[Registration, bool]`
    - This function should implement the change detection logic.
    - It should return the `Registration` object and a boolean indicating if it was newly created (`True` if new, `False` if it already existed).

### 3. Scraper Service (`app/services/scraper_service.py`)

- **Modify the function signature:** `scrape_and_persist(db: Session, club_url: str)`.
- **Scraping Logic (as before):**
  - Use `requests` and `BeautifulSoup` to fetch and parse the registration table from the `club_url`.
  - Extract `fencer_name`, `tournament_name`, `tournament_date`, and `events`.
- **Persistence Logic (New):**
  - For each scraped registration, call the CRUD functions to get/create the fencer and tournament.
  - Call `update_or_create_registration` to save the data.
  - Keep track of which registrations are new or modified.
- **Return Value:** The function should return a summary dictionary, e.g.: `{"new": 5, "updated": 28, "total": 33}`.

## Acceptance Criteria

- All specified models and CRUD functions are implemented correctly.
- When `scrape_and_persist` is run, it correctly scrapes the data from the example URL.
- Data is saved to the SQLite database, with new registrations being created and existing ones being updated.
- The function correctly reports the count of new and updated registrations.