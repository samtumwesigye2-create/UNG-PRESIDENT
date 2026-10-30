import { describe, expect, it } from 'vitest'
import { canTransitionStaffStatus, requiresDualApproval } from '@/lib/staff-security'

describe('staff security lifecycle', () => {
  it('permits controlled activation, suspension, reactivation and revocation', () => {
    expect(canTransitionStaffStatus('pending','active')).toBe(true)
    expect(canTransitionStaffStatus('active','suspended')).toBe(true)
    expect(canTransitionStaffStatus('suspended','active')).toBe(true)
    expect(canTransitionStaffStatus('pending','revoked')).toBe(true)
    expect(canTransitionStaffStatus('active','revoked')).toBe(true)
  })

  it('forbids unsafe lifecycle shortcuts', () => {
    expect(canTransitionStaffStatus('revoked','active')).toBe(false)
    expect(canTransitionStaffStatus('active','pending')).toBe(false)
    expect(canTransitionStaffStatus('suspended','pending')).toBe(false)
  })

  it('marks presidential publishing and privilege changes as dual-approval actions', () => {
    expect(requiresDualApproval('executive_order.issue')).toBe(true)
    expect(requiresDualApproval('staff.role.change')).toBe(true)
    expect(requiresDualApproval('press.release')).toBe(true)
    expect(requiresDualApproval('visitor_request.update')).toBe(false)
  })
})
