# Task Spec: Phase 1 - User Accounts & Per-User Club Tracking

**Date:** 2025-10-01
**Phase:** 1 of 4
**Status:** Ready for Implementation
**Estimated Effort:** Large (2-3 weeks)
**Context:** See `comms/planning/2025-10-01-multi-user-enhancement.md`

---

## Objective

Transform the single-tenant fencing registration notification system into a multi-user platform where users can create accounts, track their own clubs, and receive personalized daily digest emails.

---

## Success Criteria

- [ ] Users can register for an account with username/password
- [ ] Users can log in and maintain authenticated sessions
- [ ] Users can add/remove clubs to their tracking list via web UI
- [ ] Users can specify their notification email address
- [ ] Users can configure weapon filters per tracked club (foil, epee, saber, or all)
- [ ] Users receive daily digest emails at 9:00 AM with new registrations from their tracked clubs
- [ ] System admin receives email notification when new users sign up
- [ ] Admin panel allows viewing all users and their tracking stats
- [ ] Admin can disable/enable user accounts
- [ ] Existing scraper continues to work unchanged (global scraping)

---

## Out of Scope (Future Phases)

- Fencer profile tracking (Phase 2)
- Data cleanup automation (Phase 3)
- HTML email templates (Phase 4)
- Password reset functionality
- Email verification on signup
- Per-user timezone configuration
- SMS/push notifications

---

## Technical Requirements

### 1. Database Schema Changes

#### New Tables

**`users`**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**`user_sessions`**
```sql
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**`tracked_clubs`**
```sql
CREATE TABLE tracked_clubs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    club_url TEXT NOT NULL,
    club_name TEXT,
    weapon_filter TEXT,  -- Comma-separated: "foil,epee,saber" or NULL for all
    active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, club_url)
);
```

**Implementation Notes:**
- Add migration script or update `init_db()` in `app/database.py`
- Use SQLAlchemy models in `app/models.py`
- Ensure indexes on foreign keys for performance

---

### 2. Authentication System

#### Requirements

**Password Security:**
- Use `bcrypt` for password hashing (install via `pip install bcrypt`)
- Minimum password length: 8 characters
- No complexity requirements initially (can add in Phase 4)

**Session Management:**
- Server-side sessions stored in `user_sessions` table
- Session token: 32-byte random hex string (use `secrets.token_hex(32)`)
- Session expiry: 30 days
- Cookie-based session tracking (HTTP-only, secure in production)

**Implementation:**
- Create `app/services/auth_service.py` with functions:
  - `register_user(username, email, password) -> User`
  - `authenticate(username, password) -> User | None`
  - `create_session(user_id) -> session_token`
  - `validate_session(session_token) -> User | None`
  - `logout(session_token) -> None`
- Add password hashing utilities:
  - `hash_password(password) -> str`
  - `verify_password(password, password_hash) -> bool`

**Security Considerations:**
- No rate limiting initially (can add in Phase 4)
- Sessions stored in DB (survive app restarts)
- Include CSRF protection on forms (use FastAPI form utilities)

---

### 3. Web UI - Authentication Pages

Create new HTML templates in `templates/`:

#### `templates/register.html`
- Registration form with fields:
  - Username (required, unique)
  - Email (required)
  - Password (required, min 8 chars)
  - Confirm Password (client-side validation)
- Submit button → POST to `/auth/register`
- Link to login page
- Display validation errors

#### `templates/login.html`
- Login form with fields:
  - Username (required)
  - Password (required)
- Submit button → POST to `/auth/login`
- Link to registration page
- Display authentication errors

#### `templates/layout.html` (Update existing or create)
- Add navigation bar with:
  - If logged in: "Dashboard", "Tracked Clubs", "Admin" (if admin), "Logout"
  - If not logged in: "Login", "Register"
- Include CSRF token handling
- Flash message support for success/error notifications

---

### 4. Web UI - User Dashboard

#### `templates/dashboard.html`
- Display welcome message: "Welcome, {username}!"
- Show user's notification email address
- Button to "Manage Tracked Clubs"
- Stats section:
  - Number of tracked clubs
  - Total registrations monitored today (optional for Phase 1)
- Link to admin panel (if `is_admin`)

---

### 5. Web UI - Club Tracking Management

#### `templates/tracked_clubs.html`
- **Add Club Section:**
  - Form with fields:
    - Club URL (required, fencingtracker.com URL)
    - Club Name (auto-populated after scraping, or manual entry)
    - Weapon Filter (checkboxes: Foil, Epee, Saber, or "All")
  - Submit button → POST to `/clubs/add`

- **Tracked Clubs List:**
  - Table showing:
    - Club Name
    - Club URL (link)
    - Weapon Filter (display as badges/tags)
    - Status (Active/Inactive)
    - Actions: "Edit", "Remove"
  - Edit button → Opens modal or inline form to update weapon filter
  - Remove button → Soft delete (set `active=0`)

**Implementation Notes:**
- Validate club URL format (must be fencingtracker.com)
- Scrape club name from URL when adding (optional: use existing scraper to preview)
- Store weapon filter as comma-separated string: `"foil,epee"` or `NULL` for all

---

### 6. Web UI - Admin Panel

#### `templates/admin/users.html`
- **Access Control:** Only accessible to users with `is_admin=1`
- **User List Table:**
  - Columns: Username, Email, Signup Date, # Tracked Clubs, Status, Actions
  - Actions: "Disable"/"Enable", "View Details"
- **User Details View (optional for Phase 1):**
  - Show user's tracked clubs
  - Activity log (can be deferred to Phase 4)

**Implementation Notes:**
- Add route guard to check `is_admin` before rendering
- Admin status set manually in database initially (no UI to promote users)

---

### 7. API Endpoints

Add new routes in `app/api/endpoints.py` or create `app/api/auth.py`, `app/api/clubs.py`:

#### Authentication Routes

```python
POST   /auth/register
  Body: { username, email, password }
  Returns: Redirect to /login with success message

POST   /auth/login
  Body: { username, password }
  Returns: Set session cookie, redirect to /dashboard

POST   /auth/logout
  Returns: Clear session cookie, redirect to /login

GET    /auth/me
  Returns: Current user info (for frontend state)
```

#### Club Tracking Routes

```python
GET    /clubs
  Returns: List of tracked clubs for current user

POST   /clubs/add
  Body: { club_url, club_name?, weapon_filter? }
  Returns: Created tracked_club object

PATCH  /clubs/{id}
  Body: { weapon_filter?, active? }
  Returns: Updated tracked_club object

DELETE /clubs/{id}
  Returns: 204 No Content (soft delete, set active=0)
```

#### Admin Routes

```python
GET    /admin/users
  Returns: List of all users with stats (admin only)

PATCH  /admin/users/{id}
  Body: { is_admin?, active? }
  Returns: Updated user object (admin only)
```

#### User Dashboard Route

```python
GET    /dashboard
  Returns: Render dashboard.html with user stats
```

**Implementation Notes:**
- Use FastAPI dependency injection for authentication:
  ```python
  def get_current_user(session_token: str = Cookie(None)) -> User:
      # Validate session, return user or raise 401
  ```
- Add dependency for admin check:
  ```python
  def require_admin(user: User = Depends(get_current_user)) -> User:
      if not user.is_admin:
          raise HTTPException(status_code=403, detail="Admin access required")
      return user
  ```

---

### 8. Notification System Changes

#### Daily Digest Scheduler

**New Scheduled Job:**
- Trigger: Daily at 9:00 AM (system timezone)
- Function: `send_daily_digests()`
- Uses APScheduler cron trigger

**Implementation:**
```python
# In app/main.py or new app/services/digest_service.py

def send_daily_digests():
    """Send daily digest emails to all active users."""
    db = SessionLocal()
    try:
        users = crud.get_active_users(db)  # is_admin can receive digests too
        for user in users:
            try:
                send_user_digest(db, user)
            except Exception as e:
                logger.error(f"Failed to send digest to user {user.id}: {e}")
    finally:
        db.close()

def send_user_digest(db: Session, user: User):
    """Generate and send digest for a single user."""
    # 1. Get user's tracked clubs
    tracked_clubs = crud.get_tracked_clubs(db, user.id, active=True)

    # 2. Find registrations created in last 24 hours
    since = datetime.utcnow() - timedelta(hours=24)
    new_registrations = []

    for tracked_club in tracked_clubs:
        # Get registrations from this club
        registrations = crud.get_registrations_by_club_url(
            db,
            tracked_club.club_url,
            since=since
        )

        # Apply weapon filter
        filtered = apply_weapon_filter(registrations, tracked_club.weapon_filter)
        new_registrations.extend(filtered)

    # 3. If no new registrations, skip email (optional: send anyway with "No new registrations")
    if not new_registrations:
        logger.info(f"No new registrations for user {user.id}, skipping digest")
        return

    # 4. Generate email content
    subject = f"Your Daily Fencing Registration Update ({len(new_registrations)} new)"
    body = format_digest_email(user, new_registrations)

    # 5. Send via Mailgun
    send_registration_notification(
        fencer_name="",  # Not applicable for digest
        tournament_name="",
        events="",
        source_url="",
        recipients=[user.email],
        subject=subject,
        body=body
    )

    logger.info(f"Sent digest to user {user.id} ({user.email}) with {len(new_registrations)} registrations")
```

**Helper Functions:**

```python
def apply_weapon_filter(registrations: List[Registration], weapon_filter: str) -> List[Registration]:
    """Filter registrations by weapon type."""
    if not weapon_filter:  # NULL means all weapons
        return registrations

    allowed_weapons = weapon_filter.lower().split(',')
    filtered = []

    for reg in registrations:
        # Parse weapon from events string (e.g., "Cadet Men's Foil" contains "foil")
        event_lower = reg.events.lower()
        if any(weapon in event_lower for weapon in allowed_weapons):
            filtered.append(reg)

    return filtered

def format_digest_email(user: User, registrations: List[Registration]) -> str:
    """Format plain-text digest email."""
    lines = [
        f"Hi {user.username},",
        "",
        f"Here are the {len(registrations)} new registrations from the past 24 hours:",
        "",
        "─" * 60,
        "TRACKED CLUBS",
        "─" * 60,
        ""
    ]

    # Group by club
    by_club = {}
    for reg in registrations:
        club_url = reg.source_url  # Assuming source_url points to club page
        if club_url not in by_club:
            by_club[club_url] = []
        by_club[club_url].append(reg)

    for club_url, club_regs in by_club.items():
        # Get club name from tracked_clubs or tournament name
        club_name = club_regs[0].tournament.name  # Fallback
        lines.append(f"📍 {club_name}")

        for reg in club_regs:
            lines.append(f"  • {reg.fencer.name} - {reg.events}")

        lines.append(f"\nView club: {club_url}")
        lines.append("")

    lines.extend([
        "─" * 60,
        "",
        "Manage your tracking preferences:",
        "https://your-app.com/clubs",
        "",
        "Questions? Reply to this email."
    ])

    return "\n".join(lines)
```

**Scheduler Setup (in `app/main.py`):**

```python
def start_digest_scheduler():
    """Start the daily digest scheduler (separate from scrape scheduler)."""
    scheduler = BlockingScheduler()

    # Daily digest at 9:00 AM
    scheduler.add_job(
        send_daily_digests,
        'cron',
        hour=9,
        minute=0,
        id='daily_digest'
    )

    logger.info("Daily digest scheduler started (9:00 AM)")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Digest scheduler stopped")

# Add CLI command to run digest scheduler
@cli.command("digest-scheduler")
def run_digest_scheduler():
    """Start the daily digest scheduler."""
    init_db()
    start_digest_scheduler()
```

---

#### Admin New User Notification

**Implementation:**
```python
# In app/services/auth_service.py

def register_user(username: str, email: str, password: str, db: Session) -> User:
    """Register a new user and notify admin."""
    # Validate inputs
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    # Check if username exists
    existing = crud.get_user_by_username(db, username)
    if existing:
        raise ValueError("Username already exists")

    # Create user
    password_hash = hash_password(password)
    user = crud.create_user(db, username, email, password_hash)

    # Send admin notification
    try:
        notify_admin_new_user(user)
    except Exception as e:
        logger.error(f"Failed to send admin notification for new user {user.id}: {e}")
        # Don't fail registration if notification fails

    return user

def notify_admin_new_user(user: User):
    """Send email to admin about new user signup."""
    admin_email = os.getenv("ADMIN_EMAIL") or os.getenv("MAILGUN_DEFAULT_RECIPIENTS").split(',')[0]

    subject = f"New user signup: {user.username}"
    body = f"""A new user has signed up for the fencing registration tracker.

Username: {user.username}
Email: {user.email}
Signup Date: {user.created_at}

View in admin panel: https://your-app.com/admin/users
"""

    send_registration_notification(
        fencer_name="",
        tournament_name="",
        events="",
        source_url="",
        recipients=[admin_email],
        subject=subject,
        body=body
    )
```

**Environment Variable:**
- Add `ADMIN_EMAIL` to `.env.example` (optional, defaults to first recipient in `MAILGUN_DEFAULT_RECIPIENTS`)

---

### 9. CRUD Operations

Add new functions to `app/crud.py`:

#### User Operations
```python
def create_user(db: Session, username: str, email: str, password_hash: str) -> User:
    """Create a new user."""

def get_user_by_username(db: Session, username: str) -> User | None:
    """Get user by username."""

def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Get user by ID."""

def get_active_users(db: Session) -> List[User]:
    """Get all active users (for digest sending)."""

def update_user(db: Session, user_id: int, **kwargs) -> User:
    """Update user fields (is_admin, etc.)."""
```

#### Session Operations
```python
def create_session(db: Session, user_id: int, session_token: str, expires_at: datetime) -> UserSession:
    """Create a new session."""

def get_session(db: Session, session_token: str) -> UserSession | None:
    """Get session by token."""

def delete_session(db: Session, session_token: str) -> None:
    """Delete session (logout)."""

def cleanup_expired_sessions(db: Session) -> int:
    """Delete expired sessions, return count deleted."""
```

#### Tracked Club Operations
```python
def create_tracked_club(db: Session, user_id: int, club_url: str, club_name: str = None, weapon_filter: str = None) -> TrackedClub:
    """Add a club to user's tracking list."""

def get_tracked_clubs(db: Session, user_id: int, active: bool = None) -> List[TrackedClub]:
    """Get all tracked clubs for a user."""

def update_tracked_club(db: Session, tracked_club_id: int, **kwargs) -> TrackedClub:
    """Update tracked club (weapon_filter, active, etc.)."""

def delete_tracked_club(db: Session, tracked_club_id: int) -> None:
    """Soft delete tracked club (set active=False)."""
```

#### Registration Queries for Digest
```python
def get_registrations_by_club_url(db: Session, club_url: str, since: datetime = None) -> List[Registration]:
    """Get registrations from a specific club URL, optionally filtered by date."""
    # Note: Requires storing club_url in registrations or tournaments
    # May need to add source_url field to tournaments table
```

---

### 10. Configuration Updates

#### Environment Variables (`.env.example`)
```bash
# Existing Mailgun credentials
MAILGUN_API_KEY=key-1234567890abcdef1234567890abcdef
MAILGUN_DOMAIN=mg.example.com
MAILGUN_SENDER=notifications@example.com
MAILGUN_DEFAULT_RECIPIENTS=admin@example.com,alerts@example.com

# Admin notifications
ADMIN_EMAIL=admin@example.com

# Scraper scheduling
SCRAPER_CLUB_URLS=https://fencingtracker.com/club/123/Example%20Club/registrations
SCRAPER_INTERVAL_MINUTES=720

# Session security (optional, defaults to secrets.token_hex)
SECRET_KEY=your-secret-key-for-session-signing
```

#### Requirements (`requirements.txt`)
Add new dependencies:
```
bcrypt>=4.0.1
```

---

### 11. Database Migration Strategy

Since this is early development with likely no production data:

**Option A: Destructive (Recommended for Phase 1)**
- Update `app/database.py` `init_db()` to create new tables
- Document that existing DB should be backed up or recreated
- Add comment in code about future Alembic migration

**Option B: Alembic Migration (More robust)**
- Install Alembic: `pip install alembic`
- Initialize Alembic: `alembic init alembic`
- Create migration script for new tables
- Document migration commands in README

**Recommendation:** Use Option A for Phase 1 since there's no production data. Plan to introduce Alembic before Phase 2.

---

### 12. Testing Requirements

Create tests in `tests/`:

#### Unit Tests
- `tests/test_auth_service.py`:
  - Test password hashing/verification
  - Test user registration validation
  - Test session creation/validation

- `tests/test_crud_users.py`:
  - Test user CRUD operations
  - Test tracked_clubs CRUD operations

- `tests/test_weapon_filter.py`:
  - Test weapon filtering logic
  - Test filter parsing (comma-separated)

#### Integration Tests
- `tests/test_auth_endpoints.py`:
  - Test registration flow
  - Test login/logout
  - Test session persistence

- `tests/test_club_tracking.py`:
  - Test adding/removing clubs
  - Test weapon filter updates

- `tests/test_digest_generation.py`:
  - Test daily digest content generation
  - Test weapon filtering in digest
  - Mock Mailgun client

**Note:** Existing scraper tests should continue to pass unchanged.

---

## Implementation Checklist

### Database & Models
- [ ] Add new SQLAlchemy models to `app/models.py` (User, UserSession, TrackedClub)
- [ ] Update `app/database.py` to create new tables in `init_db()`
- [ ] Add CRUD operations to `app/crud.py`
- [ ] Test database schema with sample data

### Authentication Service
- [ ] Install `bcrypt` dependency
- [ ] Create `app/services/auth_service.py`
- [ ] Implement password hashing utilities
- [ ] Implement user registration logic
- [ ] Implement session management
- [ ] Add admin notification on signup

### API Endpoints
- [ ] Create `app/api/auth.py` for auth routes
- [ ] Create `app/api/clubs.py` for club tracking routes
- [ ] Create `app/api/admin.py` for admin routes
- [ ] Add authentication dependency (`get_current_user`)
- [ ] Add admin authorization dependency (`require_admin`)
- [ ] Update `app/main.py` to include new routers

### Web UI - Templates
- [ ] Update/create `templates/layout.html` with navigation
- [ ] Create `templates/register.html`
- [ ] Create `templates/login.html`
- [ ] Create `templates/dashboard.html`
- [ ] Create `templates/tracked_clubs.html`
- [ ] Create `templates/admin/users.html`
- [ ] Add CSS styling (use existing or add Bootstrap/Tailwind)

### Notification System
- [ ] Create `app/services/digest_service.py`
- [ ] Implement `send_daily_digests()` function
- [ ] Implement `format_digest_email()` function
- [ ] Implement weapon filtering logic
- [ ] Add digest scheduler to `app/main.py`
- [ ] Add CLI command `digest-scheduler`
- [ ] Update `notification_service.py` to support custom subject/body (if needed)

### Configuration
- [ ] Update `.env.example` with new variables
- [ ] Update `README.md` with new setup instructions
- [ ] Document digest scheduler usage

### Testing
- [ ] Write unit tests for auth service
- [ ] Write unit tests for CRUD operations
- [ ] Write integration tests for endpoints
- [ ] Write tests for digest generation
- [ ] Ensure existing scraper tests still pass

### Documentation
- [ ] Update `docs/ARCHITECTURE.md` with new components
- [ ] Update `NEXT_STEPS.md` to mark Phase 1 complete and outline Phase 2
- [ ] Add user guide section to `README.md`

---

## Acceptance Testing Scenarios

### Scenario 1: User Registration & Login
1. Visit `/register`
2. Register with username "testuser", email "test@example.com", password "password123"
3. Verify admin receives notification email
4. Log in at `/login` with credentials
5. Verify redirect to `/dashboard`
6. Verify navigation shows "Logout" link

### Scenario 2: Club Tracking
1. Log in as test user
2. Navigate to `/clubs`
3. Add club URL: `https://fencingtracker.com/club/100261977/Elite%20FC/registrations`
4. Set weapon filter: "foil,epee"
5. Verify club appears in tracked list
6. Edit club to change filter to "all weapons"
7. Verify update persisted
8. Remove club
9. Verify club marked as inactive

### Scenario 3: Daily Digest
1. Log in as test user
2. Track a club with known recent registrations
3. Manually trigger digest: `python -m app.main send-user-digest {user_id}` (add this CLI command for testing)
4. Verify email received at user's email address
5. Verify only foil/epee registrations included (per weapon filter)
6. Verify email format matches spec

### Scenario 4: Admin Panel
1. Log in as admin user (set `is_admin=1` in DB manually)
2. Navigate to `/admin/users`
3. Verify all users listed with stats
4. Disable a user account
5. Verify disabled user cannot log in
6. Re-enable user account

### Scenario 5: Session Persistence
1. Log in as test user
2. Close browser
3. Reopen browser and visit `/dashboard`
4. Verify still logged in (session persisted)

---

## Deployment Notes

### Running in Production (Phase 1)

**Required Processes:**
1. **FastAPI Web App:** `uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. **Scraper Scheduler:** `python -m app.main schedule` (existing)
3. **Digest Scheduler:** `python -m app.main digest-scheduler` (new)

**Process Management:**
- Use `systemd`, `supervisord`, or `pm2` to manage three processes
- Consider combining schedulers into one process (optional optimization)

**Database:**
- SQLite file location: `fc_registration.db`
- Ensure write permissions for all processes
- Consider SQLite WAL mode for concurrent access

**Security Checklist:**
- [ ] Use HTTPS in production
- [ ] Set secure cookie flags (`secure=True, httponly=True`)
- [ ] Configure CORS if needed
- [ ] Review Mailgun API key permissions

---

## Known Limitations & Future Work

**Phase 1 Limitations:**
- No password reset (admin must reset manually)
- No email verification on signup
- No rate limiting on login
- No per-user timezone for digest
- Plain-text emails only (HTML in Phase 4)
- No fencer tracking (Phase 2)
- No automatic data cleanup (Phase 3)

**Deferred to Future Phases:**
- Fencer profile tracking (Phase 2)
- Automated tournament cleanup (Phase 3)
- HTML email templates (Phase 4)
- User activity logs (Phase 4)
- Email preferences (Phase 4)

---

## Questions for Product Owner

Before implementation, please confirm:

1. **Admin account setup:** How should the first admin account be created?
   - Option A: Manual INSERT into database
   - Option B: CLI command `python -m app.main create-admin`
   - **Recommendation:** Option B

2. **Digest when no new registrations:** Should users receive an email saying "No new registrations" or skip entirely?
   - **Recommendation:** Skip email if no new registrations

3. **Club URL validation:** Should we validate the club URL by attempting to scrape it when user adds it?
   - **Recommendation:** Yes, validate URL format and attempt to fetch club name

4. **Weapon filter UI:** Checkboxes or dropdown?
   - **Recommendation:** Checkboxes with "All" option

5. **Session expiry:** 30 days fixed or should it be configurable?
   - **Recommendation:** Fixed 30 days for Phase 1

---

## Reference Links

- **Planning Doc:** `comms/planning/2025-10-01-multi-user-enhancement.md`
- **Architecture:** `docs/ARCHITECTURE.md`
- **Existing Scraper:** `app/services/scraper_service.py`
- **Existing Notification Service:** `app/services/notification_service.py`

---

*Spec Version: 1.0*
*Author: Tech Advisor*
*Approved By: [Pending]*
