# UNG-PRESIDENT Railway Migration Design

## Goal
Move UNG-PRESIDENT off Macaly and onto the existing UNG Railway hosting stack without losing source code, public content, staff functionality, authentication state, presidential records, or uploaded media references.

## Target Architecture
- Source of truth: `samtumwesigye2-create/UNG-PRESIDENT` on GitHub.
- Application hosting: Railway project `UNG-PRESIDENT`.
- Database: Railway PostgreSQL.
- Frontend: preserve the existing TanStack Start / React 19 public site and staff portal behavior and visual design.
- Backend: replace Convex/Macaly-specific persistence and auth bindings with Railway-hosted application services backed by PostgreSQL.
- Media: preserve existing uploaded presidential imagery by migrating assets or their stable references before Macaly is removed.

## Migration Safety
Macaly remains read-only as a temporary source/fallback during migration. No further feature deployment will be made there. The Macaly project is not deleted until the Railway deployment has passed acceptance testing and all required data/media have been verified.

## Functional Preservation
The migration must preserve public presidential content, executive-government directory, presidential records, events, official-document verification, contact and visit-request workflows, newsletter subscriptions, staff portal, invitation enrollment, account lifecycle states, RBAC, audit trails, and the formal presidential visual design.

## Security
No default credentials are allowed. Staff authorization remains server-side. Privileged publication and staff administration remain restricted. Secrets are stored only as Railway environment variables. PostgreSQL migrations must be additive and reversible until cutover.

## Data Flow
1. Export current Macaly/Convex source and schema.
2. Inventory live Convex tables and records.
3. Create PostgreSQL schema and migration scripts.
4. Import records with stable identifiers where feasible.
5. Point the Railway application at PostgreSQL.
6. Validate public and staff flows against the migrated data.
7. Cut over only after acceptance passes.

## Acceptance Criteria
- GitHub contains the complete deployable source.
- Railway build and health checks pass.
- PostgreSQL contains the migrated application data.
- Public homepage and public records work.
- `/admin` authentication and RBAC work.
- Published documents can be verified through the verification route.
- Contact, visit-request, subscription, and staff workflows persist after reload/redeploy.
- Uploaded imagery renders correctly.
- Existing Macaly production can be retired only after the Railway deployment passes these checks.
