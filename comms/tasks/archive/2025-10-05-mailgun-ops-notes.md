# Task Spec: Mailgun Ops Notes
**Date:** 2025-10-05
**Owner:** Architect
**Status:** Spec Ready

## Objective
Document Mailgun operational details so future deploys can reproduce the current email configuration and handle delivery issues (bounces/complaints) without guesswork.

## Deliverables
1. A short deployment/ops doc (suggest `docs/mailgun-ops.md`) covering:
   - Required environment variables (`MAILGUN_API_KEY`, `MAILGUN_DOMAIN`, `MAILGUN_SENDER`, optional `MAILGUN_DEFAULT_RECIPIENTS`, `ADMIN_EMAIL`).
   - Where values live today (e.g., `.env` template, secrets manager) and expected formats/examples.
   - Steps to verify Mailgun domain status (SPF/DKIM/DMARC, sending sandbox vs. production domain).
2. Manual bounce & complaint playbook:
   - How often to review Mailgun logs/events.
   - What to do when a bounce or complaint occurs (flag user, pause digest sending, contact user/admin).
   - Where to record incidents (log file, admin UI note, etc.).
3. Checklist update in `NEXT_STEPS.md` (or deployment notes) marking Mailgun documentation as complete once shipped.

## Work Items
- Create `docs/mailgun-ops.md` with the sections above. Use concise bullets and include command/reference links where helpful (e.g., Mailgun dashboard URLs).
- Update `.env.example` or equivalent template if it exists; otherwise add TODO note indicating where new engineers should place secrets.
- Add a pointer from `docs/ARCHITECTURE.md` (Configuration section) to the new ops doc.
- Update `NEXT_STEPS.md` → check off "Mailgun ops notes" once merged.

## Constraints & Assumptions
- Mailgun credentials already functional; no API changes needed.
- Manual process is acceptable (no webhook automation yet). Document it plainly so non-engineers can execute.
- Do not commit real secrets; use placeholders in documentation.

## Acceptance Criteria
- New ops doc reviewed for accuracy (double-check environment variable names and required values).
- Architecture doc references the new ops guide.
- NEXT_STEPS checklist item updated.
- Reviewer confirms bounce/complaint flow contains actionable steps (review cadence, responsible role, remediation actions).

## Risks & Mitigations
- **Missing context on current setup**: interview current maintainer (Frank) or inspect `.env` to confirm values before documenting.
- **Playbook too vague**: include explicit actions (e.g., "disable user via admin panel"), not just "review mailgun".
- **Doc rot**: add reminder in roadmap/backlog to revisit when automated handling arrives.

## Validation
- Run through doc instructions on a fresh environment (dry run) to ensure Mailgun config steps make sense.
- Test bounce playbook with a simulated scenario (e.g., mark test user as bounced in log) or note procedure to simulate if real bounce cannot be triggered.

## Follow-Up
- Once documentation lands, schedule review during next ops sync to ensure team alignment.
- Consider adding automated alerting/webhooks in a later phase if bounce volume becomes non-trivial.
