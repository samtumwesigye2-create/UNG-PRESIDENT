# UNG-PRESIDENT Security Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the Railway-hosted UNG-PRESIDENT platform with application, identity, edge-readiness, monitoring, backup, and disclosure controls without falsely marking provider-dependent protections as active.

**Architecture:** The public path is `Internet -> Cloudflare -> Railway web -> PostgreSQL`. Application controls remain independently enforceable server-side. Cloudflare, DNSSEC, HSTS preload, immutable/off-site backups, and phishing-resistant hardware MFA are tracked separately until deployed and verified.

**Tech Stack:** TanStack Start, React 19, Vite, Node.js, Railway, PostgreSQL, Cloudflare, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-13-ung-president-security-hardening-design.md`

## Global Constraints

- Do not alter or delete the Macaly fallback during migration.
- Do not fabricate official government domains, security contacts, or infrastructure status.
- Secrets stay in Railway/approved secret management, never source.
- Server-side authorization is authoritative; browser role claims are never trusted.
- Staff MFA is mandatory target state; privileged phishing-resistant MFA is required where the selected identity stack supports it.
- High-risk actions require execution-bound, single-use dual approval.
- All database access must be parameterized.
- Security controls use status values: `implemented`, `deployed`, `verified`, `pending_external`, `not_supported`.
- HSTS preload, DNSSEC, Cloudflare edge controls, immutable/off-site backups, and official-government-domain status are never marked verified without external evidence.

---

### Task 1: Security Status Registry and HTTP Headers

**Files:**
- Create: `src/security/control-status.ts`
- Create: `src/security/headers.ts`
- Create: `__tests__/security-headers.test.ts`
- Create: `docs/security/control-status.md`

**Interfaces:**
- Produces: `SecurityControlStatus`, `SECURITY_CONTROLS`, `buildSecurityHeaders({ production, hstsEnabled })`.

- [ ] Write tests asserting CSP, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, anti-framing policy, sensitive-cache defaults, and conditional HSTS.
- [ ] Run the focused test and confirm it fails before implementation.
- [ ] Implement a strict header builder with no wildcard script origins and no HSTS when `hstsEnabled=false`.
- [ ] Add the control registry with provider-dependent controls initially marked `pending_external`.
- [ ] Run focused tests and commit `feat: add security headers and control registry`.

### Task 2: Request Validation, CSRF, and Abuse Guards

**Files:**
- Create: `src/server/security/csrf.ts`
- Create: `src/server/security/validation.ts`
- Create: `src/server/security/rate-limit.ts`
- Create: `__tests__/security-request-guards.test.ts`

**Interfaces:**
- Produces: `issueCsrfToken()`, `verifyCsrfToken()`, strict validation helpers, and rate-limit decisions keyed by trusted request context.

- [ ] Write failing tests for missing/invalid CSRF, oversized form fields, invalid enums/emails, and login/form burst limits.
- [ ] Implement server-side validation with explicit length/format/enum constraints and rejection of unknown privileged-operation fields.
- [ ] Implement cryptographically random CSRF tokens bound to server-side/session state.
- [ ] Implement application-level rate-limit fallback for sensitive routes; document that Cloudflare edge limits remain a separate control.
- [ ] Run tests and commit `feat: add CSRF validation and abuse guards`.

### Task 3: Secure Railway Sessions and MFA Enforcement

**Files:**
- Create/Modify: `src/server/auth/*`
- Create: `__tests__/auth-security.test.ts`

**Interfaces:**
- Produces secure session creation/rotation/revocation and server-side MFA-state enforcement.

- [ ] Write failing tests for `HttpOnly`, `Secure` in production, `SameSite`, session rotation after login/role change, inactivity expiry, revoked-account denial, and MFA-required denial.
- [ ] Implement session identifiers using cryptographically random values and store only hashed/session-safe representations where appropriate.
- [ ] Require verified MFA state for every active staff session before privileged access.
- [ ] Preserve current OTP as transitional factor but label hardware/passkey MFA `pending_external` until a capable identity provider/WebAuthn implementation is connected.
- [ ] Run tests and commit `feat: enforce secure sessions and staff MFA`.

### Task 4: Server RBAC and Execution-Bound Dual Approval

**Files:**
- Create/Modify: `src/server/security/authorization.ts`
- Create/Modify: staff/executive/records service modules created by the Railway persistence migration
- Create: `__tests__/privileged-approval.test.ts`

**Interfaces:**
- Produces: `requirePermission()`, `requestApproval()`, `approveRequest()`, `executeApprovedAction()` with one-time consumption.

- [ ] Write failing tests proving requester cannot self-approve, approval is target/action-bound, approval is one-time, and revoked/suspended staff cannot execute.
- [ ] Implement role-to-permission checks server-side for `president`, `admin`, `staff`, `protocol`, `press`.
- [ ] Implement approval state with immutable request payload hash or equivalent exact-action binding.
- [ ] Require and consume approval for privileged role changes, policy-required account reactivation/revocation, executive publication, official-document publication, and emergency notices.
- [ ] Audit request/review/rejection/execution.
- [ ] Run tests and commit `feat: bind high-risk actions to dual approval`.

### Task 5: PostgreSQL and Secret Safety

**Files:**
- Create/Modify: `src/server/db.ts`
- Create: `src/server/security/redaction.ts`
- Create: `__tests__/database-security.test.ts`
- Create: `.env.example`

**Interfaces:**
- Produces parameterized DB access and secret-safe logging helpers.

- [ ] Write failing tests that reject raw SQL interpolation in service helpers and redact password/token/code/database-secret fields from logs.
- [ ] Use the selected PostgreSQL client only through parameterized query helpers.
- [ ] Enforce private `DATABASE_URL` use through Railway variables; never expose DB credentials to browser bundles.
- [ ] Ensure enrollment codes remain cryptographically hashed.
- [ ] Run tests and commit `feat: harden database and secret handling`.

### Task 6: Automated Security Scanning and Audit Events

**Files:**
- Create: `.github/workflows/security.yml`
- Create/Modify: audit service/schema under `src/server/*`
- Create: `__tests__/security-audit.test.ts`
- Create: `docs/security/patch-and-exception-policy.md`

**Interfaces:**
- Produces CI checks and normalized security audit events.

- [ ] Write tests for login failure/success, MFA/recovery, invitation, role/status, approval, publication/archive audit events.
- [ ] Implement structured audit events without passwords, enrollment codes, session tokens, reset tokens, or DB credentials.
- [ ] Add CI steps for install/build/test, dependency audit, secret scanning, and static security checks available without exposing credentials.
- [ ] Define severity/exception policy with owner, reason, compensating control, and expiry.
- [ ] Commit `feat: add automated security scanning and audit events`.

### Task 7: Backup/Recovery and VDP Readiness

**Files:**
- Create: `docs/security/backup-recovery.md`
- Create: `docs/security/vulnerability-disclosure-policy.md`
- Create: `docs/security/restore-test-template.md`
- Add public VDP route/component only if it can be published without fabricated contact information.

**Interfaces:**
- Produces documented backup controls, restore evidence requirements, and a truthful VDP surface.

- [ ] Document Railway/PostgreSQL backup mechanism actually available after inspection.
- [ ] Keep immutable/off-site status `pending_external` until a separate failure-domain copy with deletion protection is configured.
- [ ] Define restore test evidence for DB records, staff authorization, presidential media, and audit logs.
- [ ] Publish VDP scope/prohibited-testing/safe-harbor-process text but omit any reporting address that has not been supplied/approved.
- [ ] Commit `docs: add backup recovery and VDP controls`.

### Task 8: Cloudflare Edge and Production Verification

**Files:**
- Create: `docs/security/cloudflare-edge-checklist.md`
- Create: `docs/security/security-acceptance.md`

**Interfaces:**
- Produces verified/pending status for CDN, DDoS, WAF, rate limiting, origin reduction, HTTPS, HSTS, DNSSEC, and official-domain controls.

- [ ] Connect production DNS to Cloudflare only after the Railway temporary deployment is healthy.
- [ ] Enable proxied DNS/CDN, managed DDoS protection, supported WAF rules, and narrowly scoped rate rules for `/admin`, auth, enrollment/reset, and public forms.
- [ ] Verify HTTPS and HTTP-to-HTTPS behavior.
- [ ] Reduce/test direct Railway-origin exposure to the maximum technically supported level.
- [ ] Enable HSTS only after production HTTPS validation; leave preload unapproved until explicitly authorized.
- [ ] Enable/verify DNSSEC if authoritative DNS supports it.
- [ ] Record exact provider evidence and update control status from `pending_external` -> `deployed` -> `verified` only when tested.
- [ ] Commit `docs: record production security verification`.

### Task 9: Final Security Acceptance

**Files:**
- Modify: `docs/security/security-acceptance.md`

**Interfaces:**
- Produces the cutover security decision.

- [ ] Run the full automated test suite.
- [ ] Run TypeScript/build validation.
- [ ] Run targeted negative tests for unauthorized access, self-approval, reused approval, CSRF, session revocation, invalid input, and form abuse.
- [ ] Verify public security headers on the Railway/Cloudflare path.
- [ ] Verify PostgreSQL is not public and no browser bundle contains secrets.
- [ ] Verify backup/restore evidence and media availability.
- [ ] Confirm no unsupported capability is represented as active.
- [ ] Record pass/fail/pending-external evidence and commit `test: complete UNG-PRESIDENT security acceptance`.
