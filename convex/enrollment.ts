import { getAuthUserId } from '@convex-dev/auth/server'
import { v } from 'convex/values'
import { mutation, query } from './_generated/server'

const roleValidator = v.union(v.literal('president'),v.literal('admin'),v.literal('staff'),v.literal('protocol'),v.literal('press'))

async function sha256(value:string) {
  const bytes = new TextEncoder().encode(value.trim())
  const digest = await crypto.subtle.digest('SHA-256', bytes)
  return Array.from(new Uint8Array(digest)).map(b => b.toString(16).padStart(2,'0')).join('')
}

async function privileged(ctx:any) {
  const userId = await getAuthUserId(ctx)
  if (!userId) return null
  const profile = await ctx.db.query('staffProfiles').withIndex('by_user',(q:any)=>q.eq('userId',userId)).unique()
  if (!profile || !profile.active || (profile.status && profile.status !== 'active')) return null
  if (profile.role !== 'admin' && profile.role !== 'president') return null
  return { userId, profile }
}

export const issueInvitation = mutation({
  args:{ code:v.string(),email:v.string(),employeeId:v.optional(v.string()),intendedRole:roleValidator,office:v.optional(v.string()),department:v.optional(v.string()),expiresAt:v.number() },
  handler:async(ctx,args)=>{
    const actor = await privileged(ctx)
    if (!actor) return {ok:false as const,code:'FORBIDDEN',message:'Authorized HR/security administration is required.'}
    if (args.expiresAt <= Date.now()) return {ok:false as const,code:'INVALID_EXPIRY',message:'Enrollment invitation must expire in the future.'}
    const codeHash = await sha256(args.code)
    const existing = await ctx.db.query('staffInvitations').withIndex('by_code_hash',q=>q.eq('codeHash',codeHash)).unique()
    if (existing) return {ok:false as const,code:'DUPLICATE_CODE',message:'Issue a new unique enrollment code.'}
    const id=await ctx.db.insert('staffInvitations',{codeHash,email:args.email.trim().toLowerCase(),employeeId:args.employeeId?.trim(),intendedRole:args.intendedRole,office:args.office?.trim(),department:args.department?.trim(),expiresAt:args.expiresAt,createdBy:actor.userId,createdAt:Date.now()})
    await ctx.db.insert('auditLog',{userId:actor.userId,action:'enrollment.invitation.issue',entity:'staffInvitation',entityId:String(id),details:args.email.trim().toLowerCase(),createdAt:Date.now()})
    return {ok:true as const}
  }
})

export const revokeInvitation = mutation({
  args:{ invitationId:v.id('staffInvitations') },
  handler:async(ctx,args)=>{
    const actor=await privileged(ctx)
    if(!actor) return {ok:false as const,code:'FORBIDDEN',message:'Authorized HR/security administration is required.'}
    const invite=await ctx.db.get(args.invitationId)
    if(!invite) return {ok:false as const,code:'NOT_FOUND',message:'Invitation not found.'}
    if(invite.usedAt) return {ok:false as const,code:'ALREADY_USED',message:'Used invitations cannot be revoked.'}
    await ctx.db.patch(args.invitationId,{revokedAt:Date.now(),revokedBy:actor.userId})
    await ctx.db.insert('auditLog',{userId:actor.userId,action:'enrollment.invitation.revoke',entity:'staffInvitation',entityId:String(args.invitationId),createdAt:Date.now()})
    return {ok:true as const}
  }
})

export const invitationStatus = query({
  args:{ code:v.string(),email:v.string() },
  handler:async(ctx,args)=>{
    const userId=await getAuthUserId(ctx)
    if(!userId) return {ok:false as const,code:'UNAUTHENTICATED',message:'Verify your staff email before enrollment.'}
    const user=await ctx.db.get(userId)
    const authEmail=user?.email?.trim().toLowerCase()
    const supplied=args.email.trim().toLowerCase()
    if(!authEmail || authEmail!==supplied) return {ok:false as const,code:'IDENTITY_MISMATCH',message:'Enrollment must use the verified email on your signed-in account.'}
    const codeHash=await sha256(args.code)
    const invite=await ctx.db.query('staffInvitations').withIndex('by_code_hash',q=>q.eq('codeHash',codeHash)).unique()
    if(!invite) return {ok:false as const,code:'INVALID_CODE',message:'Enrollment code is invalid.'}
    if(invite.revokedAt) return {ok:false as const,code:'REVOKED',message:'Enrollment code was revoked.'}
    if(invite.usedAt) return {ok:false as const,code:'ALREADY_USED',message:'Enrollment code has already been used.'}
    if(invite.expiresAt<=Date.now()) return {ok:false as const,code:'EXPIRED',message:'Enrollment code has expired.'}
    if(invite.email!==supplied) return {ok:false as const,code:'IDENTITY_MISMATCH',message:'Enrollment code was issued for a different staff identity.'}
    return {ok:true as const,intendedRole:invite.intendedRole,office:invite.office,department:invite.department,employeeId:invite.employeeId,expiresAt:invite.expiresAt}
  }
})

export const enroll = mutation({
  args:{ code:v.string(),email:v.string(),fullName:v.string(),preferredName:v.optional(v.string()),employeeId:v.string(),phone:v.string(),jobTitle:v.string(),department:v.string(),office:v.string(),supervisor:v.string(),workLocation:v.string(),employmentType:v.string(),startDate:v.string(),acceptSecurityPolicy:v.boolean() },
  handler:async(ctx,args)=>{
    const userId=await getAuthUserId(ctx)
    if(!userId) return {ok:false as const,code:'UNAUTHENTICATED',message:'Sign in with your verified staff email first.'}
    if(!args.acceptSecurityPolicy) return {ok:false as const,code:'POLICY_REQUIRED',message:'Security policy acknowledgement is required.'}
    const user=await ctx.db.get(userId)
    const email=args.email.trim().toLowerCase()
    if(!user?.email || user.email.trim().toLowerCase()!==email) return {ok:false as const,code:'IDENTITY_MISMATCH',message:'Verified account email does not match enrollment identity.'}
    const codeHash=await sha256(args.code)
    const invite=await ctx.db.query('staffInvitations').withIndex('by_code_hash',q=>q.eq('codeHash',codeHash)).unique()
    if(!invite) return {ok:false as const,code:'INVALID_CODE',message:'Enrollment code is invalid.'}
    if(invite.revokedAt) return {ok:false as const,code:'REVOKED',message:'Enrollment code was revoked.'}
    if(invite.usedAt) return {ok:false as const,code:'ALREADY_USED',message:'Enrollment code has already been used.'}
    if(invite.expiresAt<=Date.now()) return {ok:false as const,code:'EXPIRED',message:'Enrollment code has expired.'}
    if(invite.email!==email || (invite.employeeId && invite.employeeId!==args.employeeId.trim())) return {ok:false as const,code:'IDENTITY_MISMATCH',message:'HR invitation does not match the supplied staff identity.'}
    const prior=await ctx.db.query('staffProfiles').withIndex('by_user',q=>q.eq('userId',userId)).unique()
    if(prior) return {ok:false as const,code:'ALREADY_ENROLLED',message:'This authenticated identity already has a staff profile.'}
    const now=Date.now()
    const profileId=await ctx.db.insert('staffProfiles',{userId,email,fullName:args.fullName.trim(),preferredName:args.preferredName?.trim(),employeeId:args.employeeId.trim(),phone:args.phone.trim(),jobTitle:args.jobTitle.trim(),department:args.department.trim(),office:args.office.trim(),supervisor:args.supervisor.trim(),workLocation:args.workLocation.trim(),employmentType:args.employmentType.trim(),startDate:args.startDate,role:invite.intendedRole,status:'pending',active:false,securityPolicyAcceptedAt:now,createdAt:now,updatedAt:now})
    await ctx.db.patch(invite._id,{usedAt:now,usedBy:userId})
    await ctx.db.insert('auditLog',{userId,action:'enrollment.submit',entity:'staffProfile',entityId:String(profileId),details:'Pending security/administrative activation',createdAt:now})
    return {ok:true as const,status:'pending' as const,message:'Enrollment received. Staff access remains disabled until authorized activation.'}
  }
})
