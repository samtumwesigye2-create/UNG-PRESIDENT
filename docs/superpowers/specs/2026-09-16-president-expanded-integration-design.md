# UNG-PRESIDENT Expanded Integration Design

## Goal
Integrate the expanded PRESIDENT implementation into the currently working production `main` without regressing HR registration, admin login, password reset, persistent Railway storage, or the current production startup path.

## Baseline
Production `main` remains authoritative for authentication, HR-code enrollment, password reset, SQLite persistence at `UNG_PRESIDENT_DB_PATH`, Docker startup through `bootstrap.py`, and Railway deployment configuration.

The historical `codex/finish-ung-president` branch is a source of expanded functionality only. It must not replace `main` wholesale because the branches have diverged and production contains newer fixes.

## Integration
Bring forward the expanded PRESIDENT application/data capabilities from the historical branch into focused modules on top of `main`. Preserve existing route contracts and authentication behavior. Add the expanded admin capabilities to the authenticated admin navigation/dashboard and connect each visible function to a real route and persistent data operation.

Expanded capabilities to preserve/include from the supplied PRESIDENT additions include citizen-abroad/consular records, travel advisories, emergency alerts, embassy/consulate directory, consular queue, media accreditation, document attestation, treaty/archive records, dual-control approval workflow, auditability, and the previously developed biometric enrollment/API capability where its implementation is recoverable.

## Data and security
Existing authentication and session behavior remain unchanged. Administrative write operations require authenticated authorized roles. Sensitive actions use audit records; dual-control actions must not be self-approved. Existing production data must survive deployment; schema additions are additive and initialized against the persistent database.

## UI
The existing working admin dashboard remains the shell. Expanded modules are added as clearly labeled admin navigation/dashboard functions. A module is not considered integrated merely because a button exists: its page, route, persistence, authorization, and expected action must work.

## Verification
Use regression tests before implementation for each integration group. Existing authentication/registration/password-reset tests must remain green. Add tests for expanded route availability, authorization, persistence, approval restrictions, and dashboard/navigation exposure. Deploy only after the combined test suite passes. Verify Railway startup and HTTP behavior after deployment.

## Deployment
Integrate on an isolated branch based on current `main`, review/test there, then fast-forward/merge the verified result to `main`. Railway production remains tied to `main`. Do not deploy the historical branch directly.