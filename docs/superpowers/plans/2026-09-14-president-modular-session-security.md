# PRESIDENT Modular Session Security Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace browser-only signed administrator authentication with server-side revocable sessions while keeping the oversized legacy PRESIDENT application essentially frozen.

**Architecture:** `ung_president.py` remains the legacy UI/application core. A focused `session_security.py` owns session schema, opaque token generation, SHA-256 hashing, persistence, expiry verification, and revocation; `president_app.py` remains the small production wrapper/integration boundary and continues backup startup.

**Tech Stack:** Python, FastAPI, SQLite/PostgreSQL through the existing `db_cursor` abstraction, `secrets`, `hashlib`, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-14-president-modular-session-security-design.md`

## Global Constraints

- Keep work on `feature/revocable-sessions`.
- Do not deploy production.
- Do not merge PR #3 or merge this work to `main`.
- Store only SHA-256 hashes of opaque session tokens; never persist raw tokens.
- Preserve SQLite and PostgreSQL compatibility.
- Existing backup-worker startup behavior in `president_app.py` must remain intact.
- Treat `ung_president.py` as frozen except for an unavoidable minimal hook; never replace it from truncated connector content.
- Follow RED → GREEN → REFACTOR and require the complete test suite to pass before completion.

---

### Task 1: Correct the RED acceptance contracts

**Files:**
- Modify: `tests/test_session_login_contract.py`
- Modify: `tests/test_session_logout_contract.py`
- Inspect: `ung_president.py` route definitions

**Interfaces:**
- Consumes: actual FastAPI login/logout function names from the legacy application.
- Produces: RED tests that inspect real application functions rather than guessed aliases.

- [ ] Fetch the narrow route-definition ranges needed to identify the actual login and logout function names.
- [ ] Update only the brittle source-inspection tests to reference those real functions without weakening the required persistent-session behavior.
- [ ] Run CI and verify the suite remains RED for missing persistent-session implementation, not because of guessed function names.
- [ ] Commit the corrected RED contracts.

### Task 2: Build the isolated persistent-session module

**Files:**
- Create: `session_security.py`
- Create/modify focused tests under `tests/` as needed.

**Interfaces:**
- Consumes: existing `db_cursor` callable/context manager and `SESSION_MAX_AGE_SECONDS`.
- Produces: `init_session_schema(db_cursor)`, `create_persistent_session(db_cursor, user_id, max_age_seconds)`, `verify_persistent_session(db_cursor, token)`, `revoke_persistent_session(db_cursor, token)`.

- [ ] Write/retain failing tests for schema creation, opaque token generation, hash-only persistence, expiration rejection, and revocation rejection.
- [ ] Verify those tests fail for the intended missing-module/behavior reason.
- [ ] Implement an idempotent `sessions` table with `user_id`, unique `token_hash`, `created_at`, `expires_at`, and nullable `revoked_at`.
- [ ] Generate tokens with `secrets.token_urlsafe(32)` and persist only `hashlib.sha256(token.encode()).hexdigest()`.
- [ ] Verify sessions by hash, requiring `revoked_at IS NULL`, `expires_at > CURRENT_TIMESTAMP`, and a still-existing user; return current user identity/role.
- [ ] Revoke only the presented session by setting `revoked_at=CURRENT_TIMESTAMP`.
- [ ] Run focused tests until GREEN, then commit.

### Task 3: Integrate security through the small PRESIDENT wrapper

**Files:**
- Modify: `president_app.py`
- Modify/create: small integration helper module if route wrapping/overrides need isolation.
- Avoid modifying: `ung_president.py` unless a complete safe source representation becomes available and a minimal hook is unavoidable.

**Interfaces:**
- Consumes: `app`, `db_cursor`, legacy login/logout/current-user flow, and the functions from `session_security.py`.
- Produces: application startup that initializes session schema and authentication flow that creates, verifies, and revokes persistent sessions.

- [ ] Write a failing integration test proving a login-created cookie maps to a server-side session and a revoked/expired session cannot access `/admin`.
- [ ] Verify the integration test fails before wrapper wiring.
- [ ] Initialize the session schema during wrapper startup without disturbing backup-worker startup.
- [ ] Wire successful login to create a fresh persistent session, protected requests to verify it, and logout to revoke it before cookie deletion using the smallest safe integration mechanism available.
- [ ] Preserve existing cookie security attributes (`HttpOnly`, strict SameSite, configured Secure/max-age behavior).
- [ ] Run focused integration tests until GREEN, then commit.

### Task 4: Full regression and CI acceptance

**Files:**
- No new production files unless a failing regression requires a minimal correction.

**Interfaces:**
- Consumes: completed modular session implementation.
- Produces: verified branch suitable for review into `codex/finish-ung-president`, but not production deployment.

- [ ] Run `python -m pytest tests -q` through CI.
- [ ] Confirm all session tests and pre-existing PRESIDENT tests pass.
- [ ] Inspect failures rather than weakening tests; apply minimal fixes using a fresh RED/GREEN cycle when required.
- [ ] Verify the final branch commit has successful GitHub Actions status.
- [ ] Compare `feature/revocable-sessions` against `codex/finish-ung-president` and confirm no production/deployment changes or accidental giant-file replacement occurred.
- [ ] Only after GREEN verification, prepare the branch for review into `codex/finish-ung-president`; do not merge to `main` and do not deploy.