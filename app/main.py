import typer
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from .database import init_db, get_db
from .services import scraper_service
from .services.notification_service import send_registration_notification
from .services.mailgun_client import NotificationError

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Fencing Club Registration Notifications",
    description="An API to track and get notified about fencing tournament registrations."
)

cli = typer.Typer()

@cli.command()
def db_init():
    """Initialize the database and create tables."""
    typer.echo("Initializing database...")
    init_db()
    typer.echo("Database initialized.")

@cli.command()
def scrape(club_url: str = typer.Argument(..., help="The URL of the club registration page on fencingtracker.com")):
    """Run the scraper for a specific club URL."""
    typer.echo(f"Scraping registrations from {club_url}")
    db = next(get_db())
    try:
        result = scraper_service.scrape_and_persist(db, club_url)
        typer.echo(f"Scraping complete. Total: {result['total']}, New: {result['new']}, Updated: {result['updated']}")
    finally:
        db.close()

@cli.command()
def send_test_email(recipient: str = typer.Argument(None, help="Optional recipient email address")):
    """Send a test email via Mailgun to verify configuration."""
    typer.echo("Sending test email...")

    try:
        # Use a dummy registration notification for testing
        recipients = [recipient] if recipient else None
        message_id = send_registration_notification(
            fencer_name="Test Fencer",
            tournament_name="Test Tournament",
            events="Test Event",
            source_url="https://example.com/test",
            recipients=recipients
        )
        typer.echo(f"Test email sent successfully. Message ID: {message_id}")
    except NotificationError as e:
        typer.echo(f"Failed to send test email: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1)

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    cli()
