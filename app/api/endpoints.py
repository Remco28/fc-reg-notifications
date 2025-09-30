"""
API endpoints for the Fencing Club Registration Notifications system.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.registration_query_service import query_registrations


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def get_registrations_page(
    request: Request,
    tournament: Optional[str] = None,
    fencer: Optional[str] = None,
    sort_by: str = "last_seen_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    """
    Main UI landing page showing all registrations with filtering and sorting.

    Query Parameters:
        tournament: Filter by tournament name (case-insensitive substring match)
        fencer: Filter by fencer name (case-insensitive substring match)
        sort_by: Sort field (fencer_name, tournament_name, last_seen_at)
        sort_order: Sort order (asc or desc)

    Returns:
        Rendered HTML page
    """
    try:
        registrations = query_registrations(
            db=db,
            tournament_filter=tournament,
            fencer_filter=fencer,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return templates.TemplateResponse(
            "registrations.html",
            {
                "request": request,
                "registrations": registrations,
                "tournament_filter": tournament,
                "fencer_filter": fencer,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        )
    except Exception as e:
        # Return a simple error page if database connection fails
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head><title>Error</title></head>
            <body>
                <h1>Error Loading Registrations</h1>
                <p>Unable to load registrations from the database.</p>
                <p>Error: {str(e)}</p>
            </body>
            </html>
            """,
            status_code=500
        )


@router.get("/registrations/json")
def get_registrations_json(
    tournament: Optional[str] = None,
    fencer: Optional[str] = None,
    sort_by: str = "last_seen_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    JSON API endpoint for programmatic access to registrations.

    Query Parameters:
        tournament: Filter by tournament name (case-insensitive substring match)
        fencer: Filter by fencer name (case-insensitive substring match)
        sort_by: Sort field (fencer_name, tournament_name, last_seen_at)
        sort_order: Sort order (asc or desc)

    Returns:
        JSON array of registration objects
    """
    registrations = query_registrations(
        db=db,
        tournament_filter=tournament,
        fencer_filter=fencer,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return registrations