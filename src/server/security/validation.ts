type TextOptions = {
  field: string
  min: number
  max: number
}

export function assertText(value: unknown, options: TextOptions): string {
  if (typeof value !== 'string') throw new Error(`${options.field} must be text`)
  const normalized = value.trim()
  if (normalized.length < options.min || normalized.length > options.max) {
    throw new Error(`${options.field} must be between ${options.min} and ${options.max} characters`)
  }
  return normalized
}

export function assertEmail(value: unknown): string {
  const email = assertText(value, { field: 'email', min: 3, max: 254 }).toLowerCase()
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw new Error('email is invalid')
  return email
}

export function assertEnum<const T extends readonly string[]>(value: unknown, allowed: T, field: string): T[number] {
  if (typeof value !== 'string' || !allowed.includes(value)) {
    throw new Error(`${field} is invalid`)
  }
  return value as T[number]
}

export function rejectUnknownKeys<T extends Record<string, unknown>, const K extends readonly string[]>(
  value: T,
  allowed: K,
): T {
  const allowedSet = new Set<string>(allowed)
  const unknown = Object.keys(value).filter((key) => !allowedSet.has(key))
  if (unknown.length) throw new Error(`Unexpected field(s): ${unknown.join(', ')}`)
  return value
}
