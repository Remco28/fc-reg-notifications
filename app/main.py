import logging
import os
from datetime import datetime
from typing import List, Optional

import typer
from apscheduler.schedulers.blocking import BlockingScheduler
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from .database import init_db, get_db, SessionLocal
from .services import scraper_service
from .services.notification_service import send_registration_notification
from .services.mailgun_client import NotificationError
from .api.endpoints import router

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Fencing Club Registration Notifications",
    description="An API to track and get notified about fencing tournament registrations."
)

# Include the API router
app.include_router(router)

cli = typer.Typer()
logger = logging.getLogger(__name__)

DEFAULT_SCRAPE_INTERVAL_MINUTES = 30


def _parse_club_urls(raw: Optional[str]) -> List[str]:
    if not raw:
        return []

    return [url.strip() for url in raw.split(',') if url.strip()]


def _resolve_interval(value: Optional[str], fallback: int) -> int:
    if value is None:
        return fallback

    try:
        minutes = int(value)
    except ValueError as exc:
        raise ValueError("SCRAPER_INTERVAL_MINUTES must be an integer") from exc

    if minutes <= 0:
        raise ValueError("SCRAPER_INTERVAL_MINUTES must be greater than 0")

    return minutes


def _run_scrape_job(club_url: str) -> None:
    session = SessionLocal()

    try:
        stats = scraper_service.scrape_and_persist(session, club_url)
        logger.info(
            "Scrape finished for %s (new=%s updated=%s total=%s)",
            club_url,
            stats["new"],
            stats["updated"],
            stats["total"],
        )
    except Exception:  # pragma: no cover - logged for ops visibility
        logger.exception("Scrape failed for %s", club_url)
    finally:
        session.close()


@cli.command()
def db_init():
    """Initialize the database and create tables."""
    typer.echo("Initializing database...")
    init_db()
    typer.echo("Database initialized.")


@cli.command()
def scrape(
    club_url: str = typer.Argument(
        ..., help="The URL of the club registration page on fencingtracker.com"
    )
):
    """Run the scraper for a specific club URL."""
    typer.echo(f"Scraping registrations from {club_url}")
    db = next(get_db())
    try:
        result = scraper_service.scrape_and_persist(db, club_url)
        typer.echo(
            f"Scraping complete. Total: {result['total']}, New: {result['new']}, Updated: {result['updated']}"
        )
    finally:
        db.close()


@cli.command()
def send_test_email(recipient: str = typer.Argument(None, help="Optional recipient email address")):
    """Send a test email via Mailgun to verify configuration."""
    typer.echo("Sending test email...")

    try:
        recipients = [recipient] if recipient else None
        message_id = send_registration_notification(
            fencer_name="Test Fencer",
            tournament_name="Test Tournament",
            events="Test Event",
            source_url="https://example.com/test",
            recipients=recipients,
        )
        typer.echo(f"Test email sent successfully. Message ID: {message_id}")
    except NotificationError as e:
        typer.echo(f"Failed to send test email: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1)


@cli.command("schedule")
def schedule_scraper(
    club_url: Optional[List[str]] = typer.Option(
        None,
        "--club-url",
        "-u",
        help="Club registration URL to monitor. Provide multiple times for more than one club.",
    ),
    interval: Optional[int] = typer.Option(
        None,
        "--interval",
        "-i",
        help="Minutes between scrapes. Defaults to SCRAPER_INTERVAL_MINUTES env var or 30.",
    ),
    run_now: bool = typer.Option(
        True,
        "--run-now/--no-run-now",
        help="Scrape immediately before scheduling recurring jobs.",
    ),
):
    """Run APScheduler to scrape one or more clubs at a fixed interval."""

    urls = club_url or _parse_club_urls(os.getenv("SCRAPER_CLUB_URLS"))

    if not urls:
        raise typer.BadParameter(
            "No club URLs provided. Use --club-url or set SCRAPER_CLUB_URLS in the environment."
        )

    if interval is not None and interval <= 0:
        raise typer.BadParameter("--interval must be greater than 0")

    try:
        configured_interval = interval or _resolve_interval(
            os.getenv("SCRAPER_INTERVAL_MINUTES"), DEFAULT_SCRAPE_INTERVAL_MINUTES
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(f"Scheduling {len(urls)} club(s) every {configured_interval} minute(s)")
    init_db()

    if run_now:
        typer.echo("Running initial scrape...")
        for url in urls:
            _run_scrape_job(url)

    scheduler = BlockingScheduler()

    for idx, url in enumerate(urls):
        job_id = f"scrape_{idx}"
        scheduler.add_job(
            _run_scrape_job,
            "interval",
            minutes=configured_interval,
            args=[url],
            id=job_id,
            next_run_time=datetime.utcnow(),
        )
        typer.echo(f"Scheduled job {job_id} for {url}")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        typer.echo("Scheduler stopped")


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    cli()
