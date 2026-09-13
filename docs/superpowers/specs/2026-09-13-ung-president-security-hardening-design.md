# UNG-PRESIDENT Security Hardening Design

**Date:** 2026-09-13

## Purpose

Harden the Railway-hosted UNG-PRESIDENT platform with defense-in-depth controls spanning the public edge, application, identity, data, monitoring, backup/recovery, and vulnerability reporting. The design preserves the current application and migration work while preventing unsupported infrastructure controls from being represented as active until they are actually configured and verified.

## Security Architecture

Traffic flow:

`Public Internet -> Cloudflare Edge -> Railway UNG-PRESIDENT web service -> PostgreSQL`

Cloudflare is the intended public edge for CDN delivery, DDoS mitigation, WAF, rate limiting, DNS controls, TLS enforcement, and origin shielding. Railway remains the application host. PostgreSQL remains private to the application environment and must not be exposed publicly.

The application must enforce its own security controls independently of the edge. Cloudflare is not treated as a substitute for secure application code.

## 1. Network and Infrastructure Defenses

### 1.1 DDoS Mitigation

- Place the public website behind Cloudflare before production domain cutover.
- Enable CDN/proxying for public DNS records.
- Enable Cloudflare-managed DDoS protection appropriate to the selected plan.
- Enable rate limiting for login, enrollment, password reset, public forms, and other abuse-prone endpoints.
- Validate that the Railway origin remains reachable only through the intended public path as far as Railway and Cloudflare capabilities permit.
- Record the exact Cloudflare plan/features in the security inventory before marking DDoS protection as active.

### 1.2 Web Application Firewall

- Enable Cloudflare managed WAF rulesets where the selected plan supports them.
- Add narrowly scoped custom WAF/rate rules for:
  - `/admin`
  - authentication endpoints
  - enrollment/invitation endpoints
  - password-reset endpoints
  - contact/visit/newsletter submission endpoints
- Do not rely on WAF rules as the only defense against SQL injection, XSS, or request tampering.
- Application queries must use parameterized database access only.
- User-controlled output must remain escaped by default; unsafe HTML rendering is prohibited unless content is sanitized and specifically reviewed.

### 1.3 Origin IP / Origin Exposure Reduction

- Cloudflare-proxy all public application DNS records.
- Do not publish Railway service endpoints as official public links after domain cutover.
- Restrict direct-origin access where supported by Railway/Cloudflare configuration.
- If full origin allowlisting is not technically available, document that limitation explicitly and use alternate controls such as secret-origin headers only if they can be enforced safely.
- Never claim the origin is fully masked unless direct access testing confirms it.

## 2. Data and Communication Security

### 2.1 HTTPS and HSTS

- Enforce HTTPS on the public domain.
- Redirect HTTP to HTTPS.
- Add `Strict-Transport-Security` only after HTTPS is stable on the production domain.
- Initial HSTS policy: `max-age=31536000; includeSubDomains` after validation.
- Add `preload` only after confirming all subdomains satisfy preload requirements and the domain owner explicitly accepts the operational consequences.
- Do not submit for HSTS preload during initial deployment without that confirmation.

### 2.2 Security Headers

Application responses should set, where compatible:

- `Content-Security-Policy`
- `Strict-Transport-Security`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy`
- `Permissions-Policy`
- clickjacking protection through CSP `frame-ancestors` and/or `X-Frame-Options`
- secure cache directives for authenticated and sensitive responses

CSP must be tested against actual images, scripts, fonts, and API endpoints before enforcement. Start with a strict baseline and explicitly permit only required origins.

### 2.3 DNSSEC

- Enable DNSSEC at the authoritative DNS provider if supported for the production domain.
- Verify the DS record chain before marking DNSSEC active.
- Treat DNSSEC as a domain infrastructure control, not an application feature.

### 2.4 Official Government Domain

- The platform may use a restrictive government-controlled TLD only if the appropriate government authority has approved and issued it.
- The application must not claim `.gov`, `.mil`, or equivalent status unless the actual deployed domain qualifies.
- Domain eligibility is an external governance requirement and is not implemented by code.

## 3. Access Control and Identity Management

### 3.1 Zero-Trust Principles

- Every staff request must be authenticated and authorized server-side.
- No role, account status, department, or privilege assertion from the browser is trusted by itself.
- Staff accounts default to no access until enrollment and activation are complete.
- Suspended/revoked accounts must be denied immediately on the server.
- High-risk operations must require explicit reauthorization or approval as defined below.

### 3.2 Multi-Factor Authentication

Target state:

- MFA is mandatory for all staff accounts.
- Privileged roles (`president`, `admin`) require phishing-resistant MFA where the chosen identity stack supports it, preferably WebAuthn/passkeys or hardware security keys.
- Recovery methods must not weaken privileged accounts to email-only recovery without compensating controls.
- Current password/OTP mechanisms are transitional and must not be described as hardware-backed MFA.
- If PIV/smart-card infrastructure is unavailable, do not claim PIV support.

### 3.3 RBAC and Least Privilege

Preserve and strengthen the existing roles:

- `president`
- `admin`
- `staff`
- `protocol`
- `press`

Authorization must be enforced on the server for every protected read/write action. Publication, role changes, account lifecycle operations, executive-government records, and other sensitive operations must not depend only on hidden UI controls.

### 3.4 High-Risk Dual Approval

Dual approval is required for high-risk operations, including at minimum:

- privileged role changes
- account reactivation/revocation where policy requires
- publication of executive-office/department records
- publication of official presidential documents
- emergency/public-information notices

Rules:

- requester cannot approve their own request
- approval must bind to the exact action and target record
- approval must be single-use and consumed at execution
- request, review, execution, and rejection must all be auditable

The existing approval queue does not yet satisfy this requirement until execution is bound to and consumes an approval record.

## 4. Application Security

### 4.1 Input and Database Safety

- Use parameterized PostgreSQL queries or a library that guarantees parameterization.
- Validate all public and staff mutation inputs server-side.
- Enforce length, format, and enum constraints before persistence.
- Reject unexpected fields for privileged operations.
- Do not interpolate user data into SQL, command lines, file paths, templates, or redirects.

### 4.2 XSS and Content Safety

- Avoid `dangerouslySetInnerHTML` for user/editor-controlled content.
- Any required HTML content must pass a reviewed sanitizer with an explicit allowlist.
- CSP must restrict script and frame execution.
- Public records should default to plain text/structured rendering.

### 4.3 Session Security

For the Railway authentication implementation:

- use `HttpOnly` cookies
- use `Secure` cookies in production
- use appropriate `SameSite` policy
- rotate session identifiers after authentication and privilege changes
- expire inactive sessions
- allow server-side revocation
- require stronger confirmation for sensitive operations
- protect state-changing routes from CSRF

### 4.4 Secrets

- Store secrets only in Railway/approved secret management, never GitHub source.
- Never log passwords, enrollment codes, session tokens, reset tokens, or database credentials.
- Enrollment invitation codes are stored only as cryptographic hashes.
- Rotate any credential exposed during migration or testing.

## 5. Continuous Monitoring and Maintenance

### 5.1 Automated Vulnerability Scanning

Required automated checks:

- dependency vulnerability scanning on every pull request and scheduled basis
- lockfile/dependency review
- static security checks
- secret scanning
- build/test verification
- container/deployment dependency checks where supported

Known vulnerable dependencies must block production deployment according to defined severity policy unless an explicit documented exception is approved.

### 5.2 Logging and Alerting

Record security-relevant events including:

- login success/failure
- MFA/recovery events
- invitation issuance/use/revocation
- role/status changes
- privileged approval request/review/execution
- publication/archive actions
- repeated rejected requests/rate-limit events where available

Do not collect surveillance data unrelated to application security or operations.

### 5.3 Patch Management

- Keep Node.js and runtime dependencies on supported versions.
- Apply security patches promptly after validation.
- Run the test suite and security checks before production deployment.
- Track exceptions with owner, reason, compensating control, and expiry date.

## 6. Backup and Recovery

### 6.1 Database Backups

Target state:

- automated PostgreSQL backups
- retention policy appropriate for presidential records and operational recovery
- at least one backup copy outside the primary application failure domain
- restricted backup credentials/access
- routine restoration testing

### 6.2 Immutable / Off-Site Backups

The requirement is to maintain a backup copy that application administrators and compromised application credentials cannot silently alter or delete.

Possible implementation methods include provider-native immutable backups, object-lock retention, or a separate controlled backup account. The exact mechanism must be chosen based on available Railway/database/storage capabilities.

Do not describe backups as air-gapped or immutable unless the deployed mechanism actually provides those properties and restoration has been tested.

### 6.3 Recovery Evidence

At least one documented restore test must verify:

- database restoration
- critical application records
- staff identity/authorization integrity
- uploaded presidential media availability
- audit-log preservation

## 7. Vulnerability Disclosure Program

Provide an official Vulnerability Disclosure Policy page or linked policy containing:

- authorized testing scope
- prohibited testing categories
- safe-harbor language approved by the responsible authority
- secure reporting channel
- expected acknowledgment process
- instructions for protecting sensitive findings

A reporting dashboard or ticketing system may be added only when an approved secure reporting backend/provider is connected. Until then, the public site must not fabricate an official security email or reporting address.

## 8. Verification and Status Model

Each security control must be tracked as one of:

- `implemented` — code/config exists but may not yet be deployed
- `deployed` — present in the target environment
- `verified` — independently tested and confirmed working
- `pending_external` — requires provider/domain/government action
- `not_supported` — current infrastructure cannot provide the control

Public/internal security documentation must not label a control active merely because it appears in this design.

## 9. Acceptance Criteria

UNG-PRESIDENT is security-ready for production cutover only when all critical items below are either verified or explicitly accepted as pending external dependencies:

1. Public production traffic is proxied through Cloudflare.
2. HTTPS is enforced end-to-end for public traffic.
3. WAF/DDoS/rate controls are enabled and tested where plan support exists.
4. Direct Railway origin exposure has been reduced and tested to the maximum supported level.
5. HSTS is deployed after domain validation; preload remains separate approval.
6. DNSSEC is verified if the chosen authoritative DNS supports it.
7. Server-side RBAC protects every privileged operation.
8. MFA is required for staff; privileged users use phishing-resistant MFA when technically available.
9. High-risk actions use real execution-bound dual approval.
10. Session and CSRF defenses pass security tests.
11. PostgreSQL access is parameterized and private.
12. Security headers and CSP pass browser/application tests.
13. Dependency, secret, and static security scanning run automatically.
14. Security-relevant audit events are retained.
15. Backup/recovery mechanism is documented and at least one restore has been successfully tested.
16. VDP content exists without fabricated contact information.
17. No unsupported capability is represented as active.

## 10. Source Requirements Incorporated

This design incorporates the requested controls and terminology from the user-provided references and requirements, including DDoS mitigation, WAF, origin masking, HTTPS/HSTS, DNSSEC, restrictive official domains, zero-trust, MFA, RBAC/least privilege, vulnerability scanning, immutable/off-site backup expectations, and a Vulnerability Disclosure Policy.

The design deliberately separates provider/domain controls from application controls so that infrastructure features are only marked active after deployment and verification.
