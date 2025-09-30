# Next Steps for Fencing Club Registration Notifications

## Milestone 1: Core Data Pipeline
- [x] Implement database models (`Tournament`, `Fencer`, `Registration`)
- [x] Implement CRUD functions for data persistence
- [x] Implement scraper for `fencingtracker.com`
- [x] Integrate scraper with CRUD functions to persist data and detect changes
- [x] Set up basic application entrypoint (`main.py`) to run the scraper

## Future Enhancements (Backlog)
- [x] Add email notification system for new/updated registrations
- [x] Build a simple web UI to display registrations
- [ ] Add scraper for `askfred.net`
- [x] Implement job scheduling with APScheduler

## Action Items: Email Notifications
- [x] Pick a transactional provider that supports single-sender mode (e.g., SendGrid, Mailgun Flex, Postmark)
- [x] Create an account and verify the personal sender address you will use for notifications
- [x] Generate API/SMTP credentials and store them securely in `.env`/secrets (not in git)
- [x] Implement a small mail helper in the app with logging + retry handling, referencing `comms/email-notification-playbook.md`
- [ ] Send a live test message and confirm delivery; note any follow-up tasks for bounce handling
- [ ] Test that your domain-based sending works (send a test email via CLI)
- [ ] Update your .env with the domain-based sender address if needed
- [x] Once a custom domain is ready, add SPF/DKIM/DMARC records and switch the provider to domain-based sending

## Documentation
- [ ] Write API documentation (initial version via FastAPI)
- [x] Add setup and usage instructions to a `README.md`
