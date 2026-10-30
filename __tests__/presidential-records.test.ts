import { describe, expect, it } from 'vitest'
import { classifyPublicEvents, filterOfficialDocuments } from '@/lib/presidential-records'

describe('presidential events and official documents', () => {
  it('separates domestic and international public events and preserves event types', () => {
    const events = [
      { _id:'1', title:'A', eventDate:'2026-10-01', isPublic:true, status:'scheduled', scope:'domestic', eventType:'public_appearance' },
      { _id:'2', title:'B', eventDate:'2026-10-02', isPublic:true, status:'scheduled', scope:'international', eventType:'state_visit' },
      { _id:'3', title:'C', eventDate:'2026-10-03', isPublic:false, status:'scheduled', scope:'domestic', eventType:'ceremonial' },
    ] as any[]
    const result = classifyPublicEvents(events)
    expect(result.domestic.map(x=>x._id)).toEqual(['1'])
    expect(result.international.map(x=>x._id)).toEqual(['2'])
    expect(result.international[0].eventType).toBe('state_visit')
  })

  it('returns only published official documents and supports type/status filters without fabricating fields', () => {
    const docs = [
      { _id:'p1', title:'Policy A', documentType:'policy', status:'published', issuedBy:'Office of the President', reference:'OP-POL-001' },
      { _id:'r1', title:'Regulation A', documentType:'regulation', status:'published', issuedBy:'Office of the President', reference:'OP-REG-001' },
      { _id:'d1', title:'Draft', documentType:'policy', status:'draft', issuedBy:'Office of the President', reference:'OP-POL-002' },
    ] as any[]
    const result = filterOfficialDocuments(docs, { documentType:'policy', status:'published' })
    expect(result.map(x=>x._id)).toEqual(['p1'])
    expect(result[0]).not.toHaveProperty('summary')
  })
})
