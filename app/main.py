import typer
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .database import init_db, get_db
from .services import scraper_service

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

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    cli()
