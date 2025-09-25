from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from . import models


def get_or_create_fencer(db: Session, name: str) -> models.Fencer:
    """Get an existing fencer by name or create a new one if not found."""
    fencer = db.query(models.Fencer).filter(models.Fencer.name == name).first()
    if fencer:
        return fencer

    # Fencer not found, create a new one
    fencer = models.Fencer(name=name)
    db.add(fencer)
    db.flush()  # Flush to get the ID without committing
    return fencer


def get_or_create_tournament(db: Session, name: str, date: str) -> models.Tournament:
    """Get an existing tournament by name or create a new one if not found."""
    tournament = db.query(models.Tournament).filter(models.Tournament.name == name).first()
    if tournament:
        return tournament

    # Tournament not found, create a new one
    tournament = models.Tournament(name=name, date=date)
    db.add(tournament)
    db.flush()  # Flush to get the ID without committing
    return tournament


def update_or_create_registration(db: Session, fencer: models.Fencer, tournament: models.Tournament, events: str) -> tuple[models.Registration, bool]:
    """
    Update an existing registration or create a new one.

    Returns:
        tuple[Registration, bool]: The registration object and a boolean indicating
        if it was newly created (True if new, False if it already existed).
    """
    registration = db.query(models.Registration).filter(
        models.Registration.fencer_id == fencer.id,
        models.Registration.tournament_id == tournament.id
    ).first()

    if registration:
        # Update existing registration
        registration.events = events
        registration.last_seen_at = datetime.utcnow()
        return registration, False
    else:
        # Create new registration
        registration = models.Registration(
            fencer_id=fencer.id,
            tournament_id=tournament.id,
            events=events,
            last_seen_at=datetime.utcnow()
        )
        db.add(registration)
        return registration, True
