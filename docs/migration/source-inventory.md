# UNG-PRESIDENT Source Inventory

Captured from the current Macaly project on 2026-09-13 before migration to Railway.

## Source baseline

- Macaly project: `UNG-PRESIDENT`
- Git branch: `main`
- Current Macaly commit: `3f0f69a`
- Current Macaly tag: `build-29`
- Current Macaly Git history ends at the executive-government implementation.
- The Macaly project is being treated as read-only during migration.

## Security exclusions

The following are intentionally **not** copied into GitHub:

- `.env.local`
- `.macaly/**`
- `.sandbox/**`
- Git internals
- runtime caches
- credentials or deployment secrets

## Application source

### Tests

- `__tests__/app/page.test.tsx`
- `__tests__/executive-government.test.ts`
- `__tests__/presidential-identity.test.tsx`
- `__tests__/rbac.test.ts`
- `__tests__/staff-enrollment-form.test.tsx`
- `__tests__/staff-enrollment-security.test.ts`
- `__tests__/staff-portal.test.tsx`
- `__tests__/staff-security-lifecycle.test.ts`

### Convex backend baseline

- `convex/ResendOTP.ts`
- `convex/auth.config.ts`
- `convex/auth.ts`
- `convex/enrollment.ts`
- `convex/executive.ts`
- `convex/http.ts`
- `convex/macaly.ts`
- `convex/public.ts`
- `convex/schema.ts`
- `convex/staff.ts`
- generated Convex API/type files under `convex/_generated/`

### Public/staff application

- `src/components/convex-client-provider.tsx`
- `src/components/error-boundary.tsx`
- `src/components/executive-government-directory.tsx`
- `src/components/not-found.tsx`
- `src/components/staff-portal.tsx`
- imported UI modules under `src/components/ui/`
- `src/hooks/use-mobile.ts`
- `src/lib/convex.ts`
- `src/lib/executive-government.ts`
- `src/lib/rbac.ts`
- `src/lib/staff-security.ts`
- `src/lib/utils.ts`
- `src/router.tsx`
- `src/routes/__root.tsx`
- `src/routes/admin.tsx`
- `src/routes/index.tsx`
- `src/styles.css`
- generated route tree and metadata

### Configuration/documentation

- `.gitignore`
- `components.json`
- `package.json`
- `package-lock.json`
- `tsconfig.json`
- `vite.config.ts`
- `vitest.config.ts`
- `vitest.setup.ts`
- public manifest/favicon/robots files
- `docs/security/group1-controls.md`
- `docs/security/group2-executive-government.md`
- `docs/superpowers/plans/2026-09-13-presidential-platform-expansion.md`

## Migration note

The actual Macaly Git repository currently contains fewer files than were described in later planning/verification notes. Those later files are not being fabricated during source capture. The migration first preserves the real repository at `build-29`; missing approved expansion work can then be completed on the Railway-hosted codebase with tests and normal review.
