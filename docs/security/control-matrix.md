# UNG-PRESIDENT Security Control Matrix

Status meanings:
- **Planned** — requirement accepted but implementation/configuration not complete.
- **Implemented** — application/repository support exists but external configuration may still be required.
- **Configured** — provider/system setting has been applied.
- **Verified** — evidence proves the control works in the target environment.

| Control | Status | Evidence / next gate |
|---|---|---|
| DDoS mitigation / enterprise edge CDN | Planned | Requires approved edge provider in front of Railway and traffic verification. |
| Managed WAF for SQLi/XSS/common exploits | Planned | Requires edge provider configuration and test evidence. |
| Origin shielding / direct-origin restriction | Planned | Requires edge routing plus an origin-restriction mechanism; do not claim masking from DNS alone. |
| HTTPS-only transport | Implemented | Application redirect logic added for requests positively identified as HTTP; production edge verification still required. |
| HSTS | Implemented | `max-age=31536000; includeSubDomains`; preload intentionally withheld until all covered subdomains are validated. |
| Browser security headers / CSP | Implemented | Security header policy and Nitro middleware; security-header unit tests pass in CI. |
| DNSSEC | Planned | Must be enabled at the authoritative DNS provider and DS chain validated. |
| Restricted official government TLD | Planned | Requires an authorized official government domain; no domain is fabricated. |
| Zero-trust server authorization | Partially implemented | Existing RBAC/account-state model exists; Railway/Postgres auth migration must preserve server-side checks. |
| Phishing-resistant MFA for privileged staff | Planned | WebAuthn/passkey/hardware-key enforcement required after Railway auth migration. PIV requires compatible identity provider. |
| Least-privilege RBAC | Implemented in current application model | Roles exist and privileged operations are server-authorized; migration acceptance must re-verify. |
| Automated dependency scanning | Implemented | Dependabot configuration and `npm audit` workflow added. |
| Static code security scanning | Implemented | CodeQL workflow added; GitHub Actions result required before `Verified`. |
| Runtime/security monitoring | Planned | Requires production telemetry/log-alert configuration on Railway/edge provider. |
| Automated database backup | Planned | Configure after Railway PostgreSQL service is established. |
| Immutable/off-site backup | Planned | Requires separate retention-locked destination and restore drill. |
| Restore testing | Planned | Must restore into isolated database and reconcile counts/checksums. |
| Vulnerability Disclosure Policy | Planned | Public VDP page and verified reporting channel still required. |
| `/.well-known/security.txt` | Planned | Must wait for approved security contact/reporting endpoint. |
| Researcher secure intake dashboard | Planned | Requires case-management/reporting implementation; no placeholder endpoint will be published. |

## Current rule
No row may be promoted to **Verified** without concrete evidence such as a passing test/workflow, runtime probe, provider configuration record, DNS validation, or restore drill.
