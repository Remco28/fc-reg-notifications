# Task: Mailgun Email Notification Helper

## Objective
Replace the SMTP stub with a Mailgun-backed helper so the app can send real transactional emails for new registrations. The helper must follow the reliability guidance from `comms/email-notification-playbook.md` (logging, retries, single-sender support) and keep the rest of the scraper flow intact.

## Background & Scope
- We now have an active Mailgun account in single-sender mode.
- Current notifications use a localhost SMTP server (`app/services/notification_service.py`) with minimal error handling.
- We only need plain-text emails today; no HTML, attachments, or alternate channels.
- Scraper continues to send one message per newly created registration.

Out of scope: domain-based sending (SPF/DKIM), webhook handling for bounces, templating system beyond a simple text layout, or multi-recipient fan-out.

## Requirements

### 1. Mailgun client module
- Create `app/services/mailgun_client.py` exposing a `MailgunEmailClient` class.
- Responsibilities:
  - Read configuration at init: `MAILGUN_API_KEY`, `MAILGUN_DOMAIN`, `MAILGUN_SENDER`, and default recipient list (`MAILGUN_DEFAULT_RECIPIENTS`, comma-separated). All must come from environment variables loaded by `python-dotenv`.
  - Validate configuration eagerly; raise a `RuntimeError` with a useful message describing which variable is missing.
  - Provide `send_text(subject: str, body: str, to: Optional[list[str]] = None, tags: Optional[list[str]] = None)`.
  - Build the POST request to `https://api.mailgun.net/v3/{domain}/messages` with HTTP basic auth (`api`, `MAILGUN_API_KEY`) and payload fields `from`, `to`, `subject`, `text`. If tags are provided, send each as `o:tag`.
  - Use a single `requests.Session` and a 10s timeout per request.
  - Implement retry policy: up to 3 attempts with exponential backoff (sleep 1s, 2s) on network errors or 5xx responses. Respect `Retry-After` header for 429 responses; otherwise treat 4xx as non-retryable.
  - Return the provider message id on success. On failure after retries, raise a `NotificationError` (define in the module) containing status code (if available) and response text.
  - Log via the standard library `logging` module at INFO on success (`message_id`, recipients) and WARNING/ERROR on retry/failure. Do not print directly.

### 2. Update notification service
- Refactor `app/services/notification_service.py` to:
  - Lazily instantiate a module-level `MailgunEmailClient` using the new class (e.g., `_client = None` and `get_client()` helper) so tests can swap/mocking easily.
  - Expose `send_registration_notification(fencer_name, tournament_name, events, source_url)` that assembles the email subject/body:
    - Subject: `New fencing registration: {fencer_name}`.
    - Body (plain text) with the fencer, tournament, event(s), and source URL, each on its own line for readability.
  - Accept optional override recipients (default to client defaults) for future extensibility.
  - Catch `NotificationError` inside `scraper_service` and log it (existing print replaced with logger call); do not swallow other exceptions.

### 3. Scraper integration
- Update `app/services/scraper_service.py` to call the new helper (`send_registration_notification`) instead of the SMTP function. Pass the current `club_url` so the email includes the origin page.
- Replace `print` statements for notification failures with `logging.getLogger(__name__)` usage to keep output consistent.

### 4. CLI smoke test
- Add a Typer command in `app/main.py` (e.g., `send-test-email`) that:
  - Accepts optional `recipient` argument (defaults to configured recipients).
  - Uses the notification service to send a test message (`subject="Mailgun configuration test"`, body explaining it is a manual test).
  - Prints the Mailgun message id to stdout so the operator knows it succeeded.
- Command should surface `NotificationError` with a clear `typer.echo` message and exit code 1.

### 5. Configuration & docs
- Document the new environment variables and expected values in `docs/ARCHITECTURE.md`, replacing the SMTP section with Mailgun details (include pointer to Mailgun dashboard for API key and note that secrets stay in `.env`).
- If a `.env.example` file exists, add placeholders; otherwise create a short section in `docs/ARCHITECTURE.md` that lists required keys.
- Update `README` (or create if missing) with quick-start instructions for running the new `send-test-email` command after configuring Mailgun.

### 6. Testing
- Add unit tests under `tests/services/` that cover:
  - Successful send path (mock `requests.Session.post` to return a 200 JSON payload and assert message id + logging call).
  - Retry then success (first call raises `RequestException`, second succeeds) verifying backoff attempts via mock call count.
  - Non-retryable 400 error raises `NotificationError` without additional attempts.
  - Missing environment variables cause `RuntimeError` during client init.
- Use fixtures/monkeypatch to avoid real HTTP calls and to control environment variables.
- Ensure existing tests continue to pass.

## Deliverables
- Updated service code (`app/services/mailgun_client.py`, `app/services/notification_service.py`, `app/services/scraper_service.py`, `app/main.py`).
- Updated documentation (`docs/ARCHITECTURE.md` and README).
- New/updated tests (`tests/services/...`).
- No secrets committed to git.

## Acceptance Criteria
- Running `python -m app.main send-test-email` with valid Mailgun credentials sends a message and prints the returned message id.
- Scraper notifications use Mailgun; failures are logged with enough detail to troubleshoot.
- Unit tests cover success, retry, and failure scenarios for the Mailgun client.
- Documentation reflects the Mailgun integration and how to configure it.
