import { useMemo, useState } from 'react'

export type GovernmentSearchRecord={title:string;kind:string;office:string;status:string;href:string;year?:string;topic?:string}

export function searchGovernmentContent(records:GovernmentSearchRecord[],query:string){
  const q=query.trim().toLowerCase()
  if(!q) return []
  return records.filter(r=>[r.title,r.kind,r.office,r.status,r.year,r.topic].filter(Boolean).join(' ').toLowerCase().includes(q))
}

export function GovernmentDiscovery({records}:{records:GovernmentSearchRecord[]}){
  const [query,setQuery]=useState('')
  const [kind,setKind]=useState('all')
  const results=useMemo(()=>searchGovernmentContent(records,query).filter(r=>kind==='all'||r.kind===kind),[records,query,kind])
  const kinds=useMemo(()=>Array.from(new Set(records.map(r=>r.kind))).sort(),[records])
  const directory=useMemo(()=>Array.from(new Map(records.filter(r=>r.office).map(r=>[r.office,{name:r.office,href:r.href}])).values()).sort((a,b)=>a.name.localeCompare(b.name)),[records])
  return <section className="government-discovery formal-section" id="government-directory"><div className="container">
    <nav className="breadcrumbs" aria-label="Breadcrumb"><a href="#presidency">Presidency</a><span>/</span><span>Government Directory & Search</span></nav>
    <div className="section-head"><div><span className="section-kicker">Official Discovery</span><h2>Search the Presidency & Executive Government</h2></div><p>Search published Presidency records, executive offices, events, policies and government directory entries.</p></div>
    <div className="government-search-panel">
      <label className="government-search-label">Search official Presidency content<input aria-label="Search official Presidency content" type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search orders, policies, offices, events…"/></label>
      <label>Filter by type<select value={kind} onChange={e=>setKind(e.target.value)}><option value="all">All types</option>{kinds.map(k=><option key={k} value={k}>{k}</option>)}</select></label>
    </div>
    {query?<div className="government-search-results" aria-live="polite">{results.length?results.map((r,i)=><a key={`${r.title}-${i}`} href={r.href}><span>{r.kind}</span><strong>{r.title}</strong><small>{r.office} · {r.status}</small></a>):<p className="empty-state">No matching published Presidency content.</p>}</div>:null}
    <div className="government-discovery-grid">
      <article className="government-glance"><span className="section-kicker">Executive Structure</span><h2>Government at a Glance</h2><div className="glance-links"><a href="#presidency"><strong>President</strong><span>Head of the Presidency</span></a><a href="#executive-government"><strong>Vice President</strong><span>Executive Office</span></a><a href="#executive-government"><strong>Prime Minister</strong><span>Executive Office</span></a><a href="#executive-government"><strong>Departments / Ministries</strong><span>Executive Government directory</span></a></div></article>
      <article className="az-directory"><span className="section-kicker">Directory</span><h2>A–Z Government Directory</h2>{directory.length?<div className="az-list">{directory.map(item=><a href={item.href} key={item.name}><b>{item.name.slice(0,1).toUpperCase()}</b><span>{item.name}</span></a>)}</div>:<p className="empty-state">Published executive offices and departments will appear here after staff approval.</p>}</article>
    </div>
  </div></section>
}
