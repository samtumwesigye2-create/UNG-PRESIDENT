import { describe, expect, it } from 'vitest'
import {
  assertStaffSession,
  issueSessionToken,
  requireRecentReauthentication,
  rotateSessionToken,
  serializeSessionCookie,
  verifySessionToken,
} from '../src/server/auth/session-security'

describe('secure staff session tokens and cookies', () => {
  it('stores a verifier rather than the raw bearer token and supports rotation', () => {
    const secret = '0123456789abcdef0123456789abcdef'
    const first = issueSessionToken(secret)
    expect(first.token).not.toBe(first.verifier)
    expect(verifySessionToken(first.token, first.verifier, secret)).toBe(true)

    const second = rotateSessionToken(first.token, secret)
    expect(second.token).not.toBe(first.token)
    expect(second.verifier).not.toBe(first.verifier)
    expect(verifySessionToken(second.token, second.verifier, secret)).toBe(true)
  })

  it('uses HttpOnly, Secure, SameSite and bounded lifetime in production', () => {
    const cookie = serializeSessionCookie('president_session', 'secret-token', {
      production: true,
      maxAgeSeconds: 1800,
    })
    expect(cookie).toContain('HttpOnly')
    expect(cookie).toContain('Secure')
    expect(cookie).toContain('SameSite=Strict')
    expect(cookie).toContain('Path=/')
    expect(cookie).toContain('Max-Age=1800')
  })
})

describe('zero-trust staff session enforcement', () => {
  const base = {
    accountStatus: 'active' as const,
    expiresAt: 10_000,
    lastSeenAt: 1_000,
    authenticatedAt: 500,
    mfaVerifiedAt: 800,
  }

  it('denies inactive accounts, missing MFA, expired sessions and idle sessions', () => {
    expect(() => assertStaffSession({ ...base, accountStatus: 'suspended' }, { now: 2_000 })).toThrow(/active/i)
    expect(() => assertStaffSession({ ...base, mfaVerifiedAt: undefined }, { now: 2_000 })).toThrow(/MFA/)
    expect(() => assertStaffSession({ ...base, expiresAt: 1_500 }, { now: 2_000 })).toThrow(/expired/i)
    expect(() => assertStaffSession({ ...base, lastSeenAt: 1_000 }, { now: 3_001, maxIdleMs: 2_000 })).toThrow(/inactive/i)
  })

  it('accepts an active, MFA-verified, non-expired session', () => {
    expect(assertStaffSession(base, { now: 2_000, maxIdleMs: 2_000 })).toEqual(base)
  })

  it('requires recent reauthentication for sensitive operations', () => {
    expect(() => requireRecentReauthentication({ ...base, authenticatedAt: 1_000 }, { now: 20_001, maxAgeMs: 10_000 })).toThrow(/reauthentication/i)
    expect(requireRecentReauthentication(base, { now: 2_000, maxAgeMs: 10_000 })).toEqual(base)
  })
})
