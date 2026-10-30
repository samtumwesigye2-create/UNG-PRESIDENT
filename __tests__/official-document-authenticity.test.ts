import { describe, expect, it } from 'vitest'
import { buildVerificationRecord, nextRevisionNumber } from '@/lib/official-document-authenticity'

describe('official document authenticity and revision lifecycle', () => {
  it('builds verification metadata from an immutable public reference', () => {
    const record = buildVerificationRecord({
      title: 'National Policy Record',
      reference: 'OP-POL-2026-0042',
      version: '2.0',
      issuedBy: 'Office of the President',
      issuingOffice: 'Presidential Secretariat',
      status: 'published',
      updatedAt: 1700000000000,
      publishedAt: 1690000000000,
    })
    expect(record.reference).toBe('OP-POL-2026-0042')
    expect(record.status).toBe('published')
    expect(record.verificationPath).toBe('/verify/OP-POL-2026-0042')
    expect(record.lastUpdated).toBe(1700000000000)
    expect(record.publicationTimestamp).toBe(1690000000000)
  })

  it('increments revisions without overwriting earlier history', () => {
    expect(nextRevisionNumber([])).toBe(1)
    expect(nextRevisionNumber([{ revisionNumber: 1 }, { revisionNumber: 2 }])).toBe(3)
  })
})
