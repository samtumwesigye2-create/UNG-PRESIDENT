# UNG-PRESIDENT Group 1 Staff Security Controls

## Implemented in source

- Invitation-only first-time staff enrollment using HR/security-issued single-use codes.
- Enrollment codes are hashed before storage and bound to an authorized email, intended role, expiration and optional employee/office/department metadata.
- Verified authentication email must match the HR-authorized identity.
- Enrollment creates a pending, disabled profile; authentication alone does not grant staff access.
- Staff account lifecycle states: pending, active, suspended, revoked.
- Controlled status transitions prevent revoked accounts from returning to service and block privileged users from casually disabling their own access.
- New staff creation through the old direct profile path is blocked; HR invitation flow is required.
- Role changes are blocked from the direct profile editor and reserved for privileged approval workflow.
- Privileged approvals require a different reviewer from the requester.
- Enrollment issuance, enrollment submission, staff lifecycle changes and approval decisions are written to the audit log.
- Staff portal includes the executive seal, security notice, enrollment form, HR invitation issuance, account lifecycle controls and privileged approval review.

## Security boundaries not yet claimed as active

The application does not claim the following controls are active until the supporting infrastructure is connected and verified: passkeys/hardware security keys, external SIEM, WAF/DDoS controls, immutable off-platform audit storage, device posture enforcement, automated risk scoring, disaster-recovery failover, and external secrets rotation.

## Deployment state

Source and tests are prepared, but the new Convex schema/functions require the platform's Testing-vs-Live deployment authorization before backend activation. Until that gate is cleared, the production backend remains unchanged.
