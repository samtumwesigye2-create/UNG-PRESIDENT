export type SecurityControlStatus =
  | 'implemented'
  | 'deployed'
  | 'verified'
  | 'pending_external'
  | 'not_supported'

export type SecurityControlRecord = {
  status: SecurityControlStatus
  summary: string
}

export const SECURITY_CONTROLS = {
  applicationHeaders: {
    status: 'implemented',
    summary: 'Application security-header policy is implemented in source and still requires deployment verification.',
  },
  cloudflareDdos: {
    status: 'pending_external',
    summary: 'Requires Cloudflare edge configuration and verification on the production domain.',
  },
  cloudflareWaf: {
    status: 'pending_external',
    summary: 'Requires Cloudflare managed/custom WAF configuration and verification.',
  },
  originExposureReduction: {
    status: 'pending_external',
    summary: 'Requires Cloudflare/Railway origin-access controls and direct-origin testing.',
  },
  httpsEnforcement: {
    status: 'pending_external',
    summary: 'Requires validation on the final production domain and edge path.',
  },
  hsts: {
    status: 'pending_external',
    summary: 'Must only be enabled after production HTTPS is stable.',
  },
  hstsPreload: {
    status: 'pending_external',
    summary: 'Requires separate domain-owner approval and preload eligibility verification.',
  },
  dnssec: {
    status: 'pending_external',
    summary: 'Requires authoritative DNS-provider configuration and DS-chain verification.',
  },
  phishingResistantMfa: {
    status: 'pending_external',
    summary: 'Requires WebAuthn/passkey or hardware-key capable identity infrastructure.',
  },
  immutableBackup: {
    status: 'pending_external',
    summary: 'Requires a deletion-protected backup outside the primary application failure domain plus restore testing.',
  },
} as const satisfies Record<string, SecurityControlRecord>
