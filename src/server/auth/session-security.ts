import { createHmac, randomBytes, timingSafeEqual } from 'node:crypto'

export type StaffAccountStatus = 'pending' | 'active' | 'suspended' | 'revoked'

export type StaffSessionState = {
  accountStatus: StaffAccountStatus
  expiresAt: number
  lastSeenAt: number
  authenticatedAt: number
  mfaVerifiedAt?: number
}

type SessionTokenPair = {
  token: string
  verifier: string
}

type SessionPolicy = {
  now?: number
  maxIdleMs?: number
  maxMfaAgeMs?: number
}

function hashToken(token: string, secret: string): string {
  if (!secret) throw new Error('session secret is required')
  return createHmac('sha256', secret).update(token).digest('base64url')
}

export function issueSessionToken(secret: string): SessionTokenPair {
  const token = randomBytes(32).toString('base64url')
  return { token, verifier: hashToken(token, secret) }
}

export function rotateSessionToken(_previousToken: string, secret: string): SessionTokenPair {
  return issueSessionToken(secret)
}

export function verifySessionToken(token: string, verifier: string, secret: string): boolean {
  if (!token || !verifier || !secret) return false
  const expected = Buffer.from(hashToken(token, secret))
  const supplied = Buffer.from(verifier)
  if (expected.length !== supplied.length) return false
  return timingSafeEqual(expected, supplied)
}

export function serializeSessionCookie(
  name: string,
  token: string,
  options: { production: boolean; maxAgeSeconds: number },
): string {
  if (!name || !token) throw new Error('session cookie name and token are required')
  if (!Number.isInteger(options.maxAgeSeconds) || options.maxAgeSeconds <= 0) {
    throw new Error('session cookie lifetime must be a positive integer')
  }

  const attributes = [
    `${encodeURIComponent(name)}=${encodeURIComponent(token)}`,
    'Path=/',
    `Max-Age=${options.maxAgeSeconds}`,
    'HttpOnly',
    'SameSite=Strict',
  ]
  if (options.production) attributes.push('Secure')
  return attributes.join('; ')
}

export function assertStaffSession<T extends StaffSessionState>(
  session: T,
  {
    now = Date.now(),
    maxIdleMs = 30 * 60 * 1000,
    maxMfaAgeMs = 12 * 60 * 60 * 1000,
  }: SessionPolicy = {},
): T {
  if (session.accountStatus !== 'active') throw new Error('Staff account is not active')
  if (session.expiresAt <= now) throw new Error('Staff session has expired')
  if (now - session.lastSeenAt > maxIdleMs) throw new Error('Staff session is inactive')
  if (session.mfaVerifiedAt === undefined || now - session.mfaVerifiedAt > maxMfaAgeMs) {
    throw new Error('MFA verification is required')
  }
  return session
}

export function requireRecentReauthentication<T extends StaffSessionState>(
  session: T,
  { now = Date.now(), maxAgeMs = 10 * 60 * 1000 }: { now?: number; maxAgeMs?: number } = {},
): T {
  if (now - session.authenticatedAt > maxAgeMs) {
    throw new Error('Recent reauthentication is required for this operation')
  }
  return session
}
