# UNG-PRESIDENT Image Fix and Staging Design

## Goal
Integrate the fixed Presidential/VP/national-symbol artwork from `ung president 3.pdf` into the existing UNG-PRESIDENT application without duplicating business workflows or creating a second production system.

## Architecture
Keep the existing TanStack/React application and current domain model. Add repository-owned embedded image assets as data URIs, replace all Macaly-hosted image references, and render the Presidential seal, Presidential Standard, Vice Presidential seal, and national flag using deterministic containers rather than remote crops. The test deployment uses a separate Railway service from the same GitHub branch so production remains untouched.

## Image source of truth
The uploaded fixed build embeds `PRES_SEAL_B64`, `VP_SEAL_B64`, and `NAT_FLAG_B64` and explicitly describes the seals as cropped/masked circular artwork. Those assets become the visual source of truth for this staging build.

## Non-duplication rules
- Do not create duplicate executive-order, appointment, honours, event, petition, visit, state-visit, press, audit, or staff-domain tables.
- Do not add a second authentication stack.
- Do not replace the current React/TanStack application with the uploaded FastAPI application.
- Reuse the current components and routes; only replace image sourcing/placement and remove Macaly runtime dependencies.

## Implementation
- Add `src/lib/presidential-assets.ts` containing data-URI constants for the three fixed embedded assets.
- Update the homepage to import those assets and use them in the existing identity locations.
- Update the staff portal to use the repository-owned Presidential seal.
- Update the VP component to use the repository-owned Vice Presidential seal instead of remote artwork.
- Remove `@macaly/bridge` and `@macaly/static-tagger` from package metadata because Macaly is not permitted in this project.
- Add regression tests asserting no `macaly-user-data.dev` references remain in the visual code and that the fixed embedded assets are wired into the correct identity roles.

## Testing and deployment
Run the existing Vitest suite and production build. Deploy branch `test/president-image-fix` as a new Railway staging service with its own Railway-generated URL. Do not modify the existing production service/domain during acceptance testing.
