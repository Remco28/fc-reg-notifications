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

    Note: With the corrected scraper, a fencer can have multiple registrations
    for the same tournament (one per event). The unique constraint on
    (fencer_id, tournament_id) means we need to handle this by updating
    the events field to include all events for that tournament.

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
        # If events field doesn't already contain this event, append it
        existing_events = registration.events
        if existing_events and events and events not in existing_events:
            # Append the new event to existing events (comma-separated)
            registration.events = f"{existing_events}, {events}"
        elif not existing_events:
            # No existing events, set it
            registration.events = events
        # Otherwise, event already in the list, just update timestamp

        registration.last_seen_at = datetime.utcnow()
        db.flush()
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
        try:
            db.flush()
        except IntegrityError:
            # Race condition: registration was created between our query and insert
            # Rollback and retry the query
            db.rollback()
            registration = db.query(models.Registration).filter(
                models.Registration.fencer_id == fencer.id,
                models.Registration.tournament_id == tournament.id
            ).first()
            if registration:
                # Update the existing registration instead
                existing_events = registration.events
                if existing_events and events and events not in existing_events:
                    registration.events = f"{existing_events}, {events}"
                elif not existing_events:
                    registration.events = events
                registration.last_seen_at = datetime.utcnow()
                db.flush()
                return registration, False
            else:
                # Still doesn't exist? Re-raise the error
                raise
        return registration, True
