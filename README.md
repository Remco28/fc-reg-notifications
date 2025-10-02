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
   Copy the sample file and edit it with your credentials:
   ```bash
   cp .env.example .env
   ```
   Update `.env` with your Mailgun API key, sender details, and the club URLs you want to monitor.

3. Initialize the database:
   ```bash
   python -m app.main db-init
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
- `http://localhost:8000/admin/users` – Admin-only user management.
- `http://localhost:8000/health` – Lightweight readiness probe.

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

## Configuration

All configuration is handled via environment variables. See `docs/ARCHITECTURE.md` for complete details.

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MAILGUN_API_KEY` | API key from Mailgun dashboard | `key-abc123...` |
| `MAILGUN_DOMAIN` | Sending domain configured in Mailgun | `mg.yourdomain.com` |
| `MAILGUN_SENDER` | From email address | `notifications@yourdomain.com` |
| `MAILGUN_DEFAULT_RECIPIENTS` | Comma-separated recipient emails | `admin@example.com,alerts@example.com` |
| `SCRAPER_CLUB_URLS` | Comma-separated club registration URLs for scheduled scraping | `https://fencingtracker.com/club/100261977/Elite%20FC/registrations` |
| `SCRAPER_INTERVAL_MINUTES` | Minutes between scheduled scrapes | `30` |
| `ADMIN_EMAIL` | Optional address for new user signup alerts | `owner@example.com` |
| `SESSION_COOKIE_SECURE` | Set to `true` in production to force secure cookies | `true` |

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

### Before Deploying to Production

1. **Enable secure cookies:**
   ```bash
   # In your production .env file
   SESSION_COOKIE_SECURE=true
   ```

2. **Configure HTTPS:**
   - Secure cookies require HTTPS to function
   - Set up SSL/TLS certificate (Let's Encrypt recommended)
   - Configure reverse proxy (nginx/Apache) if needed

3. **Initialize the database:**
   ```bash
   python -m app.main db-init
   ```

4. **Create the first admin account:**
   ```bash
   python -m app.main create-admin admin admin@example.com
   # You'll be prompted for a password (hidden input)
   ```

5. **Test Mailgun configuration:**
   ```bash
   python -m app.main send-test-email
   ```

6. **Set up process management:**
   You need to run three processes concurrently:
   - Web app: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - Scraper scheduler: `python -m app.main schedule`
   - Digest scheduler: `python -m app.main digest-scheduler`

   Use systemd, supervisord, or pm2 to manage these processes.

7. **Configure backups:**
   - Set up regular backups of `fc_registration.db`
   - Test restore procedure

8. **End-to-end testing:**
   - Register a test user and verify admin notification
   - Add a test club and verify scraping works
   - Manually trigger a digest: `python -m app.main send-user-digest 1`

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
```

## License

[License information to be added]
