import { describe, expect, it } from 'vitest'
import { issueCsrfToken, verifyCsrfToken } from '../src/server/security/csrf'
import { SlidingWindowRateLimiter } from '../src/server/security/rate-limit'
import { assertEmail, assertEnum, assertText, rejectUnknownKeys } from '../src/server/security/validation'

describe('CSRF protection', () => {
  it('accepts only a valid token bound to the intended session', () => {
    const secret = '0123456789abcdef0123456789abcdef'
    const token = issueCsrfToken({ sessionId: 'session-a', secret, now: 1_000 })

    expect(verifyCsrfToken({ token, sessionId: 'session-a', secret, now: 2_000 })).toBe(true)
    expect(verifyCsrfToken({ token, sessionId: 'session-b', secret, now: 2_000 })).toBe(false)
    expect(verifyCsrfToken({ token: `${token}tampered`, sessionId: 'session-a', secret, now: 2_000 })).toBe(false)
    expect(verifyCsrfToken({ token: '', sessionId: 'session-a', secret, now: 2_000 })).toBe(false)
  })

  it('expires old tokens', () => {
    const secret = '0123456789abcdef0123456789abcdef'
    const token = issueCsrfToken({ sessionId: 'session-a', secret, now: 1_000 })
    expect(verifyCsrfToken({ token, sessionId: 'session-a', secret, now: 1_000 + 7_200_001, maxAgeMs: 7_200_000 })).toBe(false)
  })
})

describe('strict input validation', () => {
  it('rejects oversized text, malformed email, invalid enums, and unknown privileged fields', () => {
    expect(() => assertText('x'.repeat(21), { field: 'subject', min: 1, max: 20 })).toThrow(/subject/)
    expect(() => assertEmail('not-an-email')).toThrow(/email/i)
    expect(() => assertEnum('superuser', ['staff', 'admin'] as const, 'role')).toThrow(/role/)
    expect(() => rejectUnknownKeys({ role: 'admin', hiddenPrivilege: true }, ['role'] as const)).toThrow(/hiddenPrivilege/)
  })

  it('returns normalized valid values', () => {
    expect(assertText('  State House  ', { field: 'office', min: 2, max: 40 })).toBe('State House')
    expect(assertEmail('  STAFF@EXAMPLE.GOV  ')).toBe('staff@example.gov')
    expect(assertEnum('staff', ['staff', 'admin'] as const, 'role')).toBe('staff')
  })
})

describe('application fallback rate limiting', () => {
  it('limits bursts within the configured window and recovers after it', () => {
    const limiter = new SlidingWindowRateLimiter()
    const policy = { limit: 2, windowMs: 60_000 }

    expect(limiter.consume('login:ip-1', policy, 1_000).allowed).toBe(true)
    expect(limiter.consume('login:ip-1', policy, 2_000).allowed).toBe(true)
    const blocked = limiter.consume('login:ip-1', policy, 3_000)
    expect(blocked.allowed).toBe(false)
    expect(blocked.retryAfterMs).toBeGreaterThan(0)
    expect(limiter.consume('login:ip-1', policy, 61_001).allowed).toBe(true)
  })
})
