# Tech Advisor Notes – 2025-09-25

ADVISORY NOTES (Fencing Club Registration Notifications)
- **Good**: Straightforward Python-first stack and component list frame the ingest→notify flow without unnecessary services (`comms/planning/2025-09-25-initial-planning.md:10`).
- **Risk (med)**: v0 scope spans two scrapers, notifications, scheduler, and web UI before we’ve proven a single connector → Action: tighten first milestone to fencingtracker + persistence + change detection, backlog AskFRED + UI until notifications work (same ref).
- **Risk (med)**: Plan doesn’t define how registrations map into tables or how to diff new vs. existing rows, risking duplicate/missed alerts → Action: sketch core schema (clubs, fencers, tournaments, registrations) with uniqueness + `last_seen_at`, outline diff workflow (`comms/planning/2025-09-25-initial-planning.md:11`).
- **Risk (low)**: Email notifications lack delivery plan (provider, auth, dev/test story) → Action: pick initial transport (local SMTP vs. SendGrid/SES), list env vars, note retry/quiet-hour expectations (`comms/planning/2025-09-25-initial-planning.md:12`).
- **Question**: Any scrape-frequency / robots.txt constraints we must honor when scheduling? (`comms/planning/2025-09-25-initial-planning.md:13`).

Suggested immediate next steps:
1. Trim and circulate the narrower milestone scope for consent.
2. Draft the lightweight data model + change detection note so implementation has clear targets.
3. Choose and document the email delivery approach (including local dev workflow) before wiring notifications.
