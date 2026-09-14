import { describe, expect, it } from 'vitest'
import { buildSecurityHeaders } from '../src/security/headers'
import { SECURITY_CONTROLS } from '../src/security/control-status'

describe('UNG-PRESIDENT security headers', () => {
  it('builds a strict baseline without HSTS before production validation', () => {
    const headers = buildSecurityHeaders({
      production: false,
      hstsEnabled: false,
      connectSrc: ['https://perceptive-mammoth-601.eu-west-1.convex.cloud', 'wss://perceptive-mammoth-601.eu-west-1.convex.cloud'],
      imageSrc: ['https://assets.macaly-user-data.dev'],
    })

    expect(headers['Content-Security-Policy']).toContain("default-src 'self'")
    expect(headers['Content-Security-Policy']).toContain("script-src 'self'")
    expect(headers['Content-Security-Policy']).toContain("frame-ancestors 'none'")
    expect(headers['Content-Security-Policy']).not.toContain("script-src *")
    expect(headers['X-Content-Type-Options']).toBe('nosniff')
    expect(headers['Referrer-Policy']).toBe('strict-origin-when-cross-origin')
    expect(headers['Permissions-Policy']).toContain('camera=()')
    expect(headers['X-Frame-Options']).toBe('DENY')
    expect(headers['Cache-Control']).toBe('no-store')
    expect(headers['Strict-Transport-Security']).toBeUndefined()
  })

  it('adds the approved one-year HSTS policy only when explicitly enabled in production', () => {
    const headers = buildSecurityHeaders({ production: true, hstsEnabled: true })
    expect(headers['Strict-Transport-Security']).toBe('max-age=31536000; includeSubDomains')
    expect(headers['Strict-Transport-Security']).not.toContain('preload')
  })
})

describe('security control status registry', () => {
  it('does not claim external controls are active before verification', () => {
    expect(SECURITY_CONTROLS.cloudflareDdos.status).toBe('pending_external')
    expect(SECURITY_CONTROLS.cloudflareWaf.status).toBe('pending_external')
    expect(SECURITY_CONTROLS.dnssec.status).toBe('pending_external')
    expect(SECURITY_CONTROLS.hstsPreload.status).toBe('pending_external')
    expect(SECURITY_CONTROLS.immutableBackup.status).toBe('pending_external')
    expect(SECURITY_CONTROLS.phishingResistantMfa.status).toBe('pending_external')
  })
})
