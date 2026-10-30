type VerifiedDocument = {
  title:string
  documentType:string
  summary?:string
  body?:string
  topic?:string
  issuingOffice:string
  issuedBy:string
  reference:string
  version:string
  effectiveDate?:string
  publicationDate?:string
  year?:string
  sourceUrl?:string
  status:string
  publishedAt?:number
  archivedAt?:number
  updatedAt:number
}

function formatTimestamp(value?:number) {
  return value ? new Date(value).toLocaleString() : 'Not recorded'
}

export function OfficialDocumentVerificationView({document}:{document:VerifiedDocument}) {
  return <main className="min-h-screen bg-slate-100 px-4 py-8 text-slate-950 print:bg-white print:p-0">
    <article className="mx-auto max-w-4xl overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm print:max-w-none print:rounded-none print:border-0 print:shadow-none">
      <div className="h-2 grid grid-cols-3" aria-hidden="true"><span className="bg-black"/><span className="bg-amber-400"/><span className="bg-red-700"/></div>
      <header className="border-b border-slate-200 px-7 py-7 md:px-10">
        <p className="text-xs font-semibold uppercase tracking-[.24em] text-amber-700">Republic of Uganda · Office of the President</p>
        <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
          <div><p className="text-sm font-semibold uppercase tracking-wide text-emerald-700">Verified Official Record</p><h1 className="mt-2 text-3xl font-semibold">{document.title}</h1></div>
          <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-800">{document.status}</span>
        </div>
      </header>

      <section className="grid gap-4 border-b border-slate-200 bg-slate-50 px-7 py-6 md:grid-cols-2 md:px-10">
        <div><span className="text-xs uppercase tracking-wide text-slate-500">Official reference</span><strong className="mt-1 block">{document.reference}</strong></div>
        <div><span className="text-xs uppercase tracking-wide text-slate-500">Version</span><strong className="mt-1 block">{document.version}</strong></div>
        <div><span className="text-xs uppercase tracking-wide text-slate-500">Issued by</span><strong className="mt-1 block">{document.issuedBy}</strong></div>
        <div><span className="text-xs uppercase tracking-wide text-slate-500">Issuing office</span><strong className="mt-1 block">{document.issuingOffice}</strong></div>
        <div><span className="text-xs uppercase tracking-wide text-slate-500">Publication timestamp</span><strong className="mt-1 block">{formatTimestamp(document.publishedAt)}</strong></div>
        <div><span className="text-xs uppercase tracking-wide text-slate-500">Last updated</span><strong className="mt-1 block">{formatTimestamp(document.updatedAt)}</strong></div>
      </section>

      <section className="space-y-6 px-7 py-8 md:px-10">
        {document.summary?<div><h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Official summary</h2><p className="mt-2 leading-7">{document.summary}</p></div>:null}
        {document.body?<div><h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Official text</h2><div className="mt-2 whitespace-pre-wrap leading-7">{document.body}</div></div>:null}
        <div className="grid gap-4 sm:grid-cols-2">
          {document.effectiveDate?<div><span className="text-xs uppercase tracking-wide text-slate-500">Effective date</span><p className="mt-1">{document.effectiveDate}</p></div>:null}
          {document.publicationDate?<div><span className="text-xs uppercase tracking-wide text-slate-500">Publication date</span><p className="mt-1">{document.publicationDate}</p></div>:null}
          {document.topic?<div><span className="text-xs uppercase tracking-wide text-slate-500">Topic</span><p className="mt-1">{document.topic}</p></div>:null}
          <div><span className="text-xs uppercase tracking-wide text-slate-500">Document type</span><p className="mt-1">{document.documentType.replaceAll('_',' ')}</p></div>
        </div>
      </section>

      <footer className="flex flex-wrap items-center gap-3 border-t border-slate-200 px-7 py-6 md:px-10 print:hidden">
        <button type="button" onClick={()=>window.print()} className="rounded-xl bg-slate-950 px-4 py-2 font-semibold text-white">Print official record</button>
        {document.sourceUrl?<a href={document.sourceUrl} target="_blank" rel="noreferrer" className="rounded-xl border border-slate-300 px-4 py-2 font-semibold">Source document</a>:null}
        <a href="/" className="ml-auto text-sm font-semibold text-slate-600">Return to Presidency portal</a>
      </footer>
    </article>
  </main>
}
