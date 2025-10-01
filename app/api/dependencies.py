"""Shared dependencies for API routes."""

from datetime import datetime
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.services import auth_service


SESSION_COOKIE_NAME = "session_token"
templates = Jinja2Templates(directory="app/templates")


def get_templates() -> Jinja2Templates:
    """Return the shared Jinja2 template environment."""
    return templates


def get_optional_user(
    request: Request,
    session_token: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Return the authenticated user if a valid session is present."""
    user = auth_service.validate_session(db, session_token)
    if user:
        request.state.user = user
    return user


def get_current_user(
    request: Request,
    session_token: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    """Require an authenticated user."""
    user = auth_service.validate_session(db, session_token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    request.state.user = user
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require that the current user has admin privileges."""
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
