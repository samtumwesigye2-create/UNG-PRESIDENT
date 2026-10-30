export type StaffStatus = 'pending' | 'active' | 'suspended' | 'revoked'

const transitions: Record<StaffStatus, StaffStatus[]> = {
  pending: ['active', 'revoked'],
  active: ['suspended', 'revoked'],
  suspended: ['active', 'revoked'],
  revoked: [],
}

const dualApprovalActions = new Set([
  'executive_order.issue',
  'executive_order.rescind',
  'staff.role.change',
  'staff.privilege.grant',
  'press.release',
  'legislation.status.change',
])

export function canTransitionStaffStatus(from: StaffStatus, to: StaffStatus) {
  return transitions[from].includes(to)
}

export function requiresDualApproval(action: string) {
  return dualApprovalActions.has(action)
}
