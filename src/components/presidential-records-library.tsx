import { useMemo, useState } from 'react'
import { classifyPublicEvents, filterOfficialDocuments, type OfficialDocument, type PublicEvent } from '../lib/presidential-records'

type Props = { events?: PublicEvent[]; documents?: OfficialDocument[] }

const eventLabels: Record<string,string> = {
  state_visit:'State Visit',
  public_appearance:'Public Appearance',
  ceremonial:'Ceremonial Event',
  official_meeting:'Official Meeting',
  other:'Presidential Event',
}

const documentLabels: Record<string,string> = {
  policy:'Policy', regulation:'Regulation', executive_directive:'Executive Directive', legislation:'Legislation', proclamation:'Proclamation', cabinet_decision:'Cabinet / Executive Decision', other:'Official Document',
}

export function PresidentialRecordsLibrary({events=[],documents=[]}:Props) {
  const classified=useMemo(()=>classifyPublicEvents(events),[events])
  const [documentType,setDocumentType]=useState<'all'|OfficialDocument['documentType']>('all')
  const visibleDocuments=useMemo(()=>filterOfficialDocuments(documents,{documentType,status:'published'}),[documents,documentType])

  const eventList=(items:PublicEvent[])=>items.length ? items.map(event=><article key={String(event._id)} className="presidential-record-card">
    <div className="record-meta"><span>{eventLabels[event.eventType||'other']||'Presidential Event'}</span><time>{event.eventDate}</time></div>
    <h3>{event.title}</h3>
    {event.location?<p>{String(event.location)}</p>:null}
    {event.counterpartCountry?<p className="record-note">Counterpart: {String(event.counterpartCountry)}</p>:null}
  </article>) : <p className="empty-state">No published events are currently listed.</p>

  return <section className="formal-section presidential-records-library" id="presidential-calendar">
    <div className="container">
      <div className="section-head"><div><span className="section-kicker">Presidential Diary</span><h2>Upcoming Presidential Events</h2></div><p>Only public events released by authorized Presidency staff are shown.</p></div>
      <div className="presidential-calendar-grid">
        <div><h3>Domestic / Home</h3>{eventList(classified.domestic)}</div>
        <div><h3>International / Abroad</h3>{eventList(classified.international)}</div>
      </div>

      <div className="records-library-head" id="policies-regulations">
        <div><span className="section-kicker">Policies & Regulations</span><h2>Official Presidential Documents</h2></div>
        <label>Document type
          <select value={documentType} onChange={event=>setDocumentType(event.target.value as typeof documentType)}>
            <option value="all">All published documents</option><option value="policy">Policies</option><option value="regulation">Regulations</option><option value="executive_directive">Executive Directives</option><option value="legislation">Legislation</option><option value="proclamation">Proclamations</option><option value="cabinet_decision">Cabinet / Executive Decisions</option><option value="other">Other</option>
          </select>
        </label>
      </div>
      <div className="official-document-grid">{visibleDocuments.length?visibleDocuments.map(document=><article key={String(document._id)} className="official-document-card">
        <div className="record-meta"><span>{documentLabels[document.documentType]}</span><span>{document.status}</span></div>
        <h3>{document.title}</h3>
        <dl><div><dt>Reference</dt><dd>{document.reference}</dd></div><div><dt>Issued by</dt><dd>{document.issuedBy}</dd></div>{document.version?<div><dt>Version</dt><dd>{String(document.version)}</dd></div>:null}{document.publicationDate?<div><dt>Published</dt><dd>{String(document.publicationDate)}</dd></div>:null}</dl>
        {document.summary?<p>{String(document.summary)}</p>:null}
        <div className="flex flex-wrap gap-3">
          <a href={`/verify/${encodeURIComponent(document.reference)}`}>Verify official record</a>
          {document.sourceUrl?<a href={String(document.sourceUrl)} target="_blank" rel="noreferrer">Source document</a>:null}
        </div>
      </article>):<p className="empty-state">No published policies or regulations are available yet.</p>}</div>
    </div>
  </section>
}
