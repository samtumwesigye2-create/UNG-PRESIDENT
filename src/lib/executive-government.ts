export type ExecutiveGovernmentRole = 'president'|'admin'|'staff'|'protocol'|'press'

export type ExecutiveDirectoryRecord = {
  kind: 'vice_president'|'prime_minister'|'department'
  name: string
  status: 'draft'|'review'|'approved'|'published'|'archived'
  mandate?: string
  functions?: string
  leaderName?: string
  leaderTitle?: string
  phone?: string
  email?: string
  website?: string
  officeAddress?: string
}

export function buildExecutiveDirectory(records: ExecutiveDirectoryRecord[]) {
  return records.filter(record => record.status === 'published')
}

export function canManageExecutiveGovernment(role: ExecutiveGovernmentRole) {
  return role === 'president' || role === 'admin' || role === 'staff'
}
