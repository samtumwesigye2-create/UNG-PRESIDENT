export type RateLimitPolicy = {
  limit: number
  windowMs: number
}

export type RateLimitDecision = {
  allowed: boolean
  remaining: number
  retryAfterMs: number
}

export class SlidingWindowRateLimiter {
  private readonly buckets = new Map<string, number[]>()

  consume(key: string, policy: RateLimitPolicy, now = Date.now()): RateLimitDecision {
    if (!key) throw new Error('rate-limit key is required')
    if (!Number.isInteger(policy.limit) || policy.limit < 1) throw new Error('rate-limit policy.limit must be >= 1')
    if (!Number.isFinite(policy.windowMs) || policy.windowMs <= 0) throw new Error('rate-limit policy.windowMs must be > 0')

    const cutoff = now - policy.windowMs
    const recent = (this.buckets.get(key) ?? []).filter((timestamp) => timestamp > cutoff)

    if (recent.length >= policy.limit) {
      const retryAfterMs = Math.max(1, recent[0] + policy.windowMs - now)
      this.buckets.set(key, recent)
      return { allowed: false, remaining: 0, retryAfterMs }
    }

    recent.push(now)
    this.buckets.set(key, recent)
    return {
      allowed: true,
      remaining: Math.max(0, policy.limit - recent.length),
      retryAfterMs: 0,
    }
  }

  clear(key?: string) {
    if (key) this.buckets.delete(key)
    else this.buckets.clear()
  }
}
