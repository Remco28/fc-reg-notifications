# Technical Specification: Security Hardening & Technical Debt Cleanup
**Date:** 2025-10-03
**Author:** Architect
**Status:** SPEC READY
**Priority:** High (Pre-Production Hardening)

---

## Context

Phase 2 is complete and production-ready, but infrastructure is still being set up. This window provides an opportunity to address accumulated technical debt and strengthen security posture before real users arrive.

The Phase 1 code review (comms/tasks/2025-10-01-phase1-code-review.md) identified several non-blocking improvements. This spec prioritizes security hardening items that are critical for production readiness and quick-win technical debt fixes.

---

## Objectives

1. **Add CSRF protection** to all state-changing forms (defense-in-depth alongside SameSite cookies)
2. **Implement rate limiting** on authentication endpoints to prevent brute-force attacks
3. **Fix deprecation warnings** by replacing `datetime.utcnow()` with `datetime.now(datetime.UTC)`
4. **Improve security feedback** by adding better error messages and lockout behavior

---

## Deliverables

### 1. CSRF Token Protection

**Goal:** Prevent Cross-Site Request Forgery attacks on all state-changing endpoints.

**Implementation Requirements:**

#### 1.1 CSRF Token Generation & Validation Service
**File:** `app/services/csrf_service.py` (new file)

**Functions:**
- `generate_csrf_token() -> str`
  - Generate a cryptographically secure random token (32 bytes, hex-encoded)
  - Return the token string

- `validate_csrf_token(session_token: str, provided_csrf_token: str, db: Session) -> bool`
  - Look up the user session by session_token
  - Compare provided_csrf_token against session.csrf_token (constant-time comparison)
  - Return True if valid, False otherwise

**Storage Strategy:**
- Store CSRF token in the `user_sessions` table (requires new column)
- Generate CSRF token when session is created
- Rotate CSRF token on successful login (generate new token)

#### 1.2 Database Schema Migration
**Migration:** `migrations/versions/YYYYMMDD_add_csrf_token_to_sessions.py`

**Changes:**
- Add `csrf_token` column to `user_sessions` table (String, nullable=True for backward compatibility)
- Backfill existing sessions with generated tokens in migration

**Model Update:**
- Add `csrf_token: str` field to `UserSession` model in `app/models.py`

#### 1.3 Middleware for CSRF Validation
**File:** `app/api/dependencies.py` (update existing)

**New Dependency Function:**
```python
def validate_csrf(
    request: Request,
    session_token: str = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db)
) -> None:
```

**Behavior:**
- Extract CSRF token from request:
  - For HTML forms: Check form field `csrf_token`
  - For JSON requests: Check header `X-CSRF-Token`
- If token missing or invalid: raise HTTPException(403, "Invalid CSRF token")
- If valid: return None (dependency succeeds)

**Exempt Endpoints:**
- GET requests (read-only, no CSRF needed)
- `/auth/login` and `/auth/register` (no existing session yet - use alternative protection)

#### 1.4 Template Helper for CSRF Tokens
**File:** `app/api/dependencies.py` (update existing)

**New Template Context Function:**
- Update `templates.env.globals` to include a `csrf_token` helper
- Helper retrieves CSRF token from current user session (via optional_user dependency)
- Returns empty string if no session exists

**Template Updates:**
All state-changing forms must include hidden CSRF input:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

**Files to Update:**
- `app/templates/register.html` - Add CSRF field to registration form (use alternative: honeypot or timing checks)
- `app/templates/login.html` - Add CSRF field to login form (use alternative: rate limiting only)
- `app/templates/tracked_clubs.html` - Add CSRF field to add club form
- `app/templates/tracked_fencers.html` - Add CSRF field to add/edit/delete fencer forms
- `app/templates/admin/users.html` - Add CSRF field if forms present

**Note on Login/Register:**
Since these endpoints don't have existing sessions, use a different CSRF strategy:
- **Option A:** Generate anonymous CSRF tokens stored in a separate cache/table with short TTL
- **Option B:** Skip CSRF for login/register, rely on rate limiting alone (simpler, acceptable for private beta)

**Decision:** Use Option B for simplicity. Document as technical debt for future enhancement.

#### 1.5 Route Protection
**Files to Update:**
- `app/api/auth.py` - Add `validate_csrf` dependency to `POST /auth/logout`
- `app/api/clubs.py` - Add `validate_csrf` dependency to:
  - `POST /clubs/add`
  - `PATCH /clubs/{id}`
  - `DELETE /clubs/{id}`
- `app/api/tracked_fencers.py` - Add `validate_csrf` dependency to all POST/PATCH/DELETE endpoints
- `app/api/admin.py` - Add `validate_csrf` dependency to `PATCH /admin/users/{id}`

**Example Usage:**
```python
@router.post("/clubs/add")
async def add_tracked_club(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _csrf: None = Depends(validate_csrf),  # Add this line
):
    # ... existing implementation
```

---

### 2. Rate Limiting on Authentication Endpoints

**Goal:** Prevent brute-force attacks on login and registration endpoints.

**Implementation Requirements:**

#### 2.1 Rate Limiting Service
**File:** `app/services/rate_limit_service.py` (new file)

**Strategy:** In-memory rate limiting with sliding window (acceptable for single-process deployment)

**Functions:**
- `check_rate_limit(key: str, max_attempts: int, window_seconds: int) -> tuple[bool, int]`
  - Track attempts for a given key (e.g., "login:username" or "register:ip")
  - Return (is_allowed: bool, remaining_attempts: int)
  - Use a sliding window algorithm with in-memory storage (dict with timestamps)

- `reset_rate_limit(key: str) -> None`
  - Clear rate limit for a key (call on successful login)

**Configuration (Environment Variables):**
- `LOGIN_RATE_LIMIT_ATTEMPTS` - Default: 5 attempts
- `LOGIN_RATE_LIMIT_WINDOW_SEC` - Default: 300 (5 minutes)
- `REGISTER_RATE_LIMIT_ATTEMPTS` - Default: 3 attempts
- `REGISTER_RATE_LIMIT_WINDOW_SEC` - Default: 3600 (1 hour)

**Storage:**
```python
# In-memory structure (module-level)
_rate_limits: Dict[str, List[float]] = {}  # key -> list of attempt timestamps
```

**Cleanup:**
- Implement periodic cleanup of expired entries (remove timestamps older than window)
- Run cleanup on each check_rate_limit call (lazy cleanup)

#### 2.2 Rate Limiting Dependency
**File:** `app/api/dependencies.py` (update existing)

**New Dependency Functions:**
```python
def check_login_rate_limit(request: Request) -> None:
    # Extract username from form/JSON (requires request body inspection)
    # Check rate limit for f"login:{username}"
    # If exceeded, raise HTTPException(429, "Too many login attempts. Try again later.")

def check_register_rate_limit(request: Request) -> None:
    # Use IP address for registration rate limiting
    # Check rate limit for f"register:{client_ip}"
    # If exceeded, raise HTTPException(429, "Too many registration attempts. Try again later.")
```

**Client IP Extraction:**
- Use `request.client.host` for IP address
- Consider `X-Forwarded-For` header if behind proxy (document in ARCHITECTURE.md)

#### 2.3 Route Integration
**File:** `app/api/auth.py`

**Updates:**
- Add `check_login_rate_limit` dependency to `POST /auth/login` (before authentication check)
- Add `check_register_rate_limit` dependency to `POST /auth/register` (before validation)
- On successful login: call `reset_rate_limit(f"login:{username}")`

**Error Handling:**
- Return 429 status code with Retry-After header (seconds until window expires)
- For HTML requests: render login/register template with rate limit error message
- For JSON requests: return `{"detail": "Too many attempts. Try again in X seconds."}`

---

### 3. Fix datetime.utcnow() Deprecation Warnings

**Goal:** Replace all instances of `datetime.utcnow()` with `datetime.now(datetime.UTC)` to resolve Python 3.12 deprecation warnings.

**Files to Update:**
Based on grep results, update these files:
- `app/crud.py`
- `app/main.py`
- `app/services/auth_service.py`
- `app/services/digest_service.py`
- `app/services/fencer_scraper_service.py`
- `app/api/tracked_fencers.py`
- All test files (grep matched):
  - `tests/test_auth_service.py`
  - `tests/test_crud_tracked_fencers.py`
  - `tests/test_tracked_fencer_routes.py`
  - `tests/services/test_fencer_scraper_service.py`

**Replacement Pattern:**
```python
# OLD (deprecated):
from datetime import datetime
now = datetime.utcnow()

# NEW (Python 3.12+):
from datetime import datetime, UTC
now = datetime.now(UTC)
```

**Testing:**
- Run full test suite (`pytest`) to verify no breakage
- Confirm deprecation warnings are eliminated

---

### 4. Configuration Updates

#### 4.1 Environment Variables Documentation
**File:** `.env.example`

Add new variables:
```bash
# Rate Limiting
LOGIN_RATE_LIMIT_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW_SEC=300
REGISTER_RATE_LIMIT_ATTEMPTS=3
REGISTER_RATE_LIMIT_WINDOW_SEC=3600
```

#### 4.2 README Updates
**File:** `README.md`

Add section under "Configuration" or "Security":
- Document CSRF token behavior
- Document rate limiting settings
- Note that rate limiting is in-memory (resets on process restart)
- Recommend external rate limiting (nginx, Cloudflare) for production

---

### 5. Testing Requirements

#### 5.1 CSRF Tests
**File:** `tests/test_csrf_protection.py` (new file)

**Test Cases:**
1. `test_csrf_token_generated_on_session_creation` - Verify new sessions have CSRF tokens
2. `test_csrf_token_validation_success` - Valid token allows request
3. `test_csrf_token_validation_failure_missing` - Missing token returns 403
4. `test_csrf_token_validation_failure_invalid` - Wrong token returns 403
5. `test_csrf_token_in_template_context` - Template helper returns correct token
6. `test_logout_requires_csrf_token` - Logout endpoint validates CSRF
7. `test_club_add_requires_csrf_token` - Club creation validates CSRF
8. `test_fencer_add_requires_csrf_token` - Fencer tracking validates CSRF

#### 5.2 Rate Limiting Tests
**File:** `tests/test_rate_limiting.py` (new file)

**Test Cases:**
1. `test_login_rate_limit_allows_under_threshold` - 4 attempts succeed
2. `test_login_rate_limit_blocks_over_threshold` - 6th attempt blocked (429)
3. `test_login_rate_limit_resets_on_success` - Successful login clears counter
4. `test_login_rate_limit_expires_after_window` - Old attempts don't count
5. `test_register_rate_limit_by_ip` - Multiple registrations from same IP blocked
6. `test_rate_limit_error_message_html` - HTML response shows user-friendly error
7. `test_rate_limit_error_message_json` - JSON response includes retry info

#### 5.3 Datetime Migration Tests
**File:** No new tests needed

**Validation:**
- Run existing test suite: `pytest`
- Verify no deprecation warnings in output
- Check that all timestamp-related tests still pass

#### 5.4 Integration Tests
**File:** `tests/test_security_integration.py` (new file)

**Test Cases:**
1. `test_login_csrf_and_rate_limit_together` - Both protections work together
2. `test_authenticated_actions_require_csrf` - All state-changing actions validate CSRF
3. `test_rate_limit_persists_across_requests` - Multiple requests increment counter

---

## Out of Scope

The following items from NEXT_STEPS.md are deferred:
- **Password Reset Flow** - Requires email infrastructure and additional UI (future phase)
- **Email Verification** - Requires confirmation workflow (future phase)
- **Per-User Timezones** - Feature enhancement, not security-critical (future phase)
- **HTML Email Templates** - UX improvement, not security-critical (Phase 4)
- **SQLAlchemy 2.0 Migration** - Low priority, no immediate benefit (future)

---

## Acceptance Criteria

### CSRF Protection
- [ ] `UserSession` model includes `csrf_token` field
- [ ] Migration adds `csrf_token` column and backfills existing sessions
- [ ] `csrf_service.py` implements token generation and validation
- [ ] Template helper `csrf_token()` available in all templates
- [ ] All state-changing forms include hidden CSRF input field
- [ ] All POST/PATCH/DELETE routes (except login/register) validate CSRF tokens
- [ ] CSRF validation returns 403 for missing/invalid tokens
- [ ] Tests cover token generation, validation, and enforcement
- [ ] Documentation updated in README.md

### Rate Limiting
- [ ] `rate_limit_service.py` implements sliding window rate limiting
- [ ] Login endpoint limited to 5 attempts per 5 minutes per username
- [ ] Registration endpoint limited to 3 attempts per hour per IP
- [ ] Rate limit errors return 429 status code with user-friendly message
- [ ] Successful login resets rate limit counter
- [ ] Configuration via environment variables (LOGIN_RATE_LIMIT_*, REGISTER_RATE_LIMIT_*)
- [ ] Tests cover rate limit enforcement, expiry, and reset behavior
- [ ] Documentation updated in README.md and .env.example

### Datetime Deprecation Fix
- [ ] All `datetime.utcnow()` calls replaced with `datetime.now(UTC)`
- [ ] Import statements updated to include `UTC` from datetime module
- [ ] Full test suite passes without deprecation warnings
- [ ] No regressions in timestamp-related functionality

### Configuration & Documentation
- [ ] `.env.example` includes all new rate limiting variables
- [ ] README.md documents CSRF token behavior
- [ ] README.md documents rate limiting configuration
- [ ] README.md notes in-memory rate limiting limitations
- [ ] ARCHITECTURE.md updated with security hardening details (optional but recommended)

---

## Implementation Notes

### CSRF Token Generation
Use Python's `secrets` module for cryptographic randomness:
```python
import secrets
token = secrets.token_hex(32)  # 64-character hex string
```

### Constant-Time Comparison
Use `secrets.compare_digest()` to prevent timing attacks:
```python
import secrets
is_valid = secrets.compare_digest(expected_token, provided_token)
```

### Rate Limiting Edge Cases
- **Concurrent Requests:** In-memory dict may have race conditions. Acceptable for private beta single-process deployment.
- **Distributed Deployment:** For multi-process production, migrate to Redis-backed rate limiting (document as future work).
- **IP Spoofing:** If behind proxy, use `X-Forwarded-For` header but validate against trusted proxies only.

### CSRF for Login/Register
Skipping CSRF for login/register is acceptable because:
1. No existing session to protect
2. Rate limiting provides primary brute-force protection
3. SameSite cookies prevent cross-site attacks on authenticated actions

Alternative for future: Pre-session CSRF tokens stored in Redis with 15-minute TTL.

---

## Security Impact Assessment

**Threat Model Coverage:**

| Threat | Mitigation | Status |
|--------|------------|--------|
| CSRF attacks on authenticated actions | CSRF tokens | ✅ Addressed |
| Brute-force login attempts | Rate limiting (5 attempts / 5 min) | ✅ Addressed |
| Account enumeration via registration | Rate limiting (3 attempts / hour) | ✅ Addressed |
| Session fixation | Session regeneration on login (existing) | ✅ Already implemented |
| Session hijacking | HTTP-only + SameSite cookies (existing) | ✅ Already implemented |
| Password cracking | Bcrypt hashing (existing) | ✅ Already implemented |
| SQL injection | SQLAlchemy ORM (existing) | ✅ Already implemented |

**Remaining Risks (Acceptable for Private Beta):**
- No account lockout after repeated failures (rate limiting provides temporary block)
- No CAPTCHA or proof-of-work (private beta, low abuse risk)
- In-memory rate limiting resets on process restart (document in ops guide)

---

## Dependencies

- Python `secrets` module (stdlib, no new dependency)
- Existing database migration infrastructure (Alembic)
- Existing test infrastructure (pytest)

---

## Rollout Plan

1. **Implement CSRF protection** (can test in isolation)
2. **Implement rate limiting** (can test in isolation)
3. **Fix datetime deprecations** (can deploy independently)
4. **Integration testing** (all features together)
5. **Documentation updates** (README, .env.example)
6. **Deploy to staging** (if available)
7. **Architect review** (code review against spec)
8. **Archive spec** (move to comms/tasks/archive/)

---

## Success Metrics

- All 27 deprecation warnings eliminated
- CSRF token validation enforced on all state-changing routes
- Login brute-force attempts blocked after 5 failures
- Registration spam blocked after 3 attempts per IP per hour
- Test coverage maintained or improved
- No performance degradation (rate limiting adds <1ms overhead)

---

## Related Documents

- Phase 1 Code Review: `comms/tasks/2025-10-01-phase1-code-review.md`
- Technical Backlog: `NEXT_STEPS.md` lines 44-60
- Architecture: `docs/ARCHITECTURE.md`
- Testing Guide: `docs/TESTING.md`

---

**Estimated Complexity:** Medium
**Estimated Time:** 4-6 hours for experienced developer
**Risk Level:** Low (incremental security improvements, no breaking changes)
