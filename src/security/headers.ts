type SecurityHeaderOptions = {
  production: boolean
  hstsEnabled: boolean
  connectSrc?: string[]
  imageSrc?: string[]
}

const unique = (values: string[]) => [...new Set(values)]

export function buildSecurityHeaders(options: SecurityHeaderOptions): Record<string, string> {
  const connectSrc = unique(["'self'", ...(options.connectSrc ?? [])])
  const imageSrc = unique(["'self'", 'data:', ...(options.imageSrc ?? [])])

  const csp = [
    "default-src 'self'",
    "base-uri 'self'",
    "object-src 'none'",
    "frame-ancestors 'none'",
    "form-action 'self'",
    `script-src 'self'`,
    `style-src 'self' 'unsafe-inline'`,
    `img-src ${imageSrc.join(' ')}`,
    `connect-src ${connectSrc.join(' ')}`,
    "font-src 'self' data:",
  ].join('; ')

  const headers: Record<string, string> = {
    'Content-Security-Policy': csp,
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
    'X-Frame-Options': 'DENY',
    'Cache-Control': 'no-store',
  }

  if (options.production && options.hstsEnabled) {
    headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
  }

  return headers
}
