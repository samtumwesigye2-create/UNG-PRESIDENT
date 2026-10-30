import { describe, expect, it } from 'vitest'
import { canPerform, type StaffRole } from '@/lib/rbac'

describe('UNG-PRESIDENT RBAC', () => {
  it('allows president/admin privileged presidential actions', () => {
    expect(canPerform('president', 'executive_orders.create')).toBe(true)
    expect(canPerform('admin', 'executive_orders.create')).toBe(true)
  })

  it('restricts operational write domains by role', () => {
    expect(canPerform('staff', 'appointments.create')).toBe(true)
    expect(canPerform('protocol', 'state_visits.create')).toBe(true)
    expect(canPerform('press', 'press_statements.create')).toBe(true)
    expect(canPerform('press', 'appointments.create')).toBe(false)
    expect(canPerform('staff', 'state_visits.create')).toBe(false)
  })

  it('rejects unknown permissions', () => {
    expect(canPerform('staff' as StaffRole, 'nope' as never)).toBe(false)
  })
})
