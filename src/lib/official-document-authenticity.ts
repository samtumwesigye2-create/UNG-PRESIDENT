type VerificationInput = {
  title: string
  reference: string
  version: string
  issuedBy: string
  issuingOffice: string
  status: string
  updatedAt: number
  publishedAt?: number
}

export function buildVerificationRecord(input: VerificationInput) {
  const reference = input.reference.trim()
  return {
    title: input.title,
    reference,
    version: input.version,
    issuedBy: input.issuedBy,
    issuingOffice: input.issuingOffice,
    status: input.status,
    lastUpdated: input.updatedAt,
    publicationTimestamp: input.publishedAt,
    verificationPath: `/verify/${encodeURIComponent(reference)}`,
  }
}

export function nextRevisionNumber(history: Array<{ revisionNumber: number }>) {
  return history.reduce((max, item) => Math.max(max, item.revisionNumber), 0) + 1
}
