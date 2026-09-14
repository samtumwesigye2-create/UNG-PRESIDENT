import { defineEventHandler, getRequestHeader, getRequestURL, sendRedirect, setResponseHeader } from 'h3'
import { buildSecurityHeaders, shouldRedirectToHttps } from '../../src/server/security/headers'

export default defineEventHandler((event) => {
  const production = process.env.NODE_ENV === 'production'
  const forwardedProto = getRequestHeader(event, 'x-forwarded-proto')

  if (shouldRedirectToHttps({ production, forwardedProto })) {
    const url = getRequestURL(event)
    url.protocol = 'https:'
    return sendRedirect(event, url.toString(), 308)
  }

  const headers = buildSecurityHeaders({ production })
  for (const [name, value] of Object.entries(headers)) {
    setResponseHeader(event, name, value)
  }
})
