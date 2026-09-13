export type PublicEvent = {
  _id?: string
  title: string
  eventDate: string
  isPublic: boolean
  status: string
  scope?: 'domestic' | 'international'
  eventType?: 'state_visit' | 'public_appearance' | 'ceremonial' | 'official_meeting' | 'other'
  [key: string]: unknown
}

export type OfficialDocument = {
  _id?: string
  title: string
  documentType: 'policy' | 'regulation' | 'executive_directive' | 'legislation' | 'proclamation' | 'cabinet_decision' | 'other'
  status: 'draft' | 'review' | 'approved' | 'published' | 'archived'
  issuedBy: string
  reference: string
  year?: string
  topic?: string
  [key: string]: unknown
}

export function classifyPublicEvents<T extends PublicEvent>(events: T[]) {
  const visible = events.filter(event => event.isPublic && event.status === 'scheduled')
  return {
    domestic: visible.filter(event => event.scope === 'domestic'),
    international: visible.filter(event => event.scope === 'international'),
  }
}

export function filterOfficialDocuments<T extends OfficialDocument>(
  documents: T[],
  filters: { documentType?: OfficialDocument['documentType'] | 'all'; status?: OfficialDocument['status'] | 'all'; year?: string; topic?: string } = {},
) {
  return documents.filter(document => {
    if (document.status !== 'published') return false
    if (filters.documentType && filters.documentType !== 'all' && document.documentType !== filters.documentType) return false
    if (filters.status && filters.status !== 'all' && document.status !== filters.status) return false
    if (filters.year && document.year !== filters.year) return false
    if (filters.topic && document.topic !== filters.topic) return false
    return true
  })
}
