# Project Manifest: FC Registration Notifications

**Purpose:** Quick-reference map for AI contributors joining or resuming work on the project. Review these pointers at the start of each session to reorient and pick up current context efficiently.

---

## 1. Core Identity (Stable)
*High-level intent, architecture, and role definitions. Check when evaluating big-picture changes or onboarding new collaborators.*

- **Architecture Overview:** `docs/ARCHITECTURE.md`
- **Project Roadmap:** `docs/ROADMAP.md`
- **Operational Next Steps Checklist:** `NEXT_STEPS.md`

## 2. Dynamic State (Volatile)
*Current work in flight, status logs, and recent decisions. Review before starting any implementation or review cycle.*

- **Activity Log:** `comms/log.md`
- **Active Task Specs:** `comms/tasks/`
  - `2025-10-05-mailgun-ops-notes.md` (ops documentation)
  - `2025-10-06-tracked-fencer-ui-session-flow.md` (UI implementation spec)
  - `2025-10-06-phase2-testing-verification.md` (testing coverage plan)
- **Completed Specs Archive:** `comms/tasks/archive/`
- **Recent Code Status Summary:** `README.md` (Quick Start / setup instructions)


## 3. Code & Config (Entrypoints)
*Primary technical files to inspect when modifying application behavior or infrastructure.*

- **FastAPI Application Entrypoint:** `app/main.py`
- **Database Models & ORM:** `app/models.py`
- **CRUD Layer:** `app/crud.py`
- **Service Logic:** `app/services/` (notably `fencer_scraper_service.py`, `digest_service.py`, `fencer_validation_service.py`)
- **API Routes:** `app/api/` (`endpoints.py`, `auth.py`, `clubs.py`, `admin.py`)
- **Templating / UI:** `app/templates/`
- **Background Jobs & Scheduling:** see helpers in `app/main.py` and `app/services/`
- **Dependencies:** `requirements.txt`
- **Environment Configuration Template:** `.env.example`
- **Database Migrations:** `migrations/` (Alembic environment + versions)
- **Automated Tests:** `tests/` (service tests under `tests/services/`, CRUD and digest coverage in root)


## 4. Operations & Tooling
*Supporting documentation and scripts for deployment, email delivery, and runbook-style tasks.*

- **Planned Mailgun Ops Guide:** `comms/tasks/2025-10-05-mailgun-ops-notes.md` (spec for upcoming doc)
- **Scheduler & CLI Commands:** outlined in `README.md` (see Quick Start & Usage sections)
- **Virtualenv / Local Setup:** `fc-reg_env/` (local environment), instructions in `README.md`


## 5. Key Contacts & Conventions
*Reminders for collaboration norms and decision records.*

- **Commit / Review Workflow:** Follow task specs in `comms/tasks/` and log updates in `comms/log.md`
- **Testing Expectations:** Default to running `pytest`; expanded coverage tracked in `comms/tasks/2025-10-06-phase2-testing-verification.md`
- **Documentation Updates:** Reflect architectural shifts in `docs/ARCHITECTURE.md` and operational changes in forthcoming ops docs

---

Keep this manifest up to date when reorganizing documentation or adding new foundational references. If a section becomes stale, update the relevant bullets alongside the change so future sessions land in the right place immediately.
