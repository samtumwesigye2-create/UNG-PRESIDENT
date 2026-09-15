"""Server-side revocable session storage for UNG-PRESIDENT."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

SESSION_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def init_session_schema(db_cursor) -> None:
    """Create the session table using the application's DB abstraction."""
    with db_cursor(commit=True) as cur:
        cur.execute(SESSION_SCHEMA)


def create_persistent_session(db_cursor, user_id: int, max_age_seconds: int) -> str:
    """Create a new opaque session. Only its hash is persisted."""
    init_session_schema(db_cursor)
    token = secrets.token_urlsafe(32)
    hashed = token_hash(token)
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=max_age_seconds)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    with db_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO sessions (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
            (user_id, hashed, expires_at),
        )
    return token


def verify_persistent_session(db_cursor, token: str):
    """Return the current account for an active, unexpired, unrevoked session."""
    if not token:
        return None
    init_session_schema(db_cursor)
    hashed = token_hash(token)
    with db_cursor() as cur:
        cur.execute(
            "SELECT u.id AS user_id, u.username, u.role, s.expires_at, s.revoked_at "
            "FROM sessions s JOIN users u ON u.id=s.user_id "
            "WHERE s.token_hash=? AND s.revoked_at IS NULL "
            "AND s.expires_at > CURRENT_TIMESTAMP",
            (hashed,),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {"user_id": row["user_id"], "username": row["username"], "role": row["role"]}


def revoke_persistent_session(db_cursor, token: str) -> None:
    """Revoke only the session represented by the supplied opaque token."""
    if not token:
        return
    init_session_schema(db_cursor)
    hashed = token_hash(token)
    with db_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE sessions SET revoked_at=CURRENT_TIMESTAMP "
            "WHERE token_hash=? AND revoked_at IS NULL",
            (hashed,),
        )
