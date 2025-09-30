# Fencing Club Registration Notifications

A system to monitor fencing tournament registrations on fencingtracker.com and send email notifications when new registrations are detected.

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
   Create a `.env` file in the project root with your Mailgun credentials:
   ```bash
   MAILGUN_API_KEY=key-1234567890abcdef1234567890abcdef
   MAILGUN_DOMAIN=mg.yourdomain.com
   MAILGUN_SENDER=notifications@yourdomain.com
   MAILGUN_DEFAULT_RECIPIENTS=admin@yourdomain.com,alerts@yourdomain.com
   ```

3. Initialize the database:
   ```bash
   python -m app.main db-init
   ```

4. Test your Mailgun configuration:
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

Access health check at: `http://localhost:8000/health`

## Configuration

All configuration is handled via environment variables. See `docs/ARCHITECTURE.md` for complete details.

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MAILGUN_API_KEY` | API key from Mailgun dashboard | `key-abc123...` |
| `MAILGUN_DOMAIN` | Sending domain configured in Mailgun | `mg.yourdomain.com` |
| `MAILGUN_SENDER` | From email address | `notifications@yourdomain.com` |
| `MAILGUN_DEFAULT_RECIPIENTS` | Comma-separated recipient emails | `admin@example.com,alerts@example.com` |

## Development

See `docs/ARCHITECTURE.md` for detailed system architecture and development guidelines.

### Running Tests

```bash
pytest
```

### Project Structure

```
├── app/
│   ├── services/           # Business logic
│   │   ├── scraper_service.py      # Web scraping
│   │   ├── notification_service.py # Email notifications
│   │   └── mailgun_client.py       # Mailgun API client
│   ├── models.py          # Database models
│   ├── crud.py           # Database operations
│   └── main.py           # CLI and FastAPI app
├── docs/
│   └── ARCHITECTURE.md   # System documentation
└── tests/                # Test suite
```

## License

[License information to be added]