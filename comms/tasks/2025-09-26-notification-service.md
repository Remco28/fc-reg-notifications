# Task: Implement Email Notification Service

**Objective:** Create a service to send email notifications when new or updated registrations are detected by the scraper.

## Technical Specification

### 1. Environment Configuration

The application will need to be configured via environment variables. Create a `.env` file in the root directory and add it to `.gitignore`. For local development, it should contain:

```
# Email configuration
SMTP_HOST=localhost
SMTP_PORT=1025
SENDER_EMAIL=test@example.com
RECIPIENT_EMAIL=you@example.com
```

*Note: The developer will need to install `python-dotenv` to load these variables.*

### 2. Notification Service (`app/services/notification_service.py`)

- Create a new file for the notification service.
- Implement a function: `send_notification(subject: str, body: str)`.
- This function should:
  - Read SMTP configuration from the environment variables.
  - Use Python's `smtplib` to connect to the SMTP server and send a plain-text email.

### 3. Scraper Service (`app/services/scraper_service.py`)

- **Modify `scrape_and_persist`:**
  - It should now call the `send_notification` function when a new registration is found.
  - For each new registration, format a simple `subject` and `body` string and pass them to the notification service.
    - Example Subject: `New Fencing Registration: Zoltan Lunin`
    - Example Body: `Zoltan Lunin has registered for the Cobra Challenge SYC/RCC in JME, CME.`

### 4. Main Application (`app/main.py`)

- Update the `scrape` command to load environment variables from the `.env` file at startup.

## Local Testing

To test this without a real email server, you can use Python's built-in debugging SMTP server. Run this command in a separate terminal:

`python -m smtpd -c DebuggingServer -n localhost:1025`

When the scraper runs, any emails it sends will be printed to the console where this debugging server is running.

## Acceptance Criteria

- When the scraper detects a new registration, it calls the notification service.
- The notification service constructs and sends an email using the configuration from the `.env` file.
- Emails for new registrations are successfully received by the local debugging SMTP server.
