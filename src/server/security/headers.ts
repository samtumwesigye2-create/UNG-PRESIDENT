export type SecurityHeaderOptions = {
  production: boolean
}

export type HttpsRedirectOptions = {
  production: boolean
  forwardedProto?: string
}

const contentSecurityPolicy = [
  "default-src 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  "frame-ancestors 'none'",
  "form-action 'self'",
  "script-src 'self'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: https://assets.macaly-user-data.dev",
  "font-src 'self' data:",
  "connect-src 'self' https://*.convex.cloud https://*.convex.site wss://*.convex.cloud",
].join('; ')

export function buildSecurityHeaders({ production }: SecurityHeaderOptions): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Security-Policy': production
      ? `${contentSecurityPolicy}; upgrade-insecure-requests`
      : contentSecurityPolicy,
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
    'Cross-Origin-Opener-Policy': 'same-origin',
  }

  if (production) {
    // Preload is intentionally omitted until every covered production subdomain
    // has been validated as HTTPS-only and the domain is ready for preload submission.
    headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
  }

  return headers
}

export function shouldRedirectToHttps({ production, forwardedProto }: HttpsRedirectOptions): boolean {
  if (!production || !forwardedProto) return false
  return forwardedProto.split(',')[0]?.trim().toLowerCase() === 'http'
}
