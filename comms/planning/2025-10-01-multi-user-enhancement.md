# Multi-User Enhancement Plan
**Date:** 2025-10-01
**Status:** Planning Phase
**Context:** Expanding single-tenant notification system to multi-user platform with per-user tracking and daily digest emails.

---

## Vision & Scope

Transform the current single-tenant fencing registration notification system into a multi-user platform where each user can:
- Track specific clubs and fencers
- Receive personalized daily digest emails
- Manage their tracking preferences via web UI
- Filter notifications by weapon type

**Out of Scope:**
- AskFred integration (future consideration)
- SMS/push notifications
- Mobile apps
- Public/open registration (private beta only)

---

## Key Decisions & Constraints

### Authentication & Sessions
- **Auth Method:** Simple username/password stored in database
- **Password Security:** Use bcrypt/argon2 for hashing
- **Session Management:** Server-side sessions (simpler than JWT for this use case)

### Notification Strategy
- **Delivery:** One email per user per day at 9:00 AM (timezone TBD - system timezone for now)
- **Format:** Daily digest with two sections:
  1. New registrations from tracked clubs
  2. New registrations for tracked fencers
- **Admin Notifications:** System owner receives email when new users sign up

### Data Management
- **Fencer Identification:** Use fencingtracker.com fencer IDs (to be verified during implementation)
- **Data Retention:** Purge tournaments older than 30 days automatically
- **Per-User Settings:** Each user specifies their own notification email address

### Filtering & Preferences
- **Default:** All weapons tracked (foil, epee, saber)
- **Per-Club Filtering:** Users can specify which weapons to track for each club
- **Per-Fencer Filtering:** Users can specify which weapons to track for each fencer

---

## Phase Breakdown

### Phase 1: User Accounts & Per-User Club Tracking
**Goal:** Enable multiple users to create accounts and track their own clubs

**Deliverables:**
- User model with authentication
- Login/registration UI
- User dashboard showing tracked clubs
- UI to add/remove club tracking
- Per-user notification preferences (email address)
- Admin panel to view all users
- Admin notification on new user signup

**Data Model Changes:**
- Add `users` table (id, username, email, password_hash, is_admin, created_at)
- Add `tracked_clubs` table (id, user_id, club_url, club_name, weapon_filter, active, created_at)
- Add `user_sessions` table for session management

**Scraper Changes:**
- Continue scraping all configured clubs globally
- Link registrations to relevant users based on their tracked clubs

**Notification Changes:**
- Daily digest scheduler (runs at 9:00 AM)
- Per-user email generation
- Group notifications by club for each user
- Apply weapon filtering to notifications

### Phase 2: Fencer Profile Tracking
**Goal:** Users can track individual fencers and get notified when they register

**Prerequisites:**
- Verify fencingtracker.com has stable fencer IDs/URLs
- Determine fencer profile page structure

**Deliverables:**
- UI to search and add fencers to tracking list
- Fencer profile scraping (if needed for discovery)
- Enhanced daily digest with "Tracked Fencers" section
- Per-fencer weapon filtering

**Data Model Changes:**
- Add `tracked_fencers` table (id, user_id, fencer_id, fencer_name, weapon_filter, active, created_at)
- Possibly enhance `fencers` table with fencingtracker_id if not already present

**Notification Changes:**
- Add "Tracked Fencers" section to daily digest
- De-duplicate if a fencer appears in both club and fencer tracking sections

### Phase 3: Data Cleanup Automation
**Goal:** Automatically purge old tournament data to keep database lean

**Deliverables:**
- Scheduled cleanup job (daily at midnight?)
- Purge tournaments with date > 30 days ago
- Cascade delete associated registrations
- Logging/metrics for purged records
- Admin UI showing cleanup history

**Implementation Notes:**
- Need to parse tournament dates reliably (extract from scraped data)
- Add `tournament_date` field to tournaments table if not already accurate
- Consider keeping aggregate stats before purging (optional)

### Phase 4: Enhanced Email Templates & Polish
**Goal:** Professional email templates and UX improvements

**Deliverables:**
- HTML email templates (with plain-text fallback)
- Better email formatting (tables, links to source)
- Email preferences (time of day, frequency)
- Notification preview in web UI
- Tournament date display in UI/emails
- Weapon icons/badges in emails

---

## Data Model Summary (Post Phase 2)

### New Tables

**users**
```
id (PK)
username (UNIQUE, NOT NULL)
email (NOT NULL)
password_hash (NOT NULL)
is_admin (BOOLEAN, DEFAULT false)
created_at (DATETIME)
```

**user_sessions**
```
id (PK)
user_id (FK)
session_token (UNIQUE)
expires_at (DATETIME)
created_at (DATETIME)
```

**tracked_clubs**
```
id (PK)
user_id (FK)
club_url (NOT NULL)
club_name (TEXT)
weapon_filter (TEXT) -- JSON or comma-separated: "foil,epee,saber" or null for all
active (BOOLEAN, DEFAULT true)
created_at (DATETIME)
```

**tracked_fencers**
```
id (PK)
user_id (FK)
fencer_id (NOT NULL) -- fencingtracker.com fencer ID
fencer_name (TEXT)
weapon_filter (TEXT) -- JSON or comma-separated
active (BOOLEAN, DEFAULT true)
created_at (DATETIME)
```

### Modified Tables

**tournaments**
- Consider adding `tournament_date` (DATE) if not already reliably parsed
- Add index on `tournament_date` for cleanup queries

**fencers**
- Consider adding `fencingtracker_id` (UNIQUE) if not already present

**registrations**
- No changes needed (existing structure works)

---

## Technical Considerations

### Authentication Implementation
- Use Flask-Login or FastAPI session middleware
- Store sessions in database (not in-memory) for persistence across restarts
- Session expiry: 30 days with "remember me", 1 day without

### Scheduler Changes
- Current: Single global scrape job
- Future:
  - Global scrape jobs (unchanged)
  - Per-user digest generation job at 9:00 AM
  - Cleanup job at midnight
  - Use APScheduler's cron triggers for time-based jobs

### Email Digest Logic
```
For each user:
  1. Query tracked_clubs where active=true
  2. Query tracked_fencers where active=true
  3. Find registrations created_at > last_digest_sent (24h window)
  4. Apply weapon filters
  5. Group by club and fencer
  6. Generate email with both sections
  7. Send via Mailgun
  8. Record digest_sent_at timestamp
```

### Admin Features (Phase 1)
- View all users (username, email, signup date)
- See user tracking stats (# clubs, # fencers tracked)
- Disable/enable user accounts
- View system logs
- Manual digest trigger for testing

### Security Considerations
- HTTPS required for production
- Password requirements: min 8 chars, complexity TBD
- Rate limiting on login attempts
- CSRF protection on forms
- No password reset initially (admin can reset manually)

---

## Open Questions & Risks

### Questions to Answer During Implementation

1. **Fencer ID Discovery:** ✅ RESOLVED
   - **Fencer IDs are stable:** Format is `/p/{fencer_id}/{fencer-name-slug}`
   - **Example:** `https://fencingtracker.com/p/100349376/Jake-Mann` (ID: 100349376)
   - **Profile page structure:**
     ```html
     <section>
       <h3>Registrations</h3>
       <table>
         <thead>
           <th>Date</th>
           <th>Tournament</th>
           <th>Event Strength</th>
         </thead>
         <tbody>
           <tr>
             <td>Oct 4</td>
             <td>October NAC</td>
             <td>Division I Men's Epee (DV1ME)</td>
           </tr>
         </tbody>
       </table>
     </section>
     ```
   - **Data available:** Date, Tournament name, Event/weapon
   - **Scraping strategy:** Parse table rows, extract registrations
   - **Name changes:** Slug may change but ID remains stable

2. **Timezone Handling:**
   - Should digest time be per-user configurable?
   - Or system-wide (simpler for Phase 1)?
   - Decision: System-wide for Phase 1, per-user in Phase 4

3. **Tournament Date Parsing:**
   - How reliable is date extraction from tournament names?
   - Do we need to scrape tournament detail pages?
   - Fallback: Use last_seen_at if date unavailable

4. **Weapon Filtering Format:**
   - Store as JSON array: `["foil", "epee"]`?
   - Or comma-separated: `"foil,epee"`?
   - Decision: Comma-separated for simplicity (easier to query)

### Risks & Mitigations

**Risk:** Fencer matching is unreliable without stable IDs
- **Mitigation:** Phase 2 depends on ID verification; defer if not feasible

**Risk:** Daily digest might be overwhelming for users tracking many clubs
- **Mitigation:** Add summary counts, collapsible sections, or weekly digest option in Phase 4

**Risk:** User expectations for real-time vs daily digests
- **Mitigation:** Clear communication in UI about digest schedule

**Risk:** Data retention and database growth
- **Mitigation:** Phase 3 cleanup automation; monitor DB size

---

## Success Metrics (Post-Launch)

- Number of active users
- Average clubs/fencers tracked per user
- Email delivery success rate
- User retention (weekly active users)
- Database size trends
- Scraper success rate

---

## Next Steps

1. Review and approve this plan
2. Create detailed task specs for Phase 1
3. Update ARCHITECTURE.md with multi-user design
4. Update NEXT_STEPS.md with Phase 1 action items
5. Begin implementation

---

## Appendix: Example Daily Digest Email

```
Subject: Your Daily Fencing Registration Update

Hi [Username],

Here are the new registrations from the past 24 hours:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TRACKED CLUBS (2 new registrations)

📍 Elite Fencing Club
  • John Smith - Cadet Men's Foil
  • Jane Doe - Junior Women's Epee

View club: https://fencingtracker.com/club/100261977/...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TRACKED FENCERS (1 new registration)

🤺 Michael Chen
  • Tournament: Northeast Regional Championship
  • Events: Division 1A Men's Epee, Veteran 50+ Men's Epee

View registration: https://fencingtracker.com/...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Manage your tracking preferences:
https://your-app.com/dashboard

Questions? Reply to this email.
```

---

*Document version: 1.0*
*Last updated: 2025-10-01*
