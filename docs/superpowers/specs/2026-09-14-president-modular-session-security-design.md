# PRESIDENT Modular Session Security Design

## Goal

Add server-side revocable administrator sessions to UNG-PRESIDENT without repeatedly rewriting the oversized `ung_president.py` application file.

## Architecture

Keep `ung_president.py` as the legacy application/UI core and keep `president_app.py` as the production entry point. Add a focused `session_security.py` module responsible for opaque session-token generation, SHA-256 token hashing, persistence, expiration checks, revocation, and session-schema initialization. The wrapper is the integration boundary for modular security behavior and existing backup startup behavior.

The raw opaque session token is sent only to the browser cookie. Only its SHA-256 hash is persisted. Session records contain `user_id`, `token_hash`, `created_at`, `expires_at`, and nullable `revoked_at`. A protected request is authenticated only when the presented token hashes to a stored, unrevoked, unexpired session and its user still exists.

## Database compatibility

The session module must work with the existing `db_cursor` abstraction so the same implementation supports SQLite tests and PostgreSQL production. Schema creation must be idempotent and run before session operations. Timestamp values use SQL-compatible UTC values and database-side `CURRENT_TIMESTAMP` checks where practical.

## Application flow

On successful login, create a new opaque persistent session and place that token in the existing secure `session` cookie. On each protected request, verify the server-side session and reload the current account. On logout, revoke the presented session before deleting the browser cookie. Existing signed-session helpers may remain temporarily for compatibility tests, but protected application authentication moves to persistent sessions.

## Integration boundary

`president_app.py` remains the small production wrapper and continues starting the backup worker. Session initialization/integration is attached there or through small imported helpers rather than moving embedded templates or artwork out of `ung_president.py` in this change. The large legacy file is otherwise treated as frozen except for any unavoidable minimal hook; if a hook cannot be made safely through the available patch mechanism, the wrapper/module must provide it without a whole-file rewrite.

## Testing

Use the already-committed RED session tests as the acceptance contract. Correct brittle tests that refer to guessed route-function names so they target the actual `login`/logout functions without weakening behavioral requirements. Add focused unit tests for the new module if required. The complete repository test suite must pass before this branch is considered GREEN.

## Safety and release constraints

Do not deploy production. Do not merge PR #3 or merge this work to `main`. Keep changes on `feature/revocable-sessions` until tests and CI are green. Production database migration and release remain gated on verified backup/restore readiness.