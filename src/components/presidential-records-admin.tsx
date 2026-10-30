import { type FormEvent, useState } from 'react'

type SaveResult = { ok:boolean; message?:string }
type Props = {
  onSaveEvent:(payload:any)=>Promise<SaveResult>|SaveResult
  onSaveDocument:(payload:any)=>Promise<SaveResult>|SaveResult
}

export function PresidentialRecordsAdmin({onSaveEvent,onSaveDocument}:Props){
  const [notice,setNotice]=useState<string|null>(null)
  const field='rounded-xl border border-slate-300 bg-white px-3 py-2'
  async function submitEvent(e:FormEvent<HTMLFormElement>){
    e.preventDefault(); const f=e.currentTarget,fd=new FormData(f)
    const r=await onSaveEvent({title:String(fd.get('title')),location:String(fd.get('location')||'')||undefined,eventDate:String(fd.get('eventDate')),description:String(fd.get('description')||'')||undefined,scope:String(fd.get('scope')),eventType:String(fd.get('eventType')),hostOffice:String(fd.get('hostOffice')||'')||undefined,counterpartCountry:String(fd.get('counterpartCountry')||'')||undefined,publicationStatus:String(fd.get('publicationStatus')),isPublic:true,status:'scheduled'})
    setNotice(r.ok?'Presidential event saved.':r.message||'Unable to save event.'); if(r.ok)f.reset()
  }
  async function submitDocument(e:FormEvent<HTMLFormElement>){
    e.preventDefault(); const f=e.currentTarget,fd=new FormData(f)
    const publicationDate=String(fd.get('publicationDate')||'')||undefined
    const r=await onSaveDocument({title:String(fd.get('title')),documentType:String(fd.get('documentType')),summary:String(fd.get('summary')||'')||undefined,topic:String(fd.get('topic')||'')||undefined,issuingOffice:String(fd.get('issuingOffice')),issuedBy:String(fd.get('issuedBy')),reference:String(fd.get('reference')),version:String(fd.get('version')),effectiveDate:String(fd.get('effectiveDate')||'')||undefined,publicationDate,year:publicationDate?.slice(0,4),sourceUrl:String(fd.get('sourceUrl')||'')||undefined,status:String(fd.get('status'))})
    setNotice(r.ok?'Official document saved.':r.message||'Unable to save official document.'); if(r.ok)f.reset()
  }
  return <section className="space-y-6">
    <div className="rounded-2xl bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold">Presidential event publishing</h2><p className="mt-1 text-sm text-slate-500">Classify every public presidential event before publication.</p>
      <form className="mt-4 grid gap-3 md:grid-cols-3" onSubmit={submitEvent}>
        <input name="title" required placeholder="Event title" className={field}/><input name="eventDate" type="date" required className={field}/><input name="location" placeholder="Location" className={field}/>
        <label className="grid gap-1 text-sm">Domestic or international<select aria-label="Domestic or international" name="scope" required className={field}><option value="domestic">Domestic / Home</option><option value="international">International / Abroad</option></select></label>
        <label className="grid gap-1 text-sm">Event type<select aria-label="Event type" name="eventType" required className={field}><option value="state_visit">State Visit</option><option value="public_appearance">Public Appearance</option><option value="ceremonial">Ceremonial Event</option><option value="official_meeting">Official Meeting</option><option value="other">Other</option></select></label>
        <label className="grid gap-1 text-sm">Publication state<select name="publicationStatus" className={field}><option value="draft">Draft</option><option value="review">Review</option><option value="approved">Approved</option><option value="published">Published</option><option value="archived">Archived</option></select></label>
        <input name="hostOffice" placeholder="Host / issuing office" className={field}/><input name="counterpartCountry" placeholder="Counterpart country (if applicable)" className={field}/><textarea name="description" placeholder="Event description" className={`${field} md:col-span-3`} rows={3}/><button className="rounded-xl bg-slate-950 px-4 py-2 font-semibold text-white md:col-span-3">Save presidential event</button>
      </form>
    </div>
    <div className="rounded-2xl bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold">Policies & Regulations publishing</h2><p className="mt-1 text-sm text-slate-500">Official references and issuing-office metadata are required; draft material is never public.</p>
      <form className="mt-4 grid gap-3 md:grid-cols-3" onSubmit={submitDocument}>
        <input name="title" required placeholder="Document title" className={`${field} md:col-span-2`}/><select name="documentType" className={field}><option value="policy">Policy</option><option value="regulation">Regulation</option><option value="executive_directive">Executive Directive</option><option value="legislation">Legislation</option><option value="proclamation">Proclamation</option><option value="cabinet_decision">Cabinet / Executive Decision</option><option value="other">Other</option></select>
        <label className="grid gap-1 text-sm">Official document reference<input aria-label="Official document reference" name="reference" required placeholder="Official reference" className={field}/></label><input name="version" required placeholder="Version, e.g. 1.0" className={field}/><input name="topic" placeholder="Topic" className={field}/><input name="issuingOffice" required placeholder="Issuing office" className={field}/><input name="issuedBy" required placeholder="Issued by" className={field}/><input name="publicationDate" type="date" className={field}/><input name="effectiveDate" type="date" className={field}/><input name="sourceUrl" type="url" placeholder="Official document URL" className={`${field} md:col-span-2`}/>
        <label className="grid gap-1 text-sm">Publication status<select aria-label="Publication status" name="status" className={field}><option value="draft">Draft</option><option value="review">Review</option><option value="approved">Approved</option><option value="published">Published</option><option value="archived">Archived</option></select></label><textarea name="summary" placeholder="Public summary" className={`${field} md:col-span-3`} rows={3}/><button className="rounded-xl bg-slate-950 px-4 py-2 font-semibold text-white md:col-span-3">Save official document</button>
      </form>
    </div>
    {notice?<p className="rounded-xl bg-white p-4 text-sm shadow-sm">{notice}</p>:null}
  </section>
}
