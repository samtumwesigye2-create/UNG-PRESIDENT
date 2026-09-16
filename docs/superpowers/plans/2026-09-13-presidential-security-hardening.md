# UNG-PRESIDENT Security Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add verifiable layered security controls to UNG-PRESIDENT across application headers, CI security scanning, staff identity, edge protection, recovery, and vulnerability disclosure.

**Architecture:** Separate controls into application controls we can implement directly in the repository/Railway and provider controls that require an edge/DNS/backup service. Every control gets an explicit lifecycle state so planned infrastructure is never misreported as active. Application changes are test-first and land through the isolated security branch.

**Tech Stack:** TanStack Start, Nitro, React 19, Vitest, GitHub Actions, Railway, PostgreSQL target, external edge/DNS provider to be selected/configured.

**Spec:** `docs/superpowers/specs/2026-09-13-presidential-security-hardening.md`

## Global Constraints
- No fabricated official domains, contacts, or security addresses.
- No claim that WAF, DDoS scrubbing, DNSSEC, origin shielding, immutable backups, or phishing-resistant MFA are active until configured and verified.
- Preserve existing RBAC and staff lifecycle controls while strengthening them.
- Secrets stay in host/provider secret stores, never source control.
- Security-critical code changes require tests first.

---

### Task 1: Application Transport and Browser Security Headers
**Files:**
- Test: `__tests__/security-headers.test.ts`
- Create: `src/server/security/headers.ts`
- Create: `server/middleware/security.ts`

- [ ] Write failing tests for HSTS, CSP, frame protection, no-sniff, referrer policy, permissions policy and HTTPS redirect behavior contract.
- [ ] Run tests and observe failure because the security module does not exist.
- [ ] Implement minimal header policy helper.
- [ ] Add Nitro middleware that applies headers to every response and redirects insecure production requests when proxy headers prove HTTP.
- [ ] Run tests and build.

### Task 2: Automated Vulnerability and Static Security Scanning
**Files:**
- Create: `.github/dependabot.yml`
- Create: `.github/workflows/security.yml`

- [ ] Add weekly npm dependency update checks.
- [ ] Add pull-request/default-branch test and build checks.
- [ ] Add npm audit and CodeQL scanning with least-required workflow permissions.
- [ ] Verify workflow results on the security PR.

### Task 3: Vulnerability Disclosure Foundation
**Files:**
- Create: `src/routes/security.tsx`
- Create later when approved contact exists: `public/.well-known/security.txt`

- [ ] Create VDP page with scope/safe-harbor/reporting guidance without inventing a security contact.
- [ ] Ensure the page explicitly shows the reporting channel as pending until configured.
- [ ] Add `security.txt` only after a verified contact is supplied.

### Task 4: Staff Phishing-Resistant MFA
**Files:**
- Modify after Railway auth migration: `src/server/auth/*`, staff UI, tests.

- [ ] Add WebAuthn/passkey registration and assertion tests.
- [ ] Require hardware/passkey MFA for president/admin roles.
- [ ] Preserve role and active-status revalidation server-side.
- [ ] Add recovery policy without bypass tokens stored in plaintext.
- [ ] Mark PIV federation separately until an identity provider exists.

### Task 5: Edge DDoS/WAF/Origin Shielding and DNSSEC
**Provider configuration:** external edge/DNS platform in front of Railway.

- [ ] Put production hostname behind enterprise CDN/reverse proxy.
- [ ] Enable managed WAF rules and rate limiting.
- [ ] Restrict direct-origin access where supported and verify bypass attempts fail.
- [ ] Enable DNSSEC and validate DS chain.
- [ ] Enable HSTS preload only after every covered production subdomain passes HTTPS validation.
- [ ] Record evidence and exact provider configuration in `docs/security/edge-verification.md`.

### Task 6: Backup and Recovery
**Target:** Railway PostgreSQL plus logically separate backup destination.

- [ ] Configure automated database backups and retention.
- [ ] Configure separate/off-site copy or immutable object retention.
- [ ] Document RPO/RTO.
- [ ] Run a restore drill to an isolated database.
- [ ] Record checksums/count reconciliation and restore timing before marking the control verified.

### Task 7: Security Acceptance Matrix
**Files:**
- Create: `docs/security/control-matrix.md`

- [ ] Track each requested control as planned/implemented/configured/verified.
- [ ] Link evidence: test, workflow run, provider configuration, restore drill, or runtime probe.
- [ ] Block production-security signoff for any critical control lacking evidence.
