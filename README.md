# UNG-PRESIDENT

The Python application is recovered from `ung president 3(2).pdf`. It provides public presidential pages, executive orders, honours, visitor requests, petitions, and an authenticated staff portal for appointments, events, state visits, press statements, HR enrollment and audit logs. Its seals and national flag artwork are embedded.

## Run

Use Python 3.12, install `requirements.txt`, then run `python ung_president.py`. Open http://localhost:8000. On the first start, a one-use **HR enrollment code** appears in the console. Use it at `/admin/register` to create the first administrator; there is no default password.

## Railway deployment

The root Dockerfile runs the Python application independently of the older React/Convex source retained in this repository. Provision Railway PostgreSQL and expose its `DATABASE_URL` to the service. Production startup deliberately refuses SQLite. Also set `UNG_PRESIDENT_SECRET` to a persistent cryptographically random value and set a one-time `UNG_PRESIDENT_BOOTSTRAP_CODE` for the first administrator enrollment. Remove that bootstrap variable after the account has been created. Railway supplies `PORT`; `/health` checks database connectivity and HTTPS session cookies are enabled automatically.

SQLite remains available only for local development and tests through `UNG_PRESIDENT_DB_PATH`. This update does not migrate older Convex or SQLite records automatically; existing records, accounts, and media must be inventoried and migrated explicitly before replacing a live service.

## Authentication

Passwords use salted PBKDF2-HMAC-SHA256 (260,000 iterations), constant-time comparison and a 12-character complexity policy. Five bad passwords trigger a 15-minute account lockout. Session cookies contain HMAC-signed payloads, expire after eight hours, and use HttpOnly and SameSite=Strict. HR codes are stored hashed with the signing secret; registration tokens expire after 20 minutes. The signing secret must stay stable across restarts so unused HR codes remain valid. Local execution creates a private `.secret` file rather than changing the key on every start.

Role checks gate privileged writes; only the president signs orders. Signed sessions are revalidated against the current account and role on every protected request. Logout clears the browser cookie, but a copied token remains usable until its eight-hour expiry unless the account is removed or renamed. There is no MFA or central JANUS integration in this build. Avoid treating the handoff as equivalent to all security features described in the older planning documents.

## Validation

Install `requirements-dev.txt`, then run `python -m pytest tests -q`. Tests cover public pages, unauthorized access, password policy, login cookies, restricted signing/audit access, one-use enrollment, password hashing, token tampering and HTML escaping. Registration's missing password-policy helper and template escaping have been corrected from the PDF source.


## UNG-VAULT / Digital SCIF integration

The Digital Executive Suite now includes a principal-only **Secure Vault & SCIF** area.

- UNG-PRESIDENT is the executive-facing launch surface.
- UNG-VAULT remains a separate security boundary and continues to own cryptography, protected-object storage, classification enforcement, Digital SCIF sessions, audit records, and SENTINEL security-event forwarding.
- The Executive Suite checks VAULT service health and exposes executive shortcuts for protected documents, Digital SCIF, encrypted file exchange, redacted sharing, emergency revocation, and security activity.
- Configure the backend location with `UNG_VAULT_BASE_URL`.
- UNG-PRESIDENT does not store VAULT master keys or SCIF plaintext.


## Executive record storage policy

The Digital Executive Suite now treats UNG-VAULT as the authoritative encrypted store for newly created executive operational records.

- Secure communications, executive archive entries and boardroom/private-suite meeting records are serialized and sent to UNG-VAULT over an HMAC-SHA256 signed service-to-service channel.
- VAULT encrypts the complete record before persistence and returns a protected object ID.
- UNG-PRESIDENT stores only local display/index metadata plus the VAULT object reference; message bodies and protected notes are no longer retained as local plaintext or local application ciphertext for new records.
- Record creation is fail closed: if VAULT is unavailable or rejects the signed request, the Executive Suite does not create the local record.
- Existing legacy records remain readable under their previous storage model until separately migrated.
- Authentication/session state and password/MFA material remain operational identity state, not executive document records, and are not copied into VAULT as record payloads.
