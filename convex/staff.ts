import { getAuthUserId } from '@convex-dev/auth/server'
import { v } from 'convex/values'
import { mutation, query } from './_generated/server'

const roleValidator = v.union(v.literal('president'),v.literal('admin'),v.literal('staff'),v.literal('protocol'),v.literal('press'))
const statusValidator = v.union(v.literal('pending'),v.literal('active'),v.literal('suspended'),v.literal('revoked'))

type StaffStatus = 'pending'|'active'|'suspended'|'revoked'
const allowedTransitions: Record<StaffStatus, StaffStatus[]> = { pending:['active','revoked'], active:['suspended','revoked'], suspended:['active','revoked'], revoked:[] }

async function currentProfile(ctx:any) {
  const userId = await getAuthUserId(ctx)
  if (!userId) return null
  const user = await ctx.db.get(userId)
  const email = user?.email?.toLowerCase()
  if (!email) return null
  let profile = await ctx.db.query('staffProfiles').withIndex('by_user',(q:any)=>q.eq('userId',userId)).unique()
  if (!profile) {
    profile = await ctx.db.query('staffProfiles').withIndex('by_email',(q:any)=>q.eq('email',email)).unique()
    if (profile && !profile.userId) {
      await ctx.db.patch(profile._id,{userId,updatedAt:Date.now()})
      profile = {...profile,userId}
    }
  }
  const effectiveStatus:StaffStatus = profile?.status ?? (profile?.active ? 'active' : 'pending')
  if (!profile?.active || effectiveStatus !== 'active') return null
  return {userId,profile:{...profile,status:effectiveStatus}}
}

async function privileged(ctx:any) {
  const found=await currentProfile(ctx)
  if(!found || (found.profile.role!=='admin' && found.profile.role!=='president')) return null
  return found
}

export const me = query({
  args:{},
  handler:async(ctx)=>{
    const userId=await getAuthUserId(ctx)
    if(!userId) return {ok:false as const,code:'UNAUTHENTICATED',message:'Sign in is required.'}
    const user=await ctx.db.get(userId)
    const email=user?.email?.toLowerCase()
    if(!email) return {ok:false as const,code:'FORBIDDEN',message:'Verified staff email is required.'}
    let p=await ctx.db.query('staffProfiles').withIndex('by_user',(q:any)=>q.eq('userId',userId)).unique()
    if(!p) p=await ctx.db.query('staffProfiles').withIndex('by_email',(q:any)=>q.eq('email',email)).unique()
    if(!p) return {ok:false as const,code:'NOT_ENROLLED',message:'This identity has not completed HR-authorized staff enrollment.'}
    const status:StaffStatus=p.status ?? (p.active?'active':'pending')
    if(status!=='active' || !p.active) return {ok:false as const,code:status.toUpperCase(),message:status==='pending'?'Enrollment is pending authorized activation.':status==='suspended'?'This staff account is suspended.':'This staff account has been revoked.'}
    return {ok:true as const,profile:{email:p.email,fullName:p.fullName,office:p.office,department:p.department,jobTitle:p.jobTitle,role:p.role,status}}
  }
})

export const dashboard = query({
  args:{},
  handler:async(ctx)=>{
    const found=await currentProfile(ctx)
    if(!found) return {ok:false as const,code:'FORBIDDEN',message:'Active staff access required.'}
    return {ok:true as const,counts:{executiveOrders:(await ctx.db.query('executiveOrders').take(1000)).length,press:(await ctx.db.query('pressStatements').take(1000)).length,events:(await ctx.db.query('stateFunctions').take(1000)).length,petitions:(await ctx.db.query('petitions').take(1000)).length,visits:(await ctx.db.query('stateVisits').take(1000)).length,messages:(await ctx.db.query('contactMessages').take(1000)).length,visitRequests:(await ctx.db.query('visitorRequests').take(1000)).length},recentMessages:await ctx.db.query('contactMessages').order('desc').take(8),recentVisitRequests:await ctx.db.query('visitorRequests').order('desc').take(8)}
  }
})

export const listProfiles = query({
  args:{},
  handler:async(ctx)=>{
    const actor=await privileged(ctx)
    if(!actor) return {ok:false as const,code:'FORBIDDEN',message:'Administrator access required.'}
    const profiles=await ctx.db.query('staffProfiles').order('desc').take(250)
    return {ok:true as const,profiles:profiles.map((p:any)=>({...p,status:p.status??(p.active?'active':'pending')}))}
  }
})

export const changeStatus = mutation({
  args:{profileId:v.id('staffProfiles'),status:statusValidator,reason:v.string()},
  handler:async(ctx,args)=>{
    const actor=await privileged(ctx)
    if(!actor) return {ok:false as const,code:'FORBIDDEN',message:'Administrator access required.'}
    const target=await ctx.db.get(args.profileId)
    if(!target) return {ok:false as const,code:'NOT_FOUND',message:'Staff profile not found.'}
    if(target.userId===actor.userId && args.status!=='active') return {ok:false as const,code:'SELF_LOCKOUT_BLOCKED',message:'Use a second privileged administrator for changes to your own access.'}
    const from:StaffStatus=target.status??(target.active?'active':'pending')
    if(!allowedTransitions[from].includes(args.status)) return {ok:false as const,code:'INVALID_TRANSITION',message:`Cannot move staff account from ${from} to ${args.status}.`}
    const active=args.status==='active'
    await ctx.db.patch(args.profileId,{status:args.status,active,updatedAt:Date.now()})
    await ctx.db.insert('auditLog',{userId:actor.userId,action:`staff.status.${args.status}`,entity:'staffProfile',entityId:String(args.profileId),details:args.reason.trim(),createdAt:Date.now()})
    return {ok:true as const}
  }
})

export const requestApproval = mutation({
  args:{action:v.string(),entity:v.string(),entityId:v.optional(v.string()),reason:v.string()},
  handler:async(ctx,args)=>{
    const found=await currentProfile(ctx)
    if(!found) return {ok:false as const,code:'FORBIDDEN',message:'Active staff access required.'}
    const id=await ctx.db.insert('privilegedApprovals',{action:args.action,entity:args.entity,entityId:args.entityId,requestedBy:found.userId,requestedAt:Date.now(),status:'pending',reason:args.reason.trim()})
    await ctx.db.insert('auditLog',{userId:found.userId,action:'approval.request',entity:args.entity,entityId:args.entityId,details:`${args.action}: ${args.reason.trim()}`,createdAt:Date.now()})
    return {ok:true as const,approvalId:id}
  }
})

export const listPendingApprovals = query({
  args:{},
  handler:async(ctx)=>{
    const actor=await privileged(ctx)
    if(!actor) return {ok:false as const,code:'FORBIDDEN',message:'Privileged reviewer access required.'}
    return {ok:true as const,approvals:await ctx.db.query('privilegedApprovals').withIndex('by_status',q=>q.eq('status','pending')).order('desc').take(100)}
  }
})

export const reviewApproval = mutation({
  args:{approvalId:v.id('privilegedApprovals'),decision:v.union(v.literal('approved'),v.literal('rejected')),reason:v.string()},
  handler:async(ctx,args)=>{
    const actor=await privileged(ctx)
    if(!actor) return {ok:false as const,code:'FORBIDDEN',message:'Privileged reviewer access required.'}
    const approval=await ctx.db.get(args.approvalId)
    if(!approval || approval.status!=='pending') return {ok:false as const,code:'NOT_PENDING',message:'Approval is no longer pending.'}
    if(approval.requestedBy===actor.userId) return {ok:false as const,code:'SECOND_APPROVER_REQUIRED',message:'The requester cannot approve their own privileged action.'}
    await ctx.db.patch(args.approvalId,{status:args.decision,reviewedBy:actor.userId,reviewedAt:Date.now(),reason:args.reason.trim()||approval.reason})
    await ctx.db.insert('auditLog',{userId:actor.userId,action:`approval.${args.decision}`,entity:approval.entity,entityId:approval.entityId,details:approval.action,createdAt:Date.now()})
    return {ok:true as const}
  }
})

export const upsertProfile = mutation({
  args:{email:v.string(),fullName:v.string(),office:v.optional(v.string()),role:roleValidator,active:v.boolean()},
  handler:async(ctx,args)=>{
    const actor=await privileged(ctx)
    if(!actor) return {ok:false as const,code:'FORBIDDEN',message:'Administrator access required.'}
    const email=args.email.trim().toLowerCase()
    const existing=await ctx.db.query('staffProfiles').withIndex('by_email',q=>q.eq('email',email)).unique()
    if(!existing) return {ok:false as const,code:'USE_HR_INVITATION',message:'New staff must be enrolled with an HR-issued single-use enrollment code.'}
    if(existing.role!==args.role) return {ok:false as const,code:'APPROVAL_REQUIRED',message:'Role changes require the privileged approval workflow.'}
    await ctx.db.patch(existing._id,{fullName:args.fullName.trim(),office:args.office,updatedAt:Date.now()})
    await ctx.db.insert('auditLog',{userId:actor.userId,action:'staff.profile.update',entity:'staffProfile',entityId:String(existing._id),details:email,createdAt:Date.now()})
    return {ok:true as const}
  }
})

export const bootstrap = mutation({
  args:{},
  handler:async(ctx)=>{
    const userId=await getAuthUserId(ctx)
    if(!userId) return {ok:false as const,code:'UNAUTHENTICATED',message:'Sign in first.'}
    const user=await ctx.db.get(userId)
    const email=user?.email?.toLowerCase()
    const configured=process.env.PRESIDENT_BOOTSTRAP_EMAIL?.trim().toLowerCase()
    if(!email||!configured||email!==configured) return {ok:false as const,code:'FORBIDDEN',message:'This account is not the configured bootstrap administrator.'}
    const existingAdmin=await ctx.db.query('staffProfiles').filter(q=>q.or(q.eq(q.field('role'),'admin'),q.eq(q.field('role'),'president'))).first()
    if(existingAdmin) return {ok:false as const,code:'ALREADY_INITIALIZED',message:'Privileged staff access is already initialized.'}
    await ctx.db.insert('staffProfiles',{userId,email,fullName:user?.name??email,role:'admin',status:'active',active:true,createdAt:Date.now(),updatedAt:Date.now()})
    return {ok:true as const}
  }
})
