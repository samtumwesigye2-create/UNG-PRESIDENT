# UNG-PRESIDENT Security Control Status

Security controls are tracked using these states: `implemented`, `deployed`, `verified`, `pending_external`, and `not_supported`.

## Current baseline

| Control | Status | Notes |
| --- | --- | --- |
| Application security-header policy | implemented | Source policy exists; deployment verification still required. |
| Cloudflare DDoS mitigation | pending_external | Requires production-domain Cloudflare configuration and testing. |
| Cloudflare WAF | pending_external | Requires managed/custom rules and testing. |
| Origin exposure reduction | pending_external | Requires Railway/Cloudflare controls plus direct-origin testing. |
| HTTPS enforcement | pending_external | Requires final production-domain validation. |
| HSTS | pending_external | Enable only after HTTPS is stable. |
| HSTS preload | pending_external | Requires separate owner approval and eligibility checks. |
| DNSSEC | pending_external | Requires authoritative DNS configuration and DS validation. |
| Phishing-resistant privileged MFA | pending_external | Requires WebAuthn/passkey or hardware-key capable identity infrastructure. |
| Immutable/off-site backup | pending_external | Requires deletion-protected backup outside the primary failure domain and restore testing. |

A control must not be described as active merely because its implementation appears in source or documentation.
