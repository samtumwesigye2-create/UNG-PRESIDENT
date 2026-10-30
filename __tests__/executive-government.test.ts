import { describe, expect, it } from 'vitest'
import { buildExecutiveDirectory, canManageExecutiveGovernment } from '@/lib/executive-government'

describe('executive government publishing rules', () => {
  it('shows only published offices and departments without inventing missing details', () => {
    const directory = buildExecutiveDirectory([
      { kind:'vice_president', name:'Office of the Vice President', status:'published', mandate:'Coordinate assigned executive responsibilities' },
      { kind:'prime_minister', name:'Office of the Prime Minister', status:'draft' },
      { kind:'department', name:'Department A', status:'published' },
    ])
    expect(directory.map(x => x.name)).toEqual(['Office of the Vice President','Department A'])
    expect(directory[1].mandate).toBeUndefined()
  })

  it('limits executive-government editing to authorized staff roles', () => {
    expect(canManageExecutiveGovernment('president')).toBe(true)
    expect(canManageExecutiveGovernment('admin')).toBe(true)
    expect(canManageExecutiveGovernment('staff')).toBe(true)
    expect(canManageExecutiveGovernment('press')).toBe(false)
    expect(canManageExecutiveGovernment('protocol')).toBe(false)
  })
})
