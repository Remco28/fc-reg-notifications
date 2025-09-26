# Architecture Overview

Short overview of the fencing club registration notifications system as of 2025-09-26.

## System Components

### Core Services
- **FastAPI Application** (`app/main.py`) – Exposes the REST surface (currently `GET /health`) and hosts the Typer CLI entry point for operational commands.
- **Scraper Service** (`app/services/scraper_service.py`) – Fetches club registration pages from fencingtracker.com, normalizes rows, and persists changes.
- **Notification Service** (`app/services/notification_service.py`) – Sends SMTP emails when the scraper detects newly created registrations.

### Supporting Services
- **Database** – SQLite file (`fc_registration.db`) storing fencers, tournaments, and registrations.
- **Message Broker / Cache** – Not used yet; polling + DB writes are sufficient at current scale.

### Process Architecture
```
Typer CLI / FastAPI       Scraper Service            Notification Service
        |                        |                              |
        +---- SQLAlchemy Session + Models ----------------------+
        |                        |
        +---- HTTP (fencingtracker.com) ----> scrape            |
        |                        |                              |
        +------------------------ SMTP -------------------------+
```
Single process today: FastAPI app bootstraps the CLI and orchestrates scraper + notification logic.

## Data Flow Examples

### Scrape & Notify
```
`typer scrape <club_url>` → Scraper Service → requests GET club page → parse table rows → CRUD layer upserts entities → commit → if new registration → Notification Service → SMTP email
```

### Health Check
```
Client → FastAPI `GET /health` → return `{ "status": "ok" }`
```

## Key Abstractions

- **Entities/Aggregates**: `Fencer`, `Tournament`, `Registration` (`app/models.py`) with unique constraints preventing duplicate registrations per tournament.
- **Boundaries**: CLI commands (`typer`), HTTP API (FastAPI), services layer (`scraper_service`, `notification_service`), persistence (`crud`, `database`).
- **Events**: Implicit “new registration detected” handled synchronously inside the scraper; no event bus yet.

## Authentication & Authorization

- Not implemented. Health endpoint is non-sensitive; CLI expected to run in trusted environments.

## Configuration

- `.env` loaded at startup in `app/main.py` via `python-dotenv`.
- Core variables: `SMTP_HOST`, `SMTP_PORT`, `SENDER_EMAIL`, `RECIPIENT_EMAIL`; default to localhost debugging server for development.
- Additional settings (e.g., alternate DB URL) would be introduced via env vars before adding code-level defaults.

## Integration Points

- **Database**: SQLite accessed through SQLAlchemy ORM; session lifecycle managed in `database.get_db` and CLI commands.
- **External HTTP**: `requests` calls to fencingtracker.com club pages; exceptions bubble to caller for logging/handling.
- **SMTP**: Basic `smtplib.SMTP` connection; caller responsible for reliable delivery (currently best-effort with console logging).

## Runtime & Operations Notes

- Start FastAPI app with Uvicorn (`uvicorn app.main:app`); CLI commands invoked via `python -m app.main ...`.
- Database concurrency: single-process access today; keep transactions brief and rely on SQLite WAL if multi-process emerges.
- Logging: scraper prints row errors and notification failures to stdout; consider structured logging when scaling.
- Health probe: `/health` endpoint for readiness/liveness checks.
- Future scheduler can rely on APScheduler (already in requirements) to trigger `scrape` periodically.

## Development Guidelines

### For Developers
- Follow existing service separation: keep HTTP handlers thin, put logic in services, and use CRUD helpers for persistence.
- Add tests around scraper parsing and notification triggers as they evolve; mocks recommended for external HTTP/SMTP.
- Extend configuration by adding documented env vars rather than hard-coded constants.

### For Architects/Tech Leads
- Update this file when adding new surfaces (REST endpoints, background jobs, schedulers) or external integrations.
- Document non-trivial data flows (e.g., bulk imports, retries) and their failure handling so developers can implement consistently.
- Capture new infrastructure choices (queues, caches, alt databases) and how they interact with existing services.

## Related Docs

- Roadmap: `docs/ROADMAP.md`
- Task specs: `comms/tasks/YYYY-MM-DD-*.md`
- Ops/Deployment: *(not yet authored)*
- ADRs: *(none yet)*

---

Keep this overview aligned with the system’s shape; prune sections if they become stale.
