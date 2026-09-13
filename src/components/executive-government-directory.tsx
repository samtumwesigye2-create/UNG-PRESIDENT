import { VicePresidentSeal, VicePresidentialFlag } from './vice-president-seal'
type Props = {
  offices?: any[]
  departments?: any[]
}

function OfficeCard({ office }: { office: any }) {
  const vp = office?.kind === 'vice_president'
  return <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
    <div className="flex items-start gap-5">
      {vp ? <div className="h-32 w-32 shrink-0 overflow-hidden rounded-full border border-amber-300 bg-white shadow-sm"><VicePresidentSeal className="h-full w-full" /></div> : null}
      <div className="min-w-0 flex-1">
        <p className="text-xs font-semibold uppercase tracking-[.2em] text-amber-700">{vp ? 'Vice Presidency' : 'Office of the Prime Minister'}</p>
        <h3 className="mt-2 font-serif text-2xl text-slate-950">{office?.name || (vp ? 'Office of the Vice President' : 'Office of the Prime Minister')}</h3>
        {office?.leaderName ? <p className="mt-2 text-sm font-medium text-slate-700">{office.leaderName}{office.leaderTitle ? ` · ${office.leaderTitle}` : ''}</p> : null}
      </div>
    </div>
    {vp ? <div className="mt-5"><VicePresidentialFlag /></div> : null}
    {office?.mandate ? <p className="mt-5 text-sm leading-6 text-slate-600">{office.mandate}</p> : <p className="mt-5 text-sm text-slate-500">Official responsibilities and leadership details will appear here after authorized publication.</p>}
    {office?.functions ? <p className="mt-3 text-sm leading-6 text-slate-600">{office.functions}</p> : null}
    {(office?.website || office?.email || office?.phone) ? <div className="mt-5 flex flex-wrap gap-3 text-sm">{office.website ? <a className="underline" href={office.website}>Official website</a> : null}{office.email ? <a className="underline" href={`mailto:${office.email}`}>Email office</a> : null}{office.phone ? <span>{office.phone}</span> : null}</div> : null}
  </article>
}

export function ExecutiveGovernmentDirectory({ offices = [], departments = [] }: Props) {
  const vp = offices.find(x => x.kind === 'vice_president')
  const pm = offices.find(x => x.kind === 'prime_minister')
  return <section id="executive-government" className="bg-slate-50 py-20">
    <div className="container">
      <div className="mb-10 max-w-3xl"><span className="section-kicker">Executive Government</span><h2 className="mt-3 font-serif text-4xl text-slate-950">Offices and executive departments</h2><p className="mt-4 text-slate-600">Only information published by authorized Presidency staff appears in this directory. Unpublished leadership, contact and mandate information is not inferred or filled in.</p></div>
      <div className="grid gap-6 lg:grid-cols-2"><OfficeCard office={vp || {kind:'vice_president',name:'Office of the Vice President'}}/><OfficeCard office={pm || {kind:'prime_minister',name:'Office of the Prime Minister'}}/></div>
      <div className="mt-10 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[.2em] text-amber-700">Departments & Ministries</p><h3 className="mt-2 font-serif text-2xl">Executive Government Directory</h3></div><span className="text-sm text-slate-500">{departments.length} published</span></div>
        {departments.length ? <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{departments.map(d => <article key={d._id} className="rounded-2xl border border-slate-200 p-4"><h4 className="font-semibold text-slate-950">{d.name}</h4>{d.shortName ? <p className="text-xs uppercase tracking-wide text-slate-500">{d.shortName}</p> : null}{d.mandate ? <p className="mt-3 text-sm leading-6 text-slate-600">{d.mandate}</p> : null}{d.leaderName ? <p className="mt-3 text-sm font-medium">{d.leaderName}{d.leaderTitle ? ` · ${d.leaderTitle}` : ''}</p> : null}{d.website ? <a className="mt-3 inline-block text-sm underline" href={d.website}>Official link</a> : null}</article>)}</div> : <p className="mt-6 rounded-2xl border border-dashed border-slate-300 p-5 text-sm text-slate-500">No executive departments or ministries have been published yet.</p>}
      </div>
    </div>
  </section>
}
