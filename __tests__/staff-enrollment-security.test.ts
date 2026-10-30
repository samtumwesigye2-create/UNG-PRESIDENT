import { describe, expect, it } from 'vitest'
import { createHash } from 'node:crypto'

const hashCode = (code: string) => createHash('sha256').update(code.trim()).digest('hex')

type Invitation = { codeHash:string; email:string; role:string; expiresAt:number; usedAt?:number; revokedAt?:number }

function validateInvitation(invite: Invitation | null, code:string, email:string, now:number) {
  if (!invite || invite.codeHash !== hashCode(code)) return 'INVALID_CODE'
  if (invite.revokedAt) return 'REVOKED'
  if (invite.usedAt) return 'ALREADY_USED'
  if (invite.expiresAt <= now) return 'EXPIRED'
  if (invite.email !== email.trim().toLowerCase()) return 'IDENTITY_MISMATCH'
  return 'VALID'
}

describe('HR staff enrollment contract', () => {
  const now = 1_800_000_000_000
  const base: Invitation = { codeHash:hashCode('HR-7F9K-2P4M'), email:'staff@gov.ug', role:'protocol', expiresAt:now + 60_000 }

  it('rejects invalid, expired, used, revoked and identity-mismatched invitations', () => {
    expect(validateInvitation(base, 'wrong', 'staff@gov.ug', now)).toBe('INVALID_CODE')
    expect(validateInvitation({...base, expiresAt:now}, 'HR-7F9K-2P4M', 'staff@gov.ug', now)).toBe('EXPIRED')
    expect(validateInvitation({...base, usedAt:now-1}, 'HR-7F9K-2P4M', 'staff@gov.ug', now)).toBe('ALREADY_USED')
    expect(validateInvitation({...base, revokedAt:now-1}, 'HR-7F9K-2P4M', 'staff@gov.ug', now)).toBe('REVOKED')
    expect(validateInvitation(base, 'HR-7F9K-2P4M', 'other@gov.ug', now)).toBe('IDENTITY_MISMATCH')
  })

  it('accepts a current single-use code only for its HR-authorized identity and bound role', () => {
    expect(validateInvitation(base, 'HR-7F9K-2P4M', 'STAFF@gov.ug', now)).toBe('VALID')
    expect(base.role).toBe('protocol')
  })
})
