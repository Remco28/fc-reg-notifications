from types import SimpleNamespace
from unittest.mock import patch

from app import crud
from app.services import auth_service, digest_service


def test_apply_weapon_filter_returns_matching_events():
    registrations = [
        SimpleNamespace(events="Junior Women's Foil"),
        SimpleNamespace(events="Cadet Men's Saber"),
    ]

    filtered = digest_service.apply_weapon_filter(registrations, "foil")

    assert len(filtered) == 1
    assert filtered[0].events == "Junior Women's Foil"


def test_send_user_digest_skips_when_no_registrations(db_session):
    password_hash = auth_service.hash_password("password123")
    user = crud.create_user(db_session, "tester", "tester@example.com", password_hash)
    crud.create_tracked_club(
        db_session,
        user_id=user.id,
        club_url="https://fencingtracker.com/club/1/Example/registrations",
        club_name="Example Club",
    )
    db_session.commit()

    with patch("app.services.digest_service.send_registration_notification") as mock_send:
        sent = digest_service.send_user_digest(db_session, user)

    assert sent is False
    mock_send.assert_not_called()


def test_send_user_digest_sends_email(db_session):
    password_hash = auth_service.hash_password("password123")
    user = crud.create_user(db_session, "digest", "digest@example.com", password_hash)
    tracked = crud.create_tracked_club(
        db_session,
        user_id=user.id,
        club_url="https://fencingtracker.com/club/2/Elite/registrations",
        club_name="Elite FC",
        weapon_filter="foil",
    )

    fencer = crud.get_or_create_fencer(db_session, "Jane Doe")
    tournament = crud.get_or_create_tournament(db_session, "Autumn Open", "2025-10-01")
    crud.update_or_create_registration(
        db_session,
        fencer,
        tournament,
        events="Junior Women's Foil",
        club_url=tracked.club_url,
    )
    db_session.commit()

    with patch("app.services.digest_service.send_registration_notification") as mock_send:
        sent = digest_service.send_user_digest(db_session, user)

    assert sent is True
    mock_send.assert_called_once()
    args, kwargs = mock_send.call_args
    assert kwargs["recipients"] == [user.email]
