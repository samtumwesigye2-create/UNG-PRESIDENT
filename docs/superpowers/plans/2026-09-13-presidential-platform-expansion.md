# UNG-PRESIDENT Presidential Platform Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand UNG-PRESIDENT into a secure executive-government portal with invitation-only staff enrollment, stronger privileged workflows, executive-office navigation, public events, policies/regulations, and a more usable diplomatic public experience.

**Architecture:** Preserve TanStack Start + Convex and the existing working public/staff application. Split the work into three independently testable groups: (1) staff identity/security, (2) executive-government records/workflows, and (3) public navigation/experience. Authorization is enforced in Convex using authenticated identity and role checks; the browser never supplies trusted roles or user IDs.

**Tech Stack:** TanStack Start, React 19, TypeScript strict, Convex, Convex Auth, Vitest, Testing Library.

**Spec:** Approved requirements from the 2026-09-13 UNG-PRESIDENT redesign/security conversation.

## Global Constraints

- Preserve existing public forms, database-backed records, staff portal, and current RBAC behavior unless explicitly strengthened here.
- Staff self-service enrollment is invitation-only and requires a single-use HR enrollment code tied to an intended identity/role and expiration.
- Collect only personnel fields needed for account matching and administration; do not duplicate highly sensitive HR records.
- Privileged authorization is derived server-side from the authenticated user.
- President/admin remain privileged roles; department-specific access must be least-privilege.
- Sensitive publishing/account actions require an approval/audit path rather than silent destructive replacement.
- Preserve uploaded presidential imagery and diplomatic navy/ivory/gold identity; add black-gold-red footer treatment and controlled flag cropping.
- Do not fabricate official contacts, policies, regulations, events, officeholders, translations, or department content.

---

## Group 1 — Staff Identity, Enrollment & Security

### Task 1: Invitation-only HR enrollment
- [ ] Add failing tests for invalid, expired, already-used, wrong-email, and valid enrollment codes.
- [ ] Extend Convex schema with HR invitations and staff profile fields.
- [ ] Implement server-side code hashing/validation, one-time redemption, expiration and role binding.
- [ ] Build first-time enrollment UI collecting approved personnel profile fields.
- [ ] Verify tests and Convex deployment.

### Task 2: Privileged workflow safeguards
- [ ] Add failing tests for role escalation, suspended accounts, privileged action approval and audit entries.
- [ ] Add staff account lifecycle states: pending, active, suspended, revoked.
- [ ] Add approval records for high-risk publishing/identity operations.
- [ ] Add tamper-resistant application audit events (no ordinary staff delete/update API).
- [ ] Add session/security center UI for staff and HR/admin account lifecycle controls.
- [ ] Verify existing RBAC regression tests.

### Task 3: Authentication hardening boundary
- [ ] Preserve verified email/password auth and reset flow.
- [ ] Add enrollment gating so authentication alone never grants staff portal authorization.
- [ ] Add clear security notices, re-authentication hooks/UX for sensitive actions, and placeholders for stronger MFA/passkey enforcement where platform support is required.
- [ ] Document controls that cannot honestly be claimed until backed by infrastructure (WAF/DDoS/SIEM/hardware-key enforcement).

## Group 2 — Executive Government & Presidential Records

### Task 4: Executive offices and departments
- [ ] Add data models for Vice President office, Prime Minister office and executive departments/ministries.
- [ ] Add mandate/function, leadership, contact/link and publication fields without inventing official data.
- [ ] Add staff CRUD with least-privilege role checks and audit entries.
- [ ] Add public executive-government directory and office pages/sections.

### Task 5: Events, policies and regulations
- [ ] Extend events with domestic/international/state-visit/public-appearance/ceremonial classification.
- [ ] Add policies/regulations/document records with status, issuing office, dates, reference, version and archival state.
- [ ] Add approval/publishing states: draft, review, approved, published, archived.
- [ ] Add public event calendar/list and policies/regulations library with filters.

### Task 6: Authenticity and records lifecycle
- [ ] Add stable public document reference and verification route for published records.
- [ ] Preserve revision history rather than destructive overwrite for official records.
- [ ] Add issued-by/status/last-updated metadata.
- [ ] Add printable/download-ready document presentation; QR can link to verification route when implemented.

## Group 3 — Public Experience, Navigation & Accessibility

### Task 7: Diplomatic visual completion
- [ ] Add black-gold-red footer band.
- [ ] Crop uploaded flag/standard presentation using object-fit/object-position/overflow framing so surrounding black canvas is hidden without modifying source assets.
- [ ] Use executive/presidential seal on staff portal.
- [ ] Preserve formal navy/ivory/gold visual system and responsive behavior.

### Task 8: Navigation and discovery
- [ ] Add responsive mega-menu for Presidency, Executive Government, Records, Policies & Regulations, Newsroom, Events and Public Engagement.
- [ ] Add site-wide search across public records with document-type/year/topic/status filters.
- [ ] Add breadcrumbs and A–Z executive-government directory.
- [ ] Add Government at a Glance panel backed only by published data.

### Task 9: Public-service UX
- [ ] Add categorized subscriptions and calendar/RSS-ready links where supported by actual backend data.
- [ ] Add low-bandwidth-friendly presentation and avoid unnecessary heavy media.
- [ ] Improve keyboard navigation, landmarks, labels, contrast and focus behavior toward WCAG 2.2 AA.
- [ ] Add emergency/public-information banner controlled by authorized staff.
- [ ] Keep FAQ/search assistance constrained to verified Presidency content if/when conversational search is enabled.

## Final Verification

- [ ] Run all unit/component/RBAC/security tests.
- [ ] Run `.sandbox/check-errors` and production build.
- [ ] Run a security review over every Convex function and public endpoint; fix approved findings.
- [ ] Deploy Convex changes.
- [ ] Inspect live preview for desktop/mobile navigation and flag cropping.
- [ ] Publish only after fresh verification passes.
