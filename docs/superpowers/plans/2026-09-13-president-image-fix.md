# UNG-PRESIDENT Image Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all Macaly-hosted presidential identity imagery with the fixed embedded assets from `ung president 3.pdf`, preserve existing business functions, and deploy a separate Railway staging URL for visual testing.

**Architecture:** Keep the existing TanStack/React codebase and domain model. Add one focused asset module, wire existing components to it, remove Macaly package dependencies, add regression tests, then deploy the test branch to a new Railway service.

**Tech Stack:** React 19, TanStack Start, TypeScript, Vite, Vitest, Railway.

**Spec:** `docs/superpowers/specs/2026-09-13-president-image-fix-design.md`

## Global Constraints
- No Macaly hosting, runtime libraries, asset URLs, or fallback.
- Do not duplicate current UNG-PRESIDENT business/domain features.
- Preserve the existing production Railway service during staging acceptance.
- Use the Presidential/VP/national-symbol assets embedded in `ung president 3.pdf` as the visual source of truth.

---

### Task 1: Regression tests for image ownership and role mapping

**Files:**
- Create: `__tests__/presidential-image-ownership.test.ts`

**Interfaces:**
- Consumes: current source files as text.
- Produces: regression assertions that fail while remote Macaly URLs remain and pass after local asset wiring.

- [ ] Write tests asserting `src/routes/index.tsx`, `src/components/staff-portal.tsx`, and `src/components/vice-president-seal.tsx` contain no `macaly-user-data.dev` references.
- [ ] Assert homepage imports `PRESIDENTIAL_SEAL_DATA_URI` and `NATIONAL_FLAG_DATA_URI` and VP component imports `VICE_PRESIDENTIAL_SEAL_DATA_URI`.
- [ ] Run `npm test -- presidential-image-ownership` and confirm RED before production edits.

### Task 2: Repository-owned presidential identity assets

**Files:**
- Create: `src/lib/presidential-assets.ts`
- Modify: `src/routes/index.tsx`
- Modify: `src/components/staff-portal.tsx`
- Modify: `src/components/vice-president-seal.tsx`

**Interfaces:**
- Produces: `PRESIDENTIAL_SEAL_DATA_URI`, `VICE_PRESIDENTIAL_SEAL_DATA_URI`, `NATIONAL_FLAG_DATA_URI`.

- [ ] Add the three fixed PNG assets as `data:image/png;base64,...` constants.
- [ ] Replace homepage remote identity URLs with the new constants without changing business-data queries or forms.
- [ ] Replace staff portal seal URL with `PRESIDENTIAL_SEAL_DATA_URI`.
- [ ] Replace VP seal artwork with `VICE_PRESIDENTIAL_SEAL_DATA_URI` and render it with deterministic `object-fit: contain`/circular framing.
- [ ] Run the focused test and confirm GREEN.

### Task 3: Remove Macaly package dependencies

**Files:**
- Modify: `package.json`

**Interfaces:**
- Produces: package metadata with no `@macaly/*` dependency.

- [ ] Remove `@macaly/bridge` from dependencies and `@macaly/static-tagger` from devDependencies.
- [ ] Run the full test suite.
- [ ] Run `npm run build` and confirm a clean production build.

### Task 4: Railway staging deployment

**Files:** none

**Interfaces:**
- Consumes: GitHub branch `test/president-image-fix`.
- Produces: separate Railway staging service + Railway-generated URL.

- [ ] Create a new Railway service from `samtumwesigye2-create/UNG-PRESIDENT`, branch `test/president-image-fix`.
- [ ] Copy only required non-secret runtime variables from the current web service as needed for the staging build.
- [ ] Wait for deployment `SUCCESS`.
- [ ] Generate a Railway domain for the staging service.
- [ ] Verify the staging URL responds and inspect deployment logs for runtime crashes before giving the URL to the user.
