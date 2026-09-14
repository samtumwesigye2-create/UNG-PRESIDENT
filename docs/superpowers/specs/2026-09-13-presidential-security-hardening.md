# UNG-PRESIDENT Security Hardening Specification

## Goal
Protect UNG-PRESIDENT as a high-sensitivity public government platform using layered network, application, identity, monitoring, recovery, and disclosure controls.

## Security Layers

### 1. Network & Infrastructure Defenses
- DDoS mitigation through an enterprise edge/CDN and traffic-scrubbing provider in front of the Railway origin.
- Web Application Firewall rules for common web exploits including SQL injection and XSS patterns.
- Origin IP/hostname shielding so normal public traffic reaches the application through the approved reverse proxy/edge only.
- Direct-origin exposure must not be described as protected until an origin-restriction mechanism is actually active and tested.

### 2. Data & Communication Security
- HTTPS-only public access.
- HTTP Strict Transport Security (HSTS) with a long max-age, includeSubDomains, and preload only after every production subdomain is confirmed HTTPS-safe.
- Strong browser security headers including Content-Security-Policy, X-Content-Type-Options, Referrer-Policy, frame protection, and Permissions-Policy.
- DNSSEC on the production DNS zone before the control is marked active.
- Government-restricted TLD/domain use when an authorized official domain is available; no fabricated government domain may be used.

### 3. Access Control & Identity Management
- Zero-trust posture: authentication is not authorization; every privileged server operation re-evaluates account state and role.
- Staff portal must enforce least-privilege RBAC.
- Privileged administrators must use phishing-resistant MFA (WebAuthn/passkey/hardware security key; PIV-compatible federation where later available) before the control is marked complete.
- No default passwords, plaintext enrollment secrets, or client-trusted role claims.
- High-risk publication and account-security actions should support dual approval and an immutable audit trail.

### 4. Continuous Monitoring & Maintenance
- Automated dependency vulnerability scanning.
- Static code/security scanning on pull requests and the default branch.
- Dependency update automation.
- Security-relevant audit events and deployment/runtime monitoring.
- No monitoring claim may imply infrastructure telemetry that has not actually been connected.

### 5. Recovery
- Automated database backups with retention and restore testing.
- At least one logically separate/off-site backup copy for critical records.
- Backup immutability/air-gap claims require verified provider configuration and a successful restore drill; they are not satisfied by source-control history alone.

### 6. Vulnerability Disclosure
- Publish a standards-compatible `/.well-known/security.txt` only after an approved security contact and reporting channel are supplied.
- Provide a public Vulnerability Disclosure Policy page describing safe-harbor scope, prohibited testing, response expectations, and the verified reporting channel.
- A future secure researcher intake dashboard may be added, but no fake contact address or unsupported case-management workflow may be published.

## Current Migration Constraint
Railway is the target application host. The existing Macaly deployment remains untouched only as a temporary fallback until the Railway replacement passes acceptance testing. Security controls that depend on an external edge/DNS provider are tracked separately from application controls and must be verified before being reported as active.

## Acceptance Principle
A security feature is classified as one of: `implemented`, `configured`, `verified`, or `planned`. Public or internal readiness reports must not collapse those states into a generic claim that the feature is active.
