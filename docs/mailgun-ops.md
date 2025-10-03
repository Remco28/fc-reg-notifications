# Mailgun Operations Guide

This document provides operational details for configuring and maintaining Mailgun for email delivery in the FC Registration Notifications system.

## 1. Configuration

### Environment Variables
The application uses the following environment variables to connect to Mailgun. These should be stored in a `.env` file for local development or managed via secrets in a production environment.

-   `MAILGUN_API_KEY`: **(Required)** Your Mailgun API key.
    -   *Example:* `key-1234567890abcdef1234567890abcdef`
    -   *Source:* Found in the Mailgun dashboard under `Settings -> API Keys`.

-   `MAILGUN_DOMAIN`: **(Required)** The Mailgun sending domain configured for this application.
    -   *Example:* `mg.yourdomain.com`
    -   *Source:* The domain you added and verified in the Mailgun dashboard under `Sending -> Domains`.

-   `MAILGUN_SENDER`: **(Required)** The "From" email address for outgoing notifications.
    -   *Example:* `FC Notifications <notifications@yourdomain.com>`
    -   *Source:* An address on your verified Mailgun domain.

-   `ADMIN_EMAIL`: **(Optional)** The email address that receives administrative alerts, such as new user sign-ups. If not set, it defaults to the first address in `MAILGUN_DEFAULT_RECIPIENTS`.
    -   *Example:* `admin@yourdomain.com`

-   `MAILGUN_DEFAULT_RECIPIENTS`: **(Optional)** A comma-separated list of email addresses to receive test emails or system alerts. This was used in early development and is less critical now but still available.
    -   *Example:* `dev1@example.com,dev2@example.com`

### Domain Verification
For emails to be delivered successfully, the Mailgun domain must be verified.

1.  **Log in** to the Mailgun dashboard.
2.  Navigate to **Sending -> Domains**.
3.  Select your domain.
4.  Ensure that all DNS records (SPF, DKIM, DMARC) have a green checkmark, indicating they are verified. If they are not, follow the instructions provided by Mailgun to update your DNS provider's settings.
5.  Confirm the domain is not a "Sandbox" domain for production use, as sandbox domains have sending restrictions.

## 2. Manual Bounce & Complaint Playbook

This manual process is for handling email delivery issues until automated webhooks are implemented.

### Review Cadence
-   Review Mailgun logs for bounces and complaints **once per week**.

### Review Process
1.  **Log in** to the Mailgun dashboard.
2.  Navigate to **Sending -> Logs**.
3.  Use the filter controls to search for events where `Status` is **Failed** or `Event` is **Complaint**.
4.  Set the time range to cover the last 7 days.

### Remediation Steps

#### For Hard Bounces
A "hard bounce" indicates a permanent delivery failure (e.g., the email address does not exist).

1.  **Identify the recipient email address** from the log entry.
2.  **Log in** to the application's admin panel.
3.  **Find the user** associated with that email address.
4.  **Disable the user's account** to prevent further email attempts. This can be done by marking the user as inactive in the admin UI.
5.  **Record the incident:** Add a note to the user's record in the admin panel indicating why their account was disabled (e.g., "Email hard bounce on YYYY-MM-DD").
6.  **(Optional)** Contact the user through an alternate channel if one is available to inform them of the issue.

#### For Complaints
A "complaint" means the user marked the email as spam.

1.  **Identify the recipient email address** from the log entry.
2.  **Log in** to the application's admin panel.
3.  **Find the user** associated with that email address.
4.  **Disable digest and notification emails** for that user. If a feature to disable emails does not exist, disabling the user account is the next best step.
5.  **Record the incident:** Add a note to the user's record (e.g., "User filed spam complaint on YYYY-MM-DD"). Do not attempt to re-enable emails for this user without their explicit consent.

## 3. Testing

You can verify the Mailgun configuration by running the `send-test-email` command:

```bash
python -m app.main send-test-email your-email@example.com
```

This will send a test email to the specified address, confirming that the API key, domain, and sender are correctly configured.
