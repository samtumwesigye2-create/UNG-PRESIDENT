import { getAuthUserId } from '@convex-dev/auth/server'
import { v } from 'convex/values'
import { mutation, query } from './_generated/server'

async function authorizedPublisher(ctx:any){
  const userId=await getAuthUserId(ctx)
  if(!userId) return null
  const user=await ctx.db.get(userId)
  const email=user?.email?.toLowerCase()
  if(!email) return null
  let profile=await ctx.db.query('staffProfiles').withIndex('by_user',(q:any)=>q.eq('userId',userId)).unique()
  if(!profile) profile=await ctx.db.query('staffProfiles').withIndex('by_email',(q:any)=>q.eq('email',email)).unique()
  const status=profile?.status ?? (profile?.active?'active':'pending')
  if(!profile?.active || status!=='active') return null
  if(!['president','admin','press'].includes(profile.role)) return null
  return {userId,profile}
}

export const listNotices = query({
  args:{},
  handler:async(ctx)=>{
    const actor=await authorizedPublisher(ctx)
    if(!actor) return {ok:false as const,code:'FORBIDDEN'}
    return {ok:true as const,notices:await ctx.db.query('emergencyNotices').order('desc').take(100)}
  },
})

export const saveNotice = mutation({
  args:{id:v.optional(v.id('emergencyNotices')),title:v.string(),message:v.string(),severity:v.union(v.literal('information'),v.literal('warning'),v.literal('emergency')),active:v.boolean(),startsAt:v.optional(v.number()),endsAt:v.optional(v.number())},
  handler:async(ctx,args)=>{
    const actor=await authorizedPublisher(ctx)
    if(!actor) return {ok:false as const,code:'FORBIDDEN',message:'President, administrator, or press authorization required.'}
    const now=Date.now()
    if(!args.title.trim()||!args.message.trim()) return {ok:false as const,code:'INVALID',message:'Title and message are required.'}
    if(args.endsAt && args.startsAt && args.endsAt<=args.startsAt) return {ok:false as const,code:'INVALID_WINDOW',message:'End time must be after start time.'}
    if(args.active){
      const active=await ctx.db.query('emergencyNotices').withIndex('by_active',(q:any)=>q.eq('active',true)).collect()
      for(const item of active) if(item._id!==args.id) await ctx.db.patch(item._id,{active:false,updatedBy:actor.userId,updatedAt:now})
    }
    let id=args.id
    if(id) await ctx.db.patch(id,{title:args.title.trim(),message:args.message.trim(),severity:args.severity,active:args.active,startsAt:args.startsAt,endsAt:args.endsAt,updatedBy:actor.userId,updatedAt:now})
    else id=await ctx.db.insert('emergencyNotices',{title:args.title.trim(),message:args.message.trim(),severity:args.severity,active:args.active,startsAt:args.startsAt,endsAt:args.endsAt,createdBy:actor.userId,updatedBy:actor.userId,createdAt:now,updatedAt:now})
    await ctx.db.insert('auditLog',{userId:actor.userId,action:'public_notice.save',entity:'emergencyNotice',entityId:String(id),details:`${args.severity}:${args.active?'active':'inactive'}`,createdAt:now})
    return {ok:true as const,id}
  },
})
