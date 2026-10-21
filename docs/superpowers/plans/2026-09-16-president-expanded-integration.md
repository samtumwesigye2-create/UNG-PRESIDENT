# UNG-PRESIDENT Expanded Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the expanded PRESIDENT administrative functions into the current working production application without regressing authentication, enrollment, password reset, persistence, or Railway startup.

**Architecture:** Current `main` is the production base. Recover expanded functionality from `codex/finish-ung-president` and the supplied PRESIDENT additions into focused modules registered on the existing FastAPI app, with additive SQLite schema and authenticated admin UI. Historical code is ported selectively rather than replacing current production files.

**Tech Stack:** Python 3.12, FastAPI, SQLite, pytest, Docker, Railway.

**Spec:** `docs/superpowers/specs/2026-09-16-president-expanded-integration-design.md`

## Global Constraints

- Preserve current HR-code registration and admin login behavior.
- Preserve password reset and SMTP/Resend behavior.
- Preserve `UNG_PRESIDENT_DB_PATH` and the Railway persistent volume.
- Keep `bootstrap.py` as the production startup path.
- Schema changes are additive; never delete existing production tables/data.
- Every visible admin function must have a working authenticated route and persistence/action behind it.
- Dual-control actions cannot be approved by the same user who initiated them.
- Existing regression tests must remain green before production deployment.

---

### Task 1: Establish integration branch and regression boundary

**Files:**
- Test: `tests/test_app.py`
- Test: `tests/test_password_reset.py`
- Test: `tests/test_expanded_admin.py`

**Interfaces:**
- Consumes: current `main` FastAPI app and authentication/session helpers.
- Produces: regression tests defining required expanded dashboard/navigation and protected route behavior.

- [ ] **Step 1:** Create an integration branch from the current `main` commit.
- [ ] **Step 2:** Add failing tests asserting an authenticated admin can see links for Citizens Abroad, Travel Advisories, Emergency Alerts, Missions, Consular Queue, Media Accreditation, Attestation, Treaties/Archive, Approvals, and Biometrics.
- [ ] **Step 3:** Add failing tests asserting anonymous access to expanded `/admin/*` routes is rejected.
- [ ] **Step 4:** Run the focused tests and confirm the new assertions fail while existing auth tests remain green.
- [ ] **Step 5:** Commit the regression boundary.

### Task 2: Add expanded persistent data schema

**Files:**
- Create: `president_expanded_data.py`
- Test: `tests/test_expanded_data.py`

**Interfaces:**
- Consumes: `core.db_cursor()` and `core.DB_PATH`.
- Produces: `init_expanded_schema()` creating additive tables for `citizens_abroad`, `travel_advisories`, `emergency_alerts`, `diplomatic_missions`, `consular_cases`, `media_accreditations`, `document_attestations`, `treaty_archive`, `approval_requests`, and `biometric_enrollments`.

- [ ] **Step 1:** Write tests that initialize the current core schema, call `init_expanded_schema()`, and assert all expanded tables exist without removing current tables.
- [ ] **Step 2:** Run the data tests and confirm failure because the module/schema does not yet exist.
- [ ] **Step 3:** Implement `init_expanded_schema()` using `CREATE TABLE IF NOT EXISTS` and foreign-key/reference fields where appropriate.
- [ ] **Step 4:** Run expanded data tests plus existing app tests and confirm they pass.
- [ ] **Step 5:** Commit the additive schema.

### Task 3: Integrate operational expanded admin routes

**Files:**
- Create: `president_expanded_admin.py`
- Modify: `bootstrap.py`
- Test: `tests/test_expanded_admin.py`

**Interfaces:**
- Consumes: existing `core.app`, `core.db_cursor`, session/admin authorization helpers, and `init_expanded_schema()`.
- Produces: authenticated list/create/update routes under `/admin/citizens-abroad`, `/admin/travel-advisories`, `/admin/emergency-alerts`, `/admin/missions`, `/admin/consular`, `/admin/media-accreditation`, `/admin/attestations`, `/admin/treaties`, `/admin/approvals`, and `/admin/biometrics`.

- [ ] **Step 1:** Extend failing route tests to cover GET pages and representative POST persistence for every module.
- [ ] **Step 2:** Run focused tests and confirm route-not-found/authorization failures.
- [ ] **Step 3:** Implement the module using the existing app's authorization conventions and parameterized SQL only.
- [ ] **Step 4:** Import/register the expanded module from `bootstrap.py` after core initialization and before Uvicorn starts.
- [ ] **Step 5:** Run focused tests and full suite; confirm all pass.
- [ ] **Step 6:** Commit operational expanded routes.

### Task 4: Implement dual-control and audit rules

**Files:**
- Modify: `president_expanded_admin.py`
- Test: `tests/test_expanded_approvals.py`

**Interfaces:**
- Consumes: `approval_requests` and existing authenticated user identity/audit facilities.
- Produces: create/approve/reject workflow where `initiator_user_id != approver_user_id`, with state transitions `pending -> approved|rejected` and audit entries.

- [ ] **Step 1:** Write tests proving a user cannot approve their own request, another authorized admin can approve it, and completed requests cannot be approved twice.
- [ ] **Step 2:** Run tests and confirm failure.
- [ ] **Step 3:** Implement the minimal state-transition and audit logic.
- [ ] **Step 4:** Run approval tests and full suite; confirm all pass.
- [ ] **Step 5:** Commit dual-control enforcement.

### Task 5: Expose expanded functions in the working dashboard

**Files:**
- Create: `president_dashboard_expanded.py`
- Modify: `bootstrap.py`
- Test: `tests/test_expanded_dashboard.py`

**Interfaces:**
- Consumes: current `/admin` authentication/session behavior and expanded route paths.
- Produces: expanded authenticated dashboard/navigation while preserving current dashboard functions.

- [ ] **Step 1:** Write tests asserting the current dashboard functions remain present and all expanded function labels/URLs are rendered for an admin.
- [ ] **Step 2:** Run tests and confirm expanded labels are absent.
- [ ] **Step 3:** Register an expanded dashboard renderer that preserves the current cards and adds the new operational modules without exposing admin controls publicly.
- [ ] **Step 4:** Run dashboard tests and full suite; confirm all pass.
- [ ] **Step 5:** Commit dashboard integration.

### Task 6: Recover and connect biometric enrollment capability

**Files:**
- Modify: `president_expanded_admin.py`
- Test: `tests/test_biometric_enrollment.py`

**Interfaces:**
- Consumes: `biometric_enrollments`, authenticated staff/user records, and recovered enrollment contract from prior PRESIDENT work.
- Produces: authenticated enrollment metadata/status API without storing raw biometric images/templates unless the recovered approved design explicitly requires it.

- [ ] **Step 1:** Recover the prior biometric endpoint/field contract from repository history/source material and encode it in failing tests.
- [ ] **Step 2:** Confirm the tests fail against the current build.
- [ ] **Step 3:** Implement the recovered contract using the expanded schema and current authorization model.
- [ ] **Step 4:** Run biometric tests and full suite; confirm all pass.
- [ ] **Step 5:** Commit biometric integration.

### Task 7: Production verification and deployment

**Files:**
- Modify only if tests expose a production packaging issue: `Dockerfile`, `bootstrap.py`, `requirements.txt`.

**Interfaces:**
- Consumes: verified integration branch.
- Produces: production `main` and healthy Railway deployment.

- [ ] **Step 1:** Run the complete pytest suite and require zero failures.
- [ ] **Step 2:** Verify Dockerfile copies every imported production module into `/app`.
- [ ] **Step 3:** Verify the integration branch contains all current `main` auth/password-reset/persistence commits.
- [ ] **Step 4:** Fast-forward/merge the verified integration result to `main` without force-resetting production history.
- [ ] **Step 5:** Wait for Railway deployment and verify status `SUCCESS`, application startup complete, and no import/schema exceptions.
- [ ] **Step 6:** Verify HTTP behavior for `/admin/login`, authenticated `/admin`, and representative expanded module routes.
- [ ] **Step 7:** Confirm the expanded dashboard is the production UI and report the deployed commit/deployment IDs.