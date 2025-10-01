"""General application routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.models import User

from .dependencies import get_current_user, get_optional_user, templates


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    user: Optional[User] = Depends(get_optional_user),
):
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tracked_clubs = crud.get_tracked_clubs(db, user.id, active=True)
    inactive_clubs = crud.get_tracked_clubs(db, user.id, active=False)

    context = {
        "request": request,
        "user": user,
        "tracked_club_count": len(tracked_clubs),
        "inactive_club_count": len(inactive_clubs),
    }

    return templates.TemplateResponse("dashboard.html", context)
