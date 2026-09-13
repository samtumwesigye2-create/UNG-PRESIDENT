import { mutation, query } from './_generated/server'
import { v } from 'convex/values'

export const homepage = query({
  args: {},
  returns: v.object({
    executiveOrders: v.array(v.any()), press: v.array(v.any()), events: v.array(v.any()), milestones: v.array(v.any()), legislation: v.array(v.any()), gallery: v.array(v.any()), youthPrograms: v.array(v.any()), executiveOffices:v.array(v.any()), executiveDepartments:v.array(v.any()),
  }),
  handler: async (ctx) => ({
    executiveOrders: await ctx.db.query('executiveOrders').withIndex('by_status', q => q.eq('status','issued')).order('desc').take(20),
    press: await ctx.db.query('pressStatements').withIndex('by_status', q => q.eq('status','released')).order('desc').take(20),
    events: await ctx.db.query('stateFunctions').withIndex('by_public_status', q => q.eq('isPublic', true).eq('status','scheduled')).order('asc').take(20),
    milestones: await ctx.db.query('milestones').withIndex('by_status', q => q.eq('status','active')).order('desc').take(30),
    legislation: await ctx.db.query('legislation').order('desc').take(30),
    gallery: await ctx.db.query('galleryItems').withIndex('by_status', q => q.eq('status','active')).order('desc').take(24),
    youthPrograms: await ctx.db.query('youthPrograms').withIndex('by_status', q => q.eq('status','open')).order('desc').take(30),
    executiveOffices: await ctx.db.query('executiveOffices').withIndex('by_status', q => q.eq('status','published')).order('desc').take(10),
    executiveDepartments: await ctx.db.query('executiveDepartments').withIndex('by_status', q => q.eq('status','published')).order('desc').take(100),
  }),
})

export const submitContact = mutation({
  args: { name:v.string(), email:v.string(), subject:v.string(), message:v.string() },
  returns: v.id('contactMessages'),
  handler: async (ctx, a) => {
    if (!a.name.trim() || !a.email.includes('@') || !a.subject.trim() || !a.message.trim()) throw new Error('All fields are required')
    return ctx.db.insert('contactMessages', {...a, status:'new', createdAt:Date.now()})
  },
})

export const submitVisitRequest = mutation({
  args: { visitorName:v.string(), email:v.string(), phone:v.optional(v.string()), country:v.optional(v.string()), organization:v.optional(v.string()), visitCategory:v.string(), groupSize:v.number(), purpose:v.string(), preferredDate:v.string(), alternateDate:v.optional(v.string()) },
  returns: v.string(),
  handler: async (ctx, a) => {
    if (!a.visitorName.trim() || !a.email.includes('@') || !a.purpose.trim() || a.groupSize < 1 || a.groupSize > 500) throw new Error('Invalid visit request')
    const ref = `SH-${new Date().getUTCFullYear()}-${Math.floor(100000 + Math.random()*900000)}`
    await ctx.db.insert('visitorRequests', {...a, status:'pending', referenceNumber:ref, createdAt:Date.now()})
    return ref
  },
})

export const subscribe = mutation({
  args: { email:v.string() },
  returns: v.boolean(),
  handler: async (ctx, {email}) => {
    if (!email.includes('@')) throw new Error('Enter a valid email')
    const existing = await ctx.db.query('newsletterSubscribers').withIndex('by_email', q => q.eq('email', email.toLowerCase())).unique()
    if (existing) return false
    await ctx.db.insert('newsletterSubscribers', { email:email.toLowerCase(), subscribedAt:Date.now(), unsubscribed:false })
    return true
  },
})
