import { getAuthUserId } from '@convex-dev/auth/server'
import { v } from 'convex/values'
import { mutation, query } from './_generated/server'

const publicationStatus = v.union(v.literal('draft'),v.literal('review'),v.literal('approved'),v.literal('published'),v.literal('archived'))
const eventScope = v.union(v.literal('domestic'),v.literal('international'))
const presidentialEventType = v.union(v.literal('state_visit'),v.literal('public_appearance'),v.literal('ceremonial'),v.literal('official_meeting'),v.literal('other'))
const officialDocumentType = v.union(v.literal('policy'),v.literal('regulation'),v.literal('executive_directive'),v.literal('legislation'),v.literal('proclamation'),v.literal('cabinet_decision'),v.literal('other'))

type PublicationStatus = 'draft'|'review'|'approved'|'published'|'archived'
const transitions: Record<PublicationStatus, PublicationStatus[]> = {
  draft:['review','archived'],
  review:['draft','approved','archived'],
  approved:['review','published','archived'],
  published:['archived'],
  archived:[],
}

async function authorizedEditor(ctx:any) {
  const userId=await getAuthUserId(ctx)
  if(!userId) return null
  const user=await ctx.db.get(userId)
  const email=user?.email?.toLowerCase()
  if(!email) return null
  let profile=await ctx.db.query('staffProfiles').withIndex('by_user',(q:any)=>q.eq('userId',userId)).unique()
  if(!profile) profile=await ctx.db.query('staffProfiles').withIndex('by_email',(q:any)=>q.eq('email',email)).unique()
  const status=profile?.status ?? (profile?.active?'active':'pending')
  if(!profile?.active || status!=='active') return null
  if(!['president','admin','staff','protocol','press'].includes(profile.role)) return null
  return {userId,profile}
}

function canPublish(role:string) { return role==='president' || role==='admin' }

export const listOfficialDocuments = query({
  args:{},
  handler:async(ctx)=>{
    const actor=await authorizedEditor(ctx)
    if(!actor) return {ok:false as const,code:'FORBIDDEN',message:'Active authorized staff access required.'}
    return {ok:true as const,documents:await ctx.db.query('officialDocuments').order('desc').take(250)}
  },
})

export const listDocumentRevisions = query({
  args:{documentId:v.id('officialDocuments')},
  handler:async(ctx,args)=>{
    const actor=await authorizedEditor(ctx)
    if(!actor) return {ok:false as const,code:'FORBIDDEN',message:'Active authorized staff access required.'}
    const revisions=await ctx.db.query('officialDocumentRevisions').withIndex('by_document',q=>q.eq('documentId',args.documentId)).collect()
    revisions.sort((a,b)=>b.revisionNumber-a.revisionNumber)
    return {ok:true as const,revisions}
  },
})

export const saveEvent = mutation({
  args:{ id:v.optional(v.id('stateFunctions')), title:v.string(), location:v.optional(v.string()), eventDate:v.string(), description:v.optional(v.string()), scope:eventScope, eventType:presidentialEventType, hostOffice:v.optional(v.string()), counterpartCountry:v.optional(v.string()), publicationStatus, isPublic:v.boolean(), status:v.string() },
  handler:async(ctx,args)=>{
    const actor=await authorizedEditor(ctx)
    if(!actor) return {ok:false as const,code:'FORBIDDEN',message:'Active authorized staff access required.'}
    if((args.publicationStatus==='published'||args.publicationStatus==='archived')&&!canPublish(actor.profile.role)) return {ok:false as const,code:'PUBLISH_FORBIDDEN',message:'President or administrator approval is required to publish or archive presidential events.'}
    const now=Date.now()
    if(args.id){
      const existing=await ctx.db.get(args.id)
      if(!existing) return {ok:false as const,code:'NOT_FOUND',message:'Event not found.'}
      const from=(existing.publicationStatus??'draft') as PublicationStatus
      if(from!==args.publicationStatus && !transitions[from].includes(args.publicationStatus)) return {ok:false as const,code:'INVALID_TRANSITION',message:`Cannot move event from ${from} to ${args.publicationStatus}.`}
      await ctx.db.patch(args.id,{...args,functionType:args.eventType,publishedAt:args.publicationStatus==='published'?(existing.publishedAt??now):existing.publishedAt,updatedBy:actor.userId,updatedAt:now})
      await ctx.db.insert('auditLog',{userId:actor.userId,action:'presidential_event.update',entity:'stateFunction',entityId:String(args.id),details:`${args.eventType}:${args.scope}:${args.publicationStatus}`,createdAt:now})
      return {ok:true as const,id:args.id}
    }
    const id=await ctx.db.insert('stateFunctions',{title:args.title.trim(),functionType:args.eventType,location:args.location,eventDate:args.eventDate,description:args.description,isPublic:args.isPublic,status:args.status,scope:args.scope,eventType:args.eventType,hostOffice:args.hostOffice,counterpartCountry:args.counterpartCountry,publicationStatus:args.publicationStatus,publishedAt:args.publicationStatus==='published'?now:undefined,createdBy:actor.userId,updatedBy:actor.userId,createdAt:now,updatedAt:now})
    await ctx.db.insert('auditLog',{userId:actor.userId,action:'presidential_event.create',entity:'stateFunction',entityId:String(id),details:`${args.eventType}:${args.scope}:${args.publicationStatus}`,createdAt:now})
    return {ok:true as const,id}
  }
})

export const saveOfficialDocument = mutation({
  args:{ id:v.optional(v.id('officialDocuments')), title:v.string(), documentType:officialDocumentType, summary:v.optional(v.string()), body:v.optional(v.string()), topic:v.optional(v.string()), issuingOffice:v.string(), issuedBy:v.string(), reference:v.string(), version:v.string(), effectiveDate:v.optional(v.string()), publicationDate:v.optional(v.string()), year:v.optional(v.string()), sourceUrl:v.optional(v.string()), status:publicationStatus },
  handler:async(ctx,args)=>{
    const actor=await authorizedEditor(ctx)
    if(!actor) return {ok:false as const,code:'FORBIDDEN',message:'Active authorized staff access required.'}
    if((args.status==='published'||args.status==='archived')&&!canPublish(actor.profile.role)) return {ok:false as const,code:'PUBLISH_FORBIDDEN',message:'President or administrator approval is required to publish or archive official documents.'}
    const reference=args.reference.trim()
    if(!reference) return {ok:false as const,code:'REFERENCE_REQUIRED',message:'An official document reference is required.'}
    const existingRef=await ctx.db.query('officialDocuments').withIndex('by_reference',q=>q.eq('reference',reference)).unique()
    if(existingRef && existingRef._id!==args.id) return {ok:false as const,code:'DUPLICATE_REFERENCE',message:'That official document reference is already in use.'}
    const now=Date.now()
    if(args.id){
      const existing=await ctx.db.get(args.id)
      if(!existing) return {ok:false as const,code:'NOT_FOUND',message:'Official document not found.'}
      const from=existing.status as PublicationStatus
      if(from!==args.status&&!transitions[from].includes(args.status)) return {ok:false as const,code:'INVALID_TRANSITION',message:`Cannot move document from ${from} to ${args.status}.`}

      const priorRevisions=await ctx.db.query('officialDocumentRevisions').withIndex('by_document',q=>q.eq('documentId',args.id!)).collect()
      const revisionNumber=priorRevisions.reduce((max,r)=>Math.max(max,r.revisionNumber),0)+1
      await ctx.db.insert('officialDocumentRevisions',{
        documentId:args.id,
        reference:existing.reference,
        revisionNumber,
        title:existing.title,
        documentType:existing.documentType,
        summary:existing.summary,
        body:existing.body,
        topic:existing.topic,
        issuingOffice:existing.issuingOffice,
        issuedBy:existing.issuedBy,
        version:existing.version,
        effectiveDate:existing.effectiveDate,
        publicationDate:existing.publicationDate,
        year:existing.year,
        sourceUrl:existing.sourceUrl,
        status:existing.status,
        publishedAt:existing.publishedAt,
        archivedAt:existing.archivedAt,
        changedBy:actor.userId,
        changedAt:now,
      })

      await ctx.db.patch(args.id,{...args,reference,publishedAt:args.status==='published'?(existing.publishedAt??now):existing.publishedAt,archivedAt:args.status==='archived'?now:existing.archivedAt,updatedBy:actor.userId,updatedAt:now})
      await ctx.db.insert('auditLog',{userId:actor.userId,action:'official_document.update',entity:'officialDocument',entityId:String(args.id),details:`${reference}:${args.status}:revision-${revisionNumber}`,createdAt:now})
      return {ok:true as const,id:args.id,revisionNumber}
    }
    const id=await ctx.db.insert('officialDocuments',{title:args.title.trim(),documentType:args.documentType,summary:args.summary,body:args.body,topic:args.topic,issuingOffice:args.issuingOffice.trim(),issuedBy:args.issuedBy.trim(),reference,version:args.version.trim(),effectiveDate:args.effectiveDate,publicationDate:args.publicationDate,year:args.year,sourceUrl:args.sourceUrl,status:args.status,publishedAt:args.status==='published'?now:undefined,archivedAt:args.status==='archived'?now:undefined,createdBy:actor.userId,updatedBy:actor.userId,createdAt:now,updatedAt:now})
    await ctx.db.insert('auditLog',{userId:actor.userId,action:'official_document.create',entity:'officialDocument',entityId:String(id),details:`${reference}:${args.status}`,createdAt:now})
    return {ok:true as const,id}
  }
})
