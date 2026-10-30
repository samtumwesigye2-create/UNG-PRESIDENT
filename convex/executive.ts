import { getAuthUserId } from '@convex-dev/auth/server'
import { v } from 'convex/values'
import { mutation, query } from './_generated/server'

const statusValidator = v.union(v.literal('draft'),v.literal('review'),v.literal('approved'),v.literal('published'),v.literal('archived'))
const officeKind = v.union(v.literal('vice_president'),v.literal('prime_minister'))

async function manager(ctx:any) {
  const userId = await getAuthUserId(ctx)
  if (!userId) return null
  const profile = await ctx.db.query('staffProfiles').withIndex('by_user',(q:any)=>q.eq('userId',userId)).unique()
  const status = profile?.status ?? (profile?.active ? 'active' : 'pending')
  if (!profile?.active || status !== 'active') return null
  if (!['president','admin','staff'].includes(profile.role)) return null
  return { userId, profile }
}

export const listForStaff = query({
  args:{},
  handler:async(ctx)=>{
    const actor=await manager(ctx)
    if(!actor) return {ok:false as const,code:'FORBIDDEN',message:'Executive-government editorial access required.'}
    return {ok:true as const,offices:await ctx.db.query('executiveOffices').order('desc').take(50),departments:await ctx.db.query('executiveDepartments').order('desc').take(250)}
  }
})

export const saveOffice = mutation({
  args:{id:v.optional(v.id('executiveOffices')),kind:officeKind,name:v.string(),mandate:v.optional(v.string()),functions:v.optional(v.string()),leaderName:v.optional(v.string()),leaderTitle:v.optional(v.string()),phone:v.optional(v.string()),email:v.optional(v.string()),website:v.optional(v.string()),officeAddress:v.optional(v.string()),status:statusValidator},
  handler:async(ctx,args)=>{
    const actor=await manager(ctx)
    if(!actor) return {ok:false as const,code:'FORBIDDEN',message:'Executive-government editorial access required.'}
    const now=Date.now()
    const fields={kind:args.kind,name:args.name.trim(),mandate:args.mandate?.trim()||undefined,functions:args.functions?.trim()||undefined,leaderName:args.leaderName?.trim()||undefined,leaderTitle:args.leaderTitle?.trim()||undefined,phone:args.phone?.trim()||undefined,email:args.email?.trim()||undefined,website:args.website?.trim()||undefined,officeAddress:args.officeAddress?.trim()||undefined,status:args.status,publishedAt:args.status==='published'?now:undefined,updatedBy:actor.userId,updatedAt:now}
    let id=args.id
    if(id){const existing=await ctx.db.get(id);if(!existing)return {ok:false as const,code:'NOT_FOUND',message:'Executive office not found.'};await ctx.db.patch(id,fields)}
    else{id=await ctx.db.insert('executiveOffices',{...fields,createdBy:actor.userId,createdAt:now})}
    await ctx.db.insert('auditLog',{userId:actor.userId,action:'executive.office.save',entity:'executiveOffice',entityId:String(id),details:`${args.kind}:${args.status}`,createdAt:now})
    return {ok:true as const,id}
  }
})

export const saveDepartment = mutation({
  args:{id:v.optional(v.id('executiveDepartments')),name:v.string(),shortName:v.optional(v.string()),mandate:v.optional(v.string()),functions:v.optional(v.string()),leaderName:v.optional(v.string()),leaderTitle:v.optional(v.string()),phone:v.optional(v.string()),email:v.optional(v.string()),website:v.optional(v.string()),officeAddress:v.optional(v.string()),sortOrder:v.optional(v.number()),status:statusValidator},
  handler:async(ctx,args)=>{
    const actor=await manager(ctx)
    if(!actor) return {ok:false as const,code:'FORBIDDEN',message:'Executive-government editorial access required.'}
    const now=Date.now()
    const fields={name:args.name.trim(),shortName:args.shortName?.trim()||undefined,mandate:args.mandate?.trim()||undefined,functions:args.functions?.trim()||undefined,leaderName:args.leaderName?.trim()||undefined,leaderTitle:args.leaderTitle?.trim()||undefined,phone:args.phone?.trim()||undefined,email:args.email?.trim()||undefined,website:args.website?.trim()||undefined,officeAddress:args.officeAddress?.trim()||undefined,sortOrder:args.sortOrder,status:args.status,publishedAt:args.status==='published'?now:undefined,updatedBy:actor.userId,updatedAt:now}
    let id=args.id
    if(id){const existing=await ctx.db.get(id);if(!existing)return {ok:false as const,code:'NOT_FOUND',message:'Executive department not found.'};await ctx.db.patch(id,fields)}
    else{id=await ctx.db.insert('executiveDepartments',{...fields,createdBy:actor.userId,createdAt:now})}
    await ctx.db.insert('auditLog',{userId:actor.userId,action:'executive.department.save',entity:'executiveDepartment',entityId:String(id),details:`${args.name.trim()}:${args.status}`,createdAt:now})
    return {ok:true as const,id}
  }
})
