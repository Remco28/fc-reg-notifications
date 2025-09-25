import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from ..crud import get_or_create_fencer, get_or_create_tournament, update_or_create_registration
from typing import Dict


def scrape_and_persist(db: Session, club_url: str) -> Dict[str, int]:
    """
    Scrape registration data from fencingtracker.com club URL and persist to database.

    Args:
        db: Database session
        club_url: URL to the fencing club's registration page

    Returns:
        Dictionary with counts of new, updated, and total registrations
    """
    try:
        response = requests.get(club_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch data from {club_url}: {str(e)}")

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the registration table - this may need adjustment based on actual HTML structure
    table = soup.find('table')
    if not table:
        raise Exception("No registration table found on the page")

    new_count = 0
    updated_count = 0
    total_count = 0

    # Skip header row
    rows = table.find_all('tr')[1:]

    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 4:  # Skip rows that don't have enough data
            continue

        try:
            # Extract data from table cells - adjust indices based on actual table structure
            fencer_name = cells[0].get_text(strip=True)
            tournament_name = cells[1].get_text(strip=True)
            tournament_date = cells[2].get_text(strip=True)
            events = cells[3].get_text(strip=True)

            # Skip empty rows
            if not fencer_name or not tournament_name:
                continue

            # Get or create fencer and tournament
            fencer = get_or_create_fencer(db, fencer_name)
            tournament = get_or_create_tournament(db, tournament_name, tournament_date)

            # Update or create registration
            registration, is_new = update_or_create_registration(db, fencer, tournament, events)

            if is_new:
                new_count += 1
            else:
                updated_count += 1

            total_count += 1

        except Exception as e:
            # Log the error but continue processing other rows
            print(f"Error processing row: {e}")
            continue

    db.commit()

    return {
        "new": new_count,
        "updated": updated_count,
        "total": total_count
    }