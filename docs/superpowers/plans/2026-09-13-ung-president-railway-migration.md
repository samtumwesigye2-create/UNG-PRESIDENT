# UNG-PRESIDENT Railway Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move UNG-PRESIDENT from Macaly/Convex to GitHub + Railway + PostgreSQL while preserving the current public site, staff portal, security model, records, and media.

**Architecture:** Keep the current TanStack Start / React 19 application structure, replace Macaly/Convex persistence with a Railway-hosted server layer backed by PostgreSQL, migrate existing records/media, and cut over only after acceptance testing. Macaly stays untouched as a temporary fallback until the Railway version is proven.

**Tech Stack:** TanStack Start, React 19, Vite, Tailwind CSS, Node.js, PostgreSQL, Railway, GitHub.

**Spec:** `docs/superpowers/specs/2026-09-13-ung-president-railway-migration-design.md`

## Global Constraints

- Do not delete or alter the existing Macaly production project during migration.
- Do not fabricate official government content or contact information.
- Preserve the current public design, staff portal, RBAC, audit behavior, records, and media.
- No default passwords or plaintext enrollment secrets.
- Secrets must live in Railway environment variables, never source control.
- Database migration must be additive/reversible until final cutover.
- Railway is the target host; PostgreSQL is the target database.

---

### Task 1: Capture the Current Application Source

**Files:**
- Populate: repository root with current application source
- Create: `docs/migration/source-inventory.md`
- Create: `docs/migration/media-inventory.md`

**Interfaces:**
- Consumes: current Macaly project source and uploaded media references
- Produces: complete GitHub source tree and inventories used by later tasks

- [ ] **Step 1: Enumerate the current Macaly source tree**

Record all application, Convex, test, configuration, and documentation files. Exclude Macaly internal sandbox metadata and credentials.

- [ ] **Step 2: Copy source files into GitHub without changing behavior**

Preserve paths and text exactly where possible so later migration work starts from the known-good implementation.

- [ ] **Step 3: Inventory media references**

Document each presidential image/flag/seal URL or asset identifier and where it is used.

- [ ] **Step 4: Verify the captured source**

Confirm `package.json`, `src/`, `convex/`, tests, and configuration files are present and coherent.

- [ ] **Step 5: Commit**

Commit message: `chore: capture UNG-PRESIDENT source`

---

### Task 2: Establish the Railway Project and PostgreSQL

**Files:**
- Create: `.env.example`
- Create: `railway.json` or equivalent Railway deployment configuration if required by the repository
- Create: `src/server/db.ts`
- Create: `src/server/health.ts`
- Test: `__tests__/railway-health.test.ts`

**Interfaces:**
- Produces: `DATABASE_URL`-driven PostgreSQL connection and `/health` readiness endpoint

- [ ] **Step 1: Write the failing health/database test**

Verify the health handler reports application readiness and database reachability separately.

- [ ] **Step 2: Run the test and confirm failure**

Expected: failure because Railway/PostgreSQL integration does not yet exist.

- [ ] **Step 3: Create Railway project `UNG-PRESIDENT` and PostgreSQL service**

Use the existing UNG Railway workspace. Do not attach a production domain yet.

- [ ] **Step 4: Implement the minimal database connector and health route**

Read only `DATABASE_URL` from environment and fail closed when unavailable.

- [ ] **Step 5: Run tests and commit**

Commit message: `feat: add Railway PostgreSQL foundation`

---

### Task 3: Recreate the Application Data Model in PostgreSQL

**Files:**
- Create: `src/server/schema/*.ts` or migration files matching the chosen PostgreSQL library
- Create: `src/server/migrations/*`
- Test: `__tests__/database-schema.test.ts`

**Interfaces:**
- Consumes: current Convex schema
- Produces: PostgreSQL tables for public content, staff identity, invitations, approvals, records, revisions, notices, subscriptions, contact messages, visit requests, executive government, events, and audit logs

- [ ] **Step 1: Write schema tests for required entities and uniqueness constraints**

Assert stable identifiers, publication states, staff email/employee uniqueness, invitation one-time semantics, revision ordering, and audit persistence.

- [ ] **Step 2: Run tests and confirm failure**

- [ ] **Step 3: Implement additive PostgreSQL migrations**

Map optional Convex fields conservatively; do not invent required values for records that may already exist.

- [ ] **Step 4: Apply migrations to the Railway PostgreSQL service**

- [ ] **Step 5: Run tests and commit**

Commit message: `feat: add UNG-PRESIDENT PostgreSQL schema`

---

### Task 4: Replace Convex Persistence with Server-Side PostgreSQL Services

**Files:**
- Create/Modify: `src/server/services/*`
- Modify: public/staff data-loading code under `src/`
- Test: existing application tests plus new service tests

**Interfaces:**
- Produces: service functions equivalent to current public, staff, enrollment, executive, records, and public-service Convex functions

- [ ] **Step 1: Write failing service tests for public homepage and official-document verification**

- [ ] **Step 2: Implement public read services**

Published-only filters must remain enforced server-side.

- [ ] **Step 3: Write failing tests for staff/enrollment/RBAC operations**

- [ ] **Step 4: Implement staff, invitation, lifecycle, approval, and audit services**

Hash enrollment codes; require active authorized staff; never trust role claims from the client.

- [ ] **Step 5: Write failing tests for executive government, events, documents, revisions, and notices**

- [ ] **Step 6: Implement equivalent write services and workflow transitions**

Preserve existing publication-state behavior unless explicitly hardened in a separate reviewed change.

- [ ] **Step 7: Run the full test suite and commit**

Commit message: `feat: move application persistence to PostgreSQL`

---

### Task 5: Move Authentication off Macaly/Convex

**Files:**
- Create/Modify: `src/server/auth/*`
- Modify: staff login/enrollment UI integration
- Test: `__tests__/auth-session.test.ts`, existing staff security tests

**Interfaces:**
- Produces: secure session identity used by all server-side authorization checks

- [ ] **Step 1: Write failing tests for login, logout, inactive-account denial, and role lookup**

- [ ] **Step 2: Implement password hashing and secure session cookies**

Use a modern password hash and `HttpOnly`, `Secure`, `SameSite` session cookies in production.

- [ ] **Step 3: Preserve invitation-only enrollment semantics**

Enrollment binds authorized email, employee identity, intended role, expiry, and one-time use.

- [ ] **Step 4: Implement password reset/verification using the approved mail provider only when configured**

No fabricated sender address or credentials.

- [ ] **Step 5: Run security tests and commit**

Commit message: `feat: migrate staff authentication to Railway`

---

### Task 6: Migrate Existing Data and Media

**Files:**
- Create: `scripts/migrate-convex-export.ts`
- Create: `scripts/verify-migration.ts`
- Create: `docs/migration/data-reconciliation.md`

**Interfaces:**
- Consumes: exported current records/media references
- Produces: PostgreSQL records and verified media mappings

- [ ] **Step 1: Export current production data without modifying it**

- [ ] **Step 2: Write migration-transform tests using representative exported records**

- [ ] **Step 3: Import into Railway PostgreSQL preserving stable references where feasible**

- [ ] **Step 4: Reconcile record counts and critical identifiers**

Compare public documents, staff profiles, executive records, events, subscriptions, contact messages, visit requests, audit logs, and revisions.

- [ ] **Step 5: Migrate or preserve media URLs and verify every presidential image renders**

- [ ] **Step 6: Commit migration tooling**

Commit message: `feat: add UNG-PRESIDENT data migration tooling`

---

### Task 7: Deploy the Application to Railway

**Files:**
- Modify deployment configuration only as needed
- Test: production build and Railway deployment health

**Interfaces:**
- Produces: temporary Railway URL backed by Railway PostgreSQL

- [ ] **Step 1: Run the complete automated test suite**

Expected: all tests pass.

- [ ] **Step 2: Run TypeScript/CSS/build validation**

Expected: zero blocking errors and successful production build.

- [ ] **Step 3: Create the Railway application deployment from the GitHub repository**

Configure required environment variables in Railway, not GitHub source.

- [ ] **Step 4: Verify `/health` and application startup**

- [ ] **Step 5: Keep the deployment on its temporary Railway URL**

Do not cut over the production domain yet.

---

### Task 8: End-to-End Acceptance and Cutover Readiness

**Files:**
- Create: `docs/migration/acceptance-results.md`

**Interfaces:**
- Produces: signed-off readiness decision for retiring Macaly

- [ ] **Step 1: Test public homepage/navigation and presidential imagery**

- [ ] **Step 2: Test published executive government, events, policies/regulations, and official-document verification**

- [ ] **Step 3: Test contact, visit request, newsletter subscription, and persistence after reload**

- [ ] **Step 4: Test staff login, enrollment, RBAC, account lifecycle, document administration, and audit logs**

- [ ] **Step 5: Compare Railway/PostgreSQL critical data against the migration reconciliation report**

- [ ] **Step 6: Record pass/fail evidence**

Only after all critical checks pass is UNG-PRESIDENT ready for production domain cutover and subsequent Macaly removal.
