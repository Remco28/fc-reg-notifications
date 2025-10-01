# Architecture Overview

Short overview of the fencing club registration notifications system as of 2025-09-26.

## System Components

### Core Services
- **FastAPI Application** (`app/main.py`) – Exposes the REST surface (currently `GET /health`) and hosts the Typer CLI entry point for operational commands.
- **Scraper Service** (`app/services/scraper_service.py`) – Fetches club registration pages from fencingtracker.com, normalizes rows, and persists changes; filters out non-tournament headings (e.g., club headers, "Tournaments") and skips duplicate sections to avoid double-loading registrations.
- **Scheduler CLI** (`app/main.py schedule`) – Uses APScheduler to trigger `scrape_and_persist` for one or more clubs on a fixed interval; reads `SCRAPER_CLUB_URLS` and `SCRAPER_INTERVAL_MINUTES` from the environment with CLI overrides.
- **Auth Service** (`app/services/auth_service.py`) – Handles user registration, password hashing (bcrypt), session lifecycle management, and admin notifications on new signups.
- **Digest Service** (`app/services/digest_service.py`) – Builds per-user daily digest emails based on tracked clubs and sends them via Mailgun; exposes scheduler helpers and a manual CLI trigger.
- **Notification Service** (`app/services/notification_service.py`) – Sends transactional emails via Mailgun when the scraper detects newly created registrations.
- **Mailgun Client** (`app/services/mailgun_client.py`) – Handles Mailgun API integration with retry logic and error handling.

### Supporting Services
- **Database** – SQLite file (`fc_registration.db`) storing fencers, tournaments, and registrations.
- **Message Broker / Cache** – Not used yet; polling + DB writes are sufficient at current scale.

### Process Architecture
```
Typer CLI / FastAPI
        |
        +---- SQLAlchemy (users, sessions, tracked_clubs, registrations)
        |
        +---- Auth Service -----+--> Session cookies (FastAPI)
        |                       |
        |                       +--> Admin notification emails
        |
        +---- Scraper Service --+--> Registration rows
        |                       |
        |                       +--> Notification Service --> Mailgun
        |
        +---- Digest Service ------> Daily digests (Mailgun)
        |
        +---- APScheduler jobs (scrape scheduler, digest scheduler)
```
Single process today: FastAPI app bootstraps the CLI and orchestrates scraper, authentication, and notification logic.

## Data Flow Examples

### Scrape & Notify
```
`typer scrape <club_url>` → Scraper Service → requests GET club page → parse table rows → CRUD layer upserts entities → commit → if new registration → Notification Service → Mailgun API → email delivery
```

### Daily Digest
```
`typer digest-scheduler` (or manual CLI run) → Digest Service → load active users → gather registrations created in the last 24 hours per tracked club → apply weapon filters → format digest email → Notification Service → Mailgun API → per-user delivery
```

### Health Check
```
Client → FastAPI `GET /health` → return `{ "status": "ok" }`
```

## Key Abstractions

- **Entities/Aggregates**: `Fencer`, `Tournament`, `Registration` (`app/models.py`) with unique constraints preventing duplicate registrations per tournament.
- **User Management**: `User`, `UserSession`, and `TrackedClub` models capture authentication, session persistence, and per-user club preferences.
- **Boundaries**: CLI commands (`typer`), HTTP API (FastAPI), services layer (`scraper_service`, `notification_service`), persistence (`crud`, `database`).
- **Events**: Implicit “new registration detected” handled synchronously inside the scraper; no event bus yet.

## Authentication & Authorization

- Username/password login backed by bcrypt hashes stored in `users.password_hash`.
- Sessions persisted in `user_sessions` with 30-day expiry and delivered via HTTP-only cookies.
- Admin-only routes enforce `is_admin` via FastAPI dependencies; bootstrap via the `create-admin` CLI command.

## Configuration

- `.env` loaded at startup in `app/main.py` via `python-dotenv`.
- Core variables for Mailgun email delivery:
  - `MAILGUN_API_KEY` - API key from Mailgun dashboard (required)
  - `MAILGUN_DOMAIN` - Sending domain configured in Mailgun (required)
  - `MAILGUN_SENDER` - From email address (required)
  - `MAILGUN_DEFAULT_RECIPIENTS` - Comma-separated list of recipient emails (required)
- Authentication settings:
  - `ADMIN_EMAIL` - Optional explicit recipient for new user alerts (defaults to first Mailgun recipient).
  - `SESSION_COOKIE_SECURE` - Set to `true` in production to force secure cookies.
- Additional settings (e.g., alternate DB URL) would be introduced via env vars before adding code-level defaults.

### Environment Variables Example
```bash
MAILGUN_API_KEY=key-1234567890abcdef1234567890abcdef
MAILGUN_DOMAIN=mg.yourdomain.com
MAILGUN_SENDER=notifications@yourdomain.com
MAILGUN_DEFAULT_RECIPIENTS=admin@yourdomain.com,alerts@yourdomain.com
```

## Integration Points

- **Database**: SQLite accessed through SQLAlchemy ORM; session lifecycle managed in `database.get_db` and CLI commands.
- **External HTTP**: `requests` calls to fencingtracker.com club pages; exceptions bubble to caller for logging/handling.
- **Mailgun API**: HTTP POST requests to Mailgun's messages endpoint with retry logic (up to 3 attempts, exponential backoff); includes proper error handling and logging.

## Runtime & Operations Notes

- Start FastAPI app with Uvicorn (`uvicorn app.main:app`); CLI commands invoked via `python -m app.main ...`.
- CLI helpers:
  - `python -m app.main create-admin <username> <email>` – bootstrap first admin user.
  - `python -m app.main digest-scheduler` – run the daily digest scheduler (cron 9:00 AM system time).
  - `python -m app.main send-user-digest <user_id>` – trigger a digest for a specific user during testing.
- Test Mailgun configuration: `python -m app.main send-test-email` (optionally specify recipient).
- Database concurrency: single-process access today; keep transactions brief and rely on SQLite WAL if multi-process emerges.
- Logging: structured logging via Python logging module for scraper errors, notification failures, and Mailgun API interactions.
- Health probe: `/health` endpoint for readiness/liveness checks.
- Future scheduler can rely on APScheduler (already in requirements) to trigger `scrape` periodically.

## Development Guidelines

### For Developers
- Follow existing service separation: keep HTTP handlers thin, put logic in services, and use CRUD helpers for persistence.
- Add tests around scraper parsing and notification triggers as they evolve; mocks recommended for external HTTP/Mailgun API calls.
- Extend configuration by adding documented env vars rather than hard-coded constants.

### For Architects/Tech Leads
- Update this file when adding new surfaces (REST endpoints, background jobs, schedulers) or external integrations.
- Document non-trivial data flows (e.g., bulk imports, retries) and their failure handling so developers can implement consistently.
- Capture new infrastructure choices (queues, caches, alt databases) and how they interact with existing services.

## Future Enhancements (In Planning)

### Multi-User Platform (Phases 1-4)
The system is planned to evolve from a single-tenant notification system to a multi-user platform. See `comms/planning/2025-10-01-multi-user-enhancement.md` for full details.

**Planned capabilities:**
- User accounts with authentication (username/password)
- Per-user club and fencer tracking
- Daily digest emails (9:00 AM) with personalized content
- Weapon filtering per club/fencer
- Admin panel for user management
- Automatic data cleanup (purge tournaments older than 30 days)
- Admin notifications on new user signups

**Data model additions:**
- `users` - user accounts and authentication
- `user_sessions` - session management
- `tracked_clubs` - per-user club tracking preferences
- `tracked_fencers` - per-user fencer tracking preferences

**Architecture impact:**
- Current global scraping continues, but notifications become per-user
- Scheduler adds daily digest generation job (9:00 AM)
- Scheduler adds nightly cleanup job (midnight)
- Web UI expands from read-only to full CRUD for user preferences

## Related Docs

- Planning: `comms/planning/2025-10-01-multi-user-enhancement.md`
- Task specs: `comms/tasks/YYYY-MM-DD-*.md`
- Ops/Deployment: *(not yet authored)*
- ADRs: *(none yet)*

---

Keep this overview aligned with the system's shape; prune sections if they become stale.
