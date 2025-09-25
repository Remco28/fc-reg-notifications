# Project: Fencing Club Registration Notifications

## Milestone 1: Core Data Pipeline
*As per Tech Advisor recommendation, the initial focus is on creating a reliable data ingestion and persistence mechanism.*

- **Source:** `fencingtracker.com` only.
- **Goal:** Scrape data, persist it to a database, and correctly identify new vs. existing registrations.
- **Out of Scope (for now):** `askfred.net` integration, email notifications, web UI.

## Architecture & Technology

- **Backend Language:** Python
- **Web Framework & API:** FastAPI
- **Database:** SQLite with the SQLAlchemy ORM
- **Web Scraping:** Requests & BeautifulSoup
- **Job Scheduling:** APScheduler

## Data Model & Change Detection

### Core Schema
- **`tournaments`**
  - `id` (PK)
  - `name` (TEXT, UNIQUE)
  - `date` (TEXT)
- **`fencers`**
  - `id` (PK)
  - `name` (TEXT, UNIQUE)
- **`registrations`**
  - `id` (PK)
  - `fencer_id` (FK)
  - `tournament_id` (FK)
  - `events` (TEXT)
  - `last_seen_at` (DATETIME)
  - UNIQUE constraint on (`fencer_id`, `tournament_id`)

### Change Detection Workflow
1.  The scheduler triggers the `scraper_service`.
2.  The scraper fetches all current registrations from the website.
3.  For each scraped registration:
    a.  Use a `get_or_create` pattern for the fencer and tournament to get their IDs.
    b.  Attempt to find an existing registration matching `(fencer_id, tournament_id)`.
    c.  **If it exists:** Update the `last_seen_at` timestamp and check if the `events` string has changed. If events changed, this is a **MODIFIED** registration.
    d.  **If it does not exist:** This is a **NEW** registration. Create the record in the `registrations` table and set the `last_seen_at` timestamp.
4.  After processing all scraped items, any registration in our database that wasn't seen in the latest scrape (i.e., its `last_seen_at` is older than the current job's start time) can be considered **REMOVED** (e.g., the fencer withdrew).

## Future Planning

### Notification Service Plan
- **Provider:** Start with Python's built-in `smtplib` and a local SMTP server (like `python -m smtpd -c DebuggingServer -n localhost:1025`) for development. For production, use a transactional email service like SendGrid or AWS SES.
- **Configuration:** Store credentials and settings in environment variables (e.g., `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`).
- **Behavior:** Implement retries on failure. Establish a "quiet hours" policy to avoid sending notifications at night.

### Scraper Constraints
- The `robots.txt` for `fencingtracker.com` is permissive. However, we will implement a respectful scrape frequency (e.g., no more than once per hour) to be a good web citizen.