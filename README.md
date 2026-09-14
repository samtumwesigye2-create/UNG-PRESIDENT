# UNG-PRESIDENT

The Python application is recovered from `ung president 3(2).pdf`. It provides public presidential pages, executive orders, honours, visitor requests, petitions, and an authenticated staff portal for appointments, events, state visits, press statements, HR enrollment and audit logs. Its seals and national flag artwork are embedded.

## Run

Use Python 3.12, install `requirements.txt`, then run `python ung_president.py`. Open http://localhost:8000. On the first start, a one-use **HR enrollment code** appears in the console. Use it at `/admin/register` to create the first administrator; there is no default password.

## Railway deployment

The root Dockerfile runs the Python application independently of the older React/Convex source retained in this repository. Set `UNG_PRESIDENT_SECRET` to a persistent cryptographically random value (generate with `python -c 'import secrets; print(secrets.token_hex(32))'`). Attach a persistent volume at `/data` and set `UNG_PRESIDENT_DB_PATH=/data/ung_president.db`. Use one replica and one process: the supplied backend uses SQLite and process-local rate limiting. Railway supplies `PORT`; `/health` checks database connectivity. HTTPS session cookies are enabled on Railway.

This code update does not migrate existing Convex records, accounts or media into SQLite. Existing data must be inventoried and explicitly migrated before replacing an existing live service. PostgreSQL migration remains separate work; this supplied build uses SQLite.

## Authentication

Passwords use salted PBKDF2-HMAC-SHA256 (260,000 iterations), constant-time comparison and a 12-character complexity policy. Five bad passwords trigger a 15-minute account lockout. Session cookies contain HMAC-signed payloads, expire after eight hours, and use HttpOnly and SameSite=Strict. HR codes are stored hashed with the signing secret; registration tokens expire after 20 minutes. The signing secret must stay stable across restarts so unused HR codes remain valid. Local execution creates a private `.secret` file rather than changing the key on every start.

Role checks gate privileged writes; only the president signs orders. The supplied sessions are stateless: logout clears the browser cookie but does not revoke a copied token. Role changes require expiry of existing tokens. There is no MFA or central JANUS integration in this build. Avoid treating the handoff as equivalent to all security features described in the older planning documents.

## Validation

Install `requirements-dev.txt`, then run `python -m pytest tests -q`. Tests cover public pages, unauthorized access, password policy, login cookies, restricted signing/audit access, one-use enrollment, password hashing, token tampering and HTML escaping. Registration's missing password-policy helper and template escaping have been corrected from the PDF source.
