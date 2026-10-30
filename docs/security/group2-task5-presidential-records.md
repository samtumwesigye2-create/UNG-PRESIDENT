# Group 2 Task 5 — Presidential Events, Policies & Regulations

Implemented in source:

- Presidential events classified as Domestic/Home or International/Abroad.
- Event types: State Visit, Public Appearance, Ceremonial Event, Official Meeting, Other.
- Existing legacy public events remain readable; new draft/review/approved events are withheld from the public homepage until published.
- Official document types: Policy, Regulation, Executive Directive, Legislation, Proclamation, Cabinet/Executive Decision, Other.
- Publication workflow: draft → review → approved → published → archived, with controlled backwards transitions where review correction is needed.
- Publishing and archival actions require President or Admin role in the records backend.
- Official document references must be supplied and unique; no official reference values are fabricated by the application.
- Event and document creation/update actions are written to the audit log.
- Public Presidential Diary separates Domestic/Home and International/Abroad events.
- Public Policies & Regulations library exposes only published documents and supports document-type filtering.
- Staff portal includes publishing forms for presidential events and official documents.

Verification on 2026-09-13:

- Task 5 RED tests failed before implementation as expected.
- Presidential records helper tests pass.
- Presidential records staff UI test passes.
- Executive-government, staff-security and RBAC regression tests pass.
- `.sandbox/check-errors` reports zero TypeScript errors and zero Tailwind CSS errors.

Deployment note: Convex schema/function changes remain source-only until the Macaly live-vs-testing deployment safety gate is satisfied. Do not represent the new records backend as live before that deployment succeeds.
