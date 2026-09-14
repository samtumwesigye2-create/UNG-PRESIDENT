import { describe, expect, it } from 'vitest'
import { buildSecurityHeaders, shouldRedirectToHttps } from '../src/server/security/headers'

describe('presidential security headers', () => {
  it('enforces strict transport and browser isolation headers', () => {
    const headers = buildSecurityHeaders({ production: true })

    expect(headers['Strict-Transport-Security']).toBe('max-age=31536000; includeSubDomains')
    expect(headers['X-Content-Type-Options']).toBe('nosniff')
    expect(headers['X-Frame-Options']).toBe('DENY')
    expect(headers['Referrer-Policy']).toBe('strict-origin-when-cross-origin')
    expect(headers['Permissions-Policy']).toContain('camera=()')
    expect(headers['Permissions-Policy']).toContain('microphone=()')
    expect(headers['Content-Security-Policy']).toContain("default-src 'self'")
    expect(headers['Content-Security-Policy']).toContain("frame-ancestors 'none'")
    expect(headers['Content-Security-Policy']).toContain("object-src 'none'")
  })

  it('does not send HSTS in non-production test/dev mode', () => {
    const headers = buildSecurityHeaders({ production: false })
    expect(headers['Strict-Transport-Security']).toBeUndefined()
  })

  it('redirects only positively identified insecure production requests', () => {
    expect(shouldRedirectToHttps({ production: true, forwardedProto: 'http' })).toBe(true)
    expect(shouldRedirectToHttps({ production: true, forwardedProto: 'https' })).toBe(false)
    expect(shouldRedirectToHttps({ production: false, forwardedProto: 'http' })).toBe(false)
    expect(shouldRedirectToHttps({ production: true, forwardedProto: undefined })).toBe(false)
  })
})
