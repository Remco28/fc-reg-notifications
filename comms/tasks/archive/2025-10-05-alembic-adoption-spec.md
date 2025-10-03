# Spec: Alembic Adoption Playbook
**Date:** 2025-10-05
**Owner:** Architect
**Status:** Draft

## Objective
Introduce Alembic migrations so schema changes (e.g., `tracked_fencers`) can be applied consistently across dev, staging, and production environments. Deliver a repeatable workflow that existing developers can follow without disrupting current data.

## Success Criteria
- Alembic configuration (`alembic.ini`, migrations folder) is committed.
- Initial migration captures the current SQLite schema with no diffs after running `alembic upgrade head`.
- Contributors understand the daily workflow: autogenerate revisions, review scripts, and apply them during deploy.
- Existing database (`fc_registration.db`) remains intact; no data loss.

## Scope
- Add Alembic to dependencies and project tooling.
- Generate baseline migration representing current models.
- Document commands for creating new migrations and applying them.
- Provide fallback steps for recovering if a migration fails locally.

Out of scope: switching databases, data seeding strategy revamp, or rewriting models.

## Implementation Plan

### 1. Tooling Setup
- Add `alembic` to `requirements.txt` (or new `dev-requirements` if we split later).
- Run `alembic init migrations` to scaffold config; store under project root.
- Modify generated `alembic.ini` to point to SQLite DB via env var (`DATABASE_URL` fallback to `sqlite:///fc_registration.db`).
- Update `env.py` to import SQLAlchemy metadata (from `app.database.Base` or equivalent) and run migrations in offline/online modes.

### 2. Baseline Migration
- Ensure local DB matches models (`python -m app.main` commands run without pending schema changes).
- Use `alembic revision --autogenerate -m "baseline schema"` to create migration script.
- Review script carefully: confirm tables, indexes, constraints align with `app/models.py`.
- Apply migration on a fresh SQLite file to verify success:
  ```bash
  rm fc_registration_test.db
  DATABASE_URL=sqlite:///fc_registration_test.db alembic upgrade head
  ```
- Once validated, run against dev DB: `alembic upgrade head` (should no-op because schema already present).

### 3. Developer Workflow Documentation
Document in README or dedicated doc section:
- Creating migrations: `alembic revision --autogenerate -m "add tracked_fencers"`.
- Hand-editing migration scripts when autogenerate misses custom SQL.
- Applying migrations locally before running tests.
- Deployment checklist: ensure the deployment process runs `alembic upgrade head`.

### 4. Fallback & Recovery
- If migration fails locally:
  1. Inspect error, fix migration script, rerun `alembic upgrade head`.
  2. To reset dev DB: delete local SQLite file and re-run upgrade.
- For production failures (future): document need for manual backup before applying migrations and how to roll back using `alembic downgrade`.

## Risks & Mitigations
- **Baseline drift** (existing DB contains manual tweaks): run schema comparison before committing baseline; adjust models or migration to match reality.
- **SQLite quirks** (limited ALTER TABLE support): autogenerate might emit operations that require table rebuild. Flag these in future migrations and test thoroughly.
- **Contributor unfamiliarity**: include quick-reference commands in docs and sample workflow in `NEXT_STEPS.md` if needed.

## Validation
- Fresh DB created via Alembic matches existing models (verified using SQLAlchemy metadata reflection or integration tests).
- Run current test suite against migrated DB to ensure nothing breaks.
- Confirm `alembic history` shows baseline revision applied.

## Deliverables
- Updated dependencies (include Alembic).
- `alembic.ini`, `migrations/` directory with baseline revision.
- Documentation snippet in README or new `docs/migrations.md` describing usage.
- Checklist item added to deployment notes (e.g., `run alembic upgrade head`).

## Follow-Up
- Once adopted, block future schema PRs until they ship migrations alongside model changes.
- Evaluate moving Mailgun ops notes into docs next (Spec #2 in roadmap).

