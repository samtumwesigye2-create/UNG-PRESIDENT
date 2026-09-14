import { createHmac, randomBytes, timingSafeEqual } from 'node:crypto'

type IssueCsrfTokenArgs = {
  sessionId: string
  secret: string
  now?: number
}

type VerifyCsrfTokenArgs = {
  token: string
  sessionId: string
  secret: string
  now?: number
  maxAgeMs?: number
}

function signature(sessionId: string, timestamp: number, nonce: string, secret: string) {
  return createHmac('sha256', secret)
    .update(`${sessionId}.${timestamp}.${nonce}`)
    .digest('base64url')
}

export function issueCsrfToken({ sessionId, secret, now = Date.now() }: IssueCsrfTokenArgs): string {
  if (!sessionId || !secret) throw new Error('CSRF session and secret are required')
  const nonce = randomBytes(24).toString('base64url')
  return `${now}.${nonce}.${signature(sessionId, now, nonce, secret)}`
}

export function verifyCsrfToken({
  token,
  sessionId,
  secret,
  now = Date.now(),
  maxAgeMs = 2 * 60 * 60 * 1000,
}: VerifyCsrfTokenArgs): boolean {
  if (!token || !sessionId || !secret) return false
  const parts = token.split('.')
  if (parts.length !== 3) return false

  const [timestampText, nonce, suppliedSignature] = parts
  const timestamp = Number(timestampText)
  if (!Number.isFinite(timestamp) || !nonce || !suppliedSignature) return false
  if (timestamp > now + 30_000 || now - timestamp > maxAgeMs) return false

  const expectedSignature = signature(sessionId, timestamp, nonce, secret)
  const supplied = Buffer.from(suppliedSignature)
  const expected = Buffer.from(expectedSignature)
  if (supplied.length !== expected.length) return false

  return timingSafeEqual(supplied, expected)
}
