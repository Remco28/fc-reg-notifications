# Project: Fencing Club Registration Notifications

## High-Level Goal

Create a tool to track tournament registrations for members of a fencing club and send notifications about them.

## Architecture & Technology

### High-Level Architecture
1.  **Scraper Service:** A module with "connectors" for each data source (`fencingtracker.com`, `askfred.net`) to fetch registration data.
2.  **Database:** A relational database to store clubs, fencers, tournaments, and registrations to track changes.
3.  **Notification Service:** An email service to send alerts about new registrations.
4.  **Scheduler:** A job scheduler to run the scraper service periodically.
5.  **Web Application:** A simple web interface for viewing the collected data.

### Technology Stack
- **Backend Language:** Python
- **Web Framework & API:** FastAPI
- **Database:** SQLite with the SQLAlchemy ORM
- **Web Scraping:** Requests & BeautifulSoup
- **Job Scheduling:** APScheduler
- **Frontend:** Basic HTML, CSS, and JavaScript

## Initial Discovery

### Q1: Data Source
- **A:** Public data from `fencingtracker.com` and `askfred.net`. No API is available, so web scraping will be necessary. No credentials will be used.

### Q2: Users
- **A:** Club managers and fencers. They want to see who is attending which tournaments.

### Q3: Information Scope
- **A:** Fencer's name, tournament name, tournament date, and specific event (e.g., Y12, Cadet, Junior).

### Q4: Notification Trigger
- **A:** A new registration detected for an upcoming tournament. This implies a database is needed to track known registrations.

### Q5: Notification Method
- **A:** Email seems to be the preferred method.
