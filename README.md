# Fencing Club Registration Notifications

A multi-user system to monitor fencing tournament registrations on fencingtracker.com, letting each user track their own clubs and receive daily digest emails when new registrations appear.

## Quick Start

### Prerequisites

- Python 3.8+
- Mailgun account with API access

### Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   Copy the sample environment file `.env.example` to `.env` and fill in the required values:
   ```bash
   cp .env.example .env
   ```

3. Apply database migrations:
   ```bash
   alembic upgrade head
   ```

4. Create the initial admin user (interactive password prompt):
   ```bash
   python -m app.main create-admin admin admin@example.com
   ```

5. Test your Mailgun configuration:
   ```bash
   python -m app.main send-test-email
   ```

   If successful, you should see:
   ```
   Test email sent successfully. Message ID: <message-id>
   ```

### Usage

#### Scrape registrations from a club URL

```bash
python -m app.main scrape https://www.fencingtracker.com/clubs/your-club-name
```

This will:
- Fetch the registration page
- Parse and store registration data
- Send email notifications for any new registrations found

#### Test email configuration

Send a test email to verify Mailgun setup:

```bash
# Use default recipients
python -m app.main send-test-email

# Send to specific recipient
python -m app.main send-test-email user@example.com
```

#### Start the web API

```bash
uvicorn app.main:app --reload
```

Key endpoints while developing:
- `http://localhost:8000/login` – Sign in or register a new user.
- `http://localhost:8000/dashboard` – View active and inactive tracked clubs.
- `http://localhost:8000/clubs` – Manage tracked clubs and weapon filters.
- `http://localhost:8000/fencers` – Manage tracked fencers.
- `http://localhost:8000/admin/users` – Admin-only user management.
- `http://localhost:8000/health` – Lightweight readiness probe.

#### Manage tracked fencers

1. Open the "Tracked Fencers" card on the dashboard or visit `/fencers`.
2. **Paste the full fencingtracker profile URL** (e.g., `https://fencingtracker.com/p/100349376/Jake-Mann`). The URL **must include the name slug** (e.g., `/Jake-Mann`) to work correctly.
3. The fencer's display name is automatically extracted from the URL slug.
4. Optionally add a comma-separated weapon filter (`foil,epee,saber`). Leave blank to track every weapon.
5. Click "Track fencer" to save. Scrapes respect delay and cooldown settings, so new registrations may take a few minutes to appear.

**Important:** The scraper processes only the "Registrations" table from fencer profiles, not historical "Results" data. Use the DELETE button (not just deactivate) to permanently remove a tracked fencer and start fresh if needed.

#### Run the scheduled scraper

Use APScheduler to scrape one or more clubs on an interval:

```bash
python -m app.main schedule \
  --club-url https://fencingtracker.com/club/100261977/Elite%20FC/registrations \
  --interval 30
```

If `SCRAPER_CLUB_URLS` and `SCRAPER_INTERVAL_MINUTES` are set in `.env` you can omit the command-line options. Pass `--no-run-now` to skip the immediate startup scrape.

#### Run the daily digest scheduler

```bash
python -m app.main digest-scheduler
```

This starts a blocking APScheduler process that sends per-user digest emails every day at 9:00 AM (system timezone). Use `CTRL+C` to stop. For manual testing you can send a one-off digest:

```bash
python -m app.main send-user-digest 1  # replace with a real user ID
```

## Database Migrations

This project uses [Alembic](https://alembic.sqlalchemy.org/) for database schema management. All schema changes must be applied via migrations.

### Applying Migrations

**First time setup:**
```bash
# Apply all migrations to bring database to latest schema
alembic upgrade head
```

**After pulling new code with migrations:**
```bash
# Check current migration status
alembic current

# Apply any pending migrations
alembic upgrade head
```

### Creating New Migrations

When you modify models in `app/models.py`:

1. **Generate migration from model changes:**
   ```bash
   alembic revision --autogenerate -m "add tracked_fencers table"
   ```

2. **Review the generated migration:**
   - Open `migrations/versions/<revision_id>_*.py`
   - Verify the `upgrade()` and `downgrade()` functions are correct
   - Add custom SQL or data transformations if needed

3. **Apply the migration locally:**
   ```bash
   alembic upgrade head
   ```

4. **Test your changes:**
   ```bash
   pytest
   ```

### Migration Commands Reference

| Command | Description |
|---------|-------------|
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Rollback last migration |
| `alembic current` | Show current migration version |
| `alembic history` | List all migrations |
| `alembic revision --autogenerate -m "msg"` | Create new migration from model changes |

### Environment Variables

Alembic respects the `DATABASE_URL` environment variable. If not set, it defaults to `sqlite:///./fc_registration.db`.

```bash
# Use alternate database for testing
DATABASE_URL=sqlite:///./test.db alembic upgrade head
```

### Troubleshooting & Recovery

**If a migration fails locally:**

1. **Inspect the error** and identify the issue in the migration script
2. **Fix the migration file** in `migrations/versions/`
3. **Rerun the upgrade:**
   ```bash
   alembic upgrade head
   ```

**If the migration is broken beyond repair:**

1. **For development databases (data loss acceptable):**
   ```bash
   # Delete local database and start fresh
   rm fc_registration.db
   alembic upgrade head
   ```

2. **For databases with data you need to keep:**
   ```bash
   # Downgrade to previous version
   alembic downgrade -1

   # Fix the migration script
   # Then upgrade again
   alembic upgrade head
   ```

**Production migration failures:**

1. **ALWAYS backup before running migrations:**
   ```bash
   cp fc_registration.db fc_registration.db.backup-$(date +%Y%m%d-%H%M%S)
   ```

2. **If migration fails, restore from backup:**
   ```bash
   cp fc_registration.db.backup-YYYYMMDD-HHMMSS fc_registration.db
   ```

3. **Test the fixed migration on a copy of production data** before retrying in production

### Important Notes

- **Always review autogenerated migrations** before applying them. Alembic's autogenerate is helpful but not perfect.
- **SQLite limitations**: Some operations (like renaming columns) require table rebuilds. Test thoroughly.
- **Production**: Always backup your database before running migrations in production.
- **Never edit applied migrations**: If a migration is already applied (shows in `alembic history`), create a new migration to fix issues rather than editing the old one.

## Configuration

All configuration is handled via environment variables. See `docs/ARCHITECTURE.md` for complete details.

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MAILGUN_API_KEY` | API key from Mailgun dashboard | `key-abc123...` |
| `MAILGUN_DOMAIN` | Sending domain configured in Mailgun | `mg.yourdomain.com` |
| `MAILGUN_SENDER` | From email address | `notifications@yourdomain.com` |
| `MAILGUN_DEFAULT_RECIPIENTS` | Comma-separated recipient emails | `admin@example.com,alerts@example.com` |
| `DATABASE_URL` | Database connection string used by Alembic and CLI overrides | `sqlite:///./fc_registration.db` |
| `SCRAPER_CLUB_URLS` | Comma-separated club registration URLs for scheduled scraping | `https://fencingtracker.com/club/100261977/Elite%20FC/registrations` |
| `SCRAPER_INTERVAL_MINUTES` | Minutes between scheduled scrapes | `30` |
| `FENCER_SCRAPE_ENABLED` | Toggle the tracked fencer scraper job | `true` |
| `FENCER_SCRAPE_DELAY_SEC` | Base seconds between fencer profile requests | `5` |
| `FENCER_SCRAPE_JITTER_SEC` | Random jitter applied to each fencer request | `2` |
| `FENCER_MAX_FAILURES` | Consecutive failures before a fencer enters cooldown | `3` |
| `FENCER_FAILURE_COOLDOWN_MIN` | Minutes to wait before retrying after max failures | `60` |
| `ADMIN_EMAIL` | Optional address for new user signup alerts | `owner@example.com` |
| `SESSION_COOKIE_SECURE` | Set to `true` in production to force secure cookies | `true` |

### Security Configuration

#### CSRF Protection

All state-changing endpoints (POST/PATCH/DELETE) are protected against Cross-Site Request Forgery (CSRF) attacks:

- CSRF tokens are automatically generated and stored in user sessions
- Tokens are embedded in HTML forms via the `{{ csrf_token() }}` template helper
- API requests must include the token in the `X-CSRF-Token` header
- Invalid or missing tokens result in 403 Forbidden responses

**Note:** Login and registration endpoints do not require CSRF tokens (no existing session to protect), but are protected by rate limiting instead.

#### Rate Limiting

Authentication endpoints are protected against brute-force attacks with configurable rate limits:

| Variable | Default | Description |
|----------|---------|-------------|
| `LOGIN_RATE_LIMIT_ATTEMPTS` | `5` | Maximum login attempts per username within the window |
| `LOGIN_RATE_LIMIT_WINDOW_SEC` | `300` | Time window for login rate limiting (5 minutes) |
| `REGISTER_RATE_LIMIT_ATTEMPTS` | `3` | Maximum registration attempts per IP within the window |
| `REGISTER_RATE_LIMIT_WINDOW_SEC` | `3600` | Time window for registration rate limiting (1 hour) |

**Rate Limiting Behavior:**
- Login attempts are tracked per username
- Registration attempts are tracked per client IP address
- Successful logins reset the rate limit counter for that username
- Rate limits are stored in-memory and reset on process restart
- 429 Too Many Requests responses include a `Retry-After` header

**Production Considerations:**
- In-memory rate limiting is suitable for single-process deployments
- For multi-process or distributed deployments, consider external rate limiting (nginx, Cloudflare, or Redis-backed service)
- If behind a proxy, the service reads the `X-Forwarded-For` header to determine client IP

## Development

See `docs/ARCHITECTURE.md` for detailed system architecture and development guidelines.

### Running Tests

```bash
pytest
```

### Project Structure

```
├── app/
│   ├── api/
│   │   ├── admin.py               # Admin-only routes
│   │   ├── auth.py                # Login, registration, session handling
│   │   ├── clubs.py               # Tracked club management routes
│   │   └── dependencies.py        # Shared FastAPI dependencies
│   ├── services/
│   │   ├── auth_service.py        # User registration, hashing, sessions
│   │   ├── club_validation_service.py  # Club URL validation helpers
│   │   ├── digest_service.py      # Daily digest generation and scheduler helpers
│   │   ├── notification_service.py# Email sending wrappers
│   │   └── scraper_service.py     # Web scraping logic
│   ├── templates/                 # Jinja2 templates for the web UI
│   ├── models.py                  # SQLAlchemy models (users, clubs, registrations)
│   ├── crud.py                    # Database operations
│   └── main.py                    # FastAPI app and Typer CLI commands
├── docs/
│   └── ARCHITECTURE.md            # System documentation
└── tests/                         # Pytest test suite
```

## Deployment

### Deployment Checklist

#### Infrastructure
- [ ] Set `SESSION_COOKIE_SECURE=true` in production `.env`.
- [ ] Configure HTTPS (required for secure cookies).
- [ ] Set up a process manager (e.g., systemd, supervisord) for the three required processes:
  - FastAPI web app: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
  - Scraper scheduler: `python -m app.main schedule`
  - Digest scheduler: `python -m app.main digest-scheduler`
- [ ] Configure SQLite WAL mode if not already enabled, to support concurrent processes.
- [ ] Set up log rotation for application logs.
- [ ] Configure firewall rules to expose only necessary ports (e.g., 80/443).

#### Configuration
- [ ] Ensure all production Mailgun credentials are set and DNS records (SPF/DKIM) are verified.
- [ ] Set `ADMIN_EMAIL` to the real administrator's address.
- [ ] Review and set production-level values for `SCRAPER_CLUB_URLS` and `SCRAPER_INTERVAL_MINUTES`.

#### Database
- [ ] Apply all migrations: `alembic upgrade head`.
- [ ] Create the initial admin account: `python -m app.main create-admin <username> <email>`.
- [ ] Establish and test a database backup and restore strategy for `fc_registration.db`.

#### Verification
- [ ] Send a test email to confirm Mailgun integration is working in production: `python -m app.main send-test-email`.
- [ ] Perform an end-to-end test:
    1. Register a new test user and verify the admin notification email is received.
    2. Add a tracked club and confirm that the scraper runs successfully.
    3. Manually trigger a user digest (`python -m app.main send-user-digest <user_id>`) and verify it is received and correct.
    4. Confirm all three background processes are running stably via the process manager.

### Production Environment Variables

Ensure all required variables are set in your production `.env`:

```bash
# Mailgun (required)
MAILGUN_API_KEY=your-real-api-key
MAILGUN_DOMAIN=mg.yourdomain.com
MAILGUN_SENDER=notifications@yourdomain.com
MAILGUN_DEFAULT_RECIPIENTS=admin@yourdomain.com

# Admin notifications
ADMIN_EMAIL=admin@yourdomain.com

# Security (required for production)
SESSION_COOKIE_SECURE=true

# Scraper configuration
SCRAPER_CLUB_URLS=https://fencingtracker.com/club/...
SCRAPER_INTERVAL_MINUTES=720

# Fencer scraper configuration
FENCER_SCRAPE_ENABLED=true
FENCER_SCRAPE_DELAY_SEC=5
FENCER_SCRAPE_JITTER_SEC=2
FENCER_MAX_FAILURES=3
FENCER_FAILURE_COOLDOWN_MIN=60
```

## License

[License information to be added]
