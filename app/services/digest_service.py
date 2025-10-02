"""Daily digest email generation and scheduling."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy.orm import Session

from app import crud
from app.database import SessionLocal
from app.models import Registration, TrackedClub, User

from .notification_service import send_registration_notification


logger = logging.getLogger(__name__)

DIGEST_LOOKBACK_HOURS = 24


def apply_weapon_filter(
    registrations: Iterable[Registration],
    weapon_filter: Optional[str],
) -> List[Registration]:
    """Filter registrations to those that match the configured weapons."""
    if not weapon_filter:
        return list(registrations)

    allowed = {
        weapon.strip().lower()
        for weapon in weapon_filter.split(",")
        if weapon and weapon.strip()
    }

    if not allowed:
        return list(registrations)

    filtered: List[Registration] = []
    for registration in registrations:
        events_lower = registration.events.lower()
        if any(weapon in events_lower for weapon in allowed):
            filtered.append(registration)

    return filtered


def _collect_sections(
    db: Session,
    tracked_clubs: List[TrackedClub],
    since: datetime,
) -> List[Dict[str, object]]:
    sections: List[Dict[str, object]] = []

    for tracked in tracked_clubs:
        registrations = crud.get_registrations_by_club_url(db, tracked.club_url, since=since)
        filtered = apply_weapon_filter(registrations, tracked.weapon_filter)

        if not filtered:
            continue

        section_rows = []
        for registration in filtered:
            section_rows.append(
                {
                    "fencer_name": registration.fencer.name,
                    "events": registration.events,
                    "tournament_name": registration.tournament.name,
                    "club_url": tracked.club_url,
                }
            )

        sections.append(
            {
                "club_name": tracked.club_name or tracked.club_url,
                "club_url": tracked.club_url,
                "rows": section_rows,
            }
        )

    return sections


def format_digest_email(user: User, sections: List[Dict[str, object]]) -> str:
    """Return a plain-text digest email body."""
    total_registrations = sum(len(section["rows"]) for section in sections)

    lines = [
        f"Hi {user.username},",
        "",
        f"Here are {total_registrations} new registrations from the past 24 hours:",
        "",
    ]

    for section in sections:
        club_name = section["club_name"]
        lines.append(club_name)
        lines.append("-" * len(club_name))

        for row in section["rows"]:
            lines.append(
                f"* {row['fencer_name']} - {row['events']} ({row['tournament_name']})"
            )

        lines.append(f"Club page: {section['club_url']}")
        lines.append("")

    lines.extend(
        [
            "Manage your tracking preferences:",
            "/clubs",  # Relative path; replace with production URL if needed
            "",
            "- The Fencing Tracker Team",
        ]
    )

    return "\n".join(lines)


def send_user_digest(db: Session, user: User) -> bool:
    """Generate and send a digest email for a single user.

    Returns True if an email was sent, otherwise False.
    """
    if not user.email:
        logger.info("User %s has no email address configured; skipping", user.id)
        return False

    tracked_clubs = crud.get_tracked_clubs(db, user.id, active=True)
    if not tracked_clubs:
        logger.debug("User %s has no tracked clubs; skipping digest", user.id)
        return False

    since = datetime.utcnow() - timedelta(hours=DIGEST_LOOKBACK_HOURS)
    sections = _collect_sections(db, tracked_clubs, since)

    if not sections:
        logger.info("No new registrations for user %s; skipping digest", user.id)
        return False

    subject = f"Daily fencing update ({sum(len(s['rows']) for s in sections)} new)"
    body = format_digest_email(user, sections)

    send_registration_notification(
        fencer_name="",
        tournament_name="",
        events="",
        source_url="",
        recipients=[user.email],
        subject=subject,
        body=body,
    )

    logger.info(
        "Sent digest to user %s (%s) with %s new registrations",
        user.id,
        user.email,
        sum(len(section["rows"]) for section in sections),
    )

    return True


def send_daily_digests() -> None:
    """Send digests to all active users."""
    session = SessionLocal()
    try:
        users = crud.get_active_users(session)
        for user in users:
            try:
                send_user_digest(session, user)
                session.expire_all()
            except Exception as exc:  # pragma: no cover - defensive logging
                session.rollback()
                logger.exception("Failed to send digest to user %s: %s", user.id, exc)
    finally:
        session.close()


def start_digest_scheduler() -> None:
    """Start the blocking APScheduler for digests."""
    scheduler = BlockingScheduler()
    scheduler.add_job(
        send_daily_digests,
        "cron",
        hour=9,
        minute=0,
        id="daily_digest",
    )

    logger.info("Daily digest scheduler started (9:00 AM)")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):  # pragma: no cover - CLI convenience
        logger.info("Digest scheduler stopped")
