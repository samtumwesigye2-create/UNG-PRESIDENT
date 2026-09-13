import { createFileRoute } from '@tanstack/react-router'
import { useMutation, useQuery } from 'convex/react'
import { api } from '../../convex/_generated/api'
import { FormEvent, useState } from 'react'
import { ExecutiveGovernmentDirectory } from '../components/executive-government-directory'

export const Route = createFileRoute('/')({ component: PresidentHome })

const PRESIDENTIAL_STANDARD = 'https://assets.macaly-user-data.dev/cdn-cgi/image/format=webp,width=2000,height=2000,fit=scale-down,quality=85,anim=false/w5xb3too087c17afd6dv9mov/es9cbxmoiix2ab2r0cemhfzx/h_Il2OuQtYfn0pk_AjEhC.jpeg'
const PRESIDENTIAL_SEAL = 'https://assets.macaly-user-data.dev/cdn-cgi/image/format=webp,width=2000,height=2000,fit=scale-down,quality=85,anim=false/w5xb3too087c17afd6dv9mov/es9cbxmoiix2ab2r0cemhfzx/nO8TOweGAmSWEz5Jojfg0.jpeg'
const HERO_PHOTO = 'https://assets.macaly-user-data.dev/cdn-cgi/image/format=webp,width=2000,height=2000,fit=scale-down,quality=85,anim=false/w5xb3too087c17afd6dv9mov/es9cbxmoiix2ab2r0cemhfzx/0GNEy1EzABEvWsyoKN8b2.jpeg'
const CEREMONIAL_PHOTO = 'https://assets.macaly-user-data.dev/cdn-cgi/image/format=webp,width=2000,height=2000,fit=scale-down,quality=85,anim=false/w5xb3too087c17afd6dv9mov/es9cbxmoiix2ab2r0cemhfzx/cX1jvSh2aF8KtsBomeaSg.jpeg'

export function PresidentHome() {
  const data = useQuery(api.public.homepage)
  const submitContact = useMutation(api.public.submitContact)
  const submitVisit = useMutation(api.public.submitVisitRequest)
  const subscribe = useMutation(api.public.subscribe)
  const [message, setMessage] = useState('')
  const [visitRef, setVisitRef] = useState('')
  const [newsletter, setNewsletter] = useState('')

  async function onContact(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setMessage('Sending…')
    const f = new FormData(e.currentTarget)
    try {
      await submitContact({ name:String(f.get('name')||''), email:String(f.get('email')||''), subject:String(f.get('subject')||''), message:String(f.get('message')||'') })
      setMessage('Message received by the Office of the President.'); e.currentTarget.reset()
    } catch { setMessage('Unable to send. Please check the form and try again.') }
  }

  async function onVisit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setVisitRef('Submitting…')
    const f = new FormData(e.currentTarget)
    try {
      const ref = await submitVisit({ visitorName:String(f.get('visitorName')||''), email:String(f.get('email')||''), phone:String(f.get('phone')||'')||undefined, country:String(f.get('country')||'')||undefined, organization:String(f.get('organization')||'')||undefined, visitCategory:String(f.get('visitCategory')||'general_tour'), groupSize:Number(f.get('groupSize')||1), purpose:String(f.get('purpose')||''), preferredDate:String(f.get('preferredDate')||''), alternateDate:String(f.get('alternateDate')||'')||undefined })
      setVisitRef(`Request received. Reference: ${ref}`); e.currentTarget.reset()
    } catch { setVisitRef('Unable to submit the request. Please review the form.') }
  }

  async function onSubscribe(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); const f = new FormData(e.currentTarget); const email=String(f.get('email')||'')
    try { const added=await subscribe({email}); setNewsletter(added?'Subscription confirmed.':'This email is already subscribed.'); e.currentTarget.reset() }
    catch { setNewsletter('Enter a valid email address.') }
  }

  return <div className="presidency-site">
    <header className="masthead">
      <div className="flag-ribbon" aria-hidden="true"><span/><span/><span/></div>
      <div className="container masthead-inner">
        <div className="identity-lockup">
          <div className="seal-frame"><img src={PRESIDENTIAL_SEAL} alt="Presidential seal" /></div>
          <div><div className="country-line">Republic of Uganda</div><div className="office-line">Office of the President</div></div>
        </div>
        <div className="masthead-meta"><span>State House</span><span>Official Public Portal</span></div>
      </div>
    </header>

    <nav className="diplomatic-nav"><div className="container diplomatic-nav-inner">
      <a href="#presidency">The Presidency</a><a href="#executive-government">Executive Government</a><a href="#records">Presidential Records</a><a href="#priorities">National Priorities</a><a href="#news">Newsroom</a><a href="#events">State Events</a><a href="#engage">Public Engagement</a><a href="/admin" className="staff-link">Staff Portal</a>
    </div></nav>

    <main>
      <section className="presidential-hero" id="presidency" data-state={data === undefined ? 'loading' : 'ready'}>
        <div className="hero-photo"><img src={HERO_PHOTO} alt="Presidential official imagery" /></div>
        <div className="hero-shade"/>
        <div className="container hero-grid">
          <div className="hero-copy-block">
            <div className="overline">The Presidency</div>
            <h1>Leadership in service to the Republic.</h1>
            <p>The official public gateway to the Presidency: executive actions, national priorities, State House engagements, speeches, public events and presidential records.</p>
            <div className="hero-actions"><a href="#records" className="gold-button">View Presidential Records</a><a href="#engage" className="ghost-button">Contact the Office</a></div>
          </div>
          <aside className="standard-panel">
            <div className="standard-rule">Presidential Standard</div>
            <img src={PRESIDENTIAL_STANDARD} alt="Presidential Standard" />
            <p>Symbol of the Office of the President and the authority of the Presidency.</p>
          </aside>
        </div>
      </section>

      <section className="presidential-strip"><div className="container strip-grid">
        <div><span className="strip-number">{data?.executiveOrders.length ?? 0}</span><span>Executive Orders</span></div>
        <div><span className="strip-number">{data?.press.length ?? 0}</span><span>Official Statements</span></div>
        <div><span className="strip-number">{data?.events.length ?? 0}</span><span>Public State Events</span></div>
        <div><span className="strip-number">{data?.youthPrograms.length ?? 0}</span><span>Open Public Programs</span></div>
      </div></section>

      <section className="formal-section intro-section"><div className="container intro-grid">
        <div className="section-kicker">Office of the President</div>
        <div><h2>The Presidency at a glance</h2><p className="lead">This portal organizes the public work of the Presidency by constitutional action, national policy, public communication and State House engagement.</p></div>
        <img src={CEREMONIAL_PHOTO} alt="Presidential ceremonial imagery" className="ceremonial-image" />
      </div></section>

      <ExecutiveGovernmentDirectory offices={data?.executiveOffices} departments={data?.executiveDepartments} />

      <section className="formal-section records-section" id="records"><div className="container">
        <div className="section-head light"><div><span className="section-kicker">Presidential Records</span><h2>Official actions and public documents</h2></div><p>Published records appear here only after release by authorized Presidency staff.</p></div>
        <div className="records-ledger">
          <article><span className="ledger-index">01</span><h3>Executive Orders</h3>{data?.executiveOrders.length ? data.executiveOrders.slice(0,4).map((x:any)=><p key={x._id}><strong>No. {x.orderNumber}</strong><br/>{x.title}</p>) : <p>No executive orders have been published yet.</p>}</article>
          <article><span className="ledger-index">02</span><h3>Speeches & Statements</h3>{data?.press.length ? data.press.slice(0,4).map((x:any)=><p key={x._id}><strong>{x.headline}</strong><br/>{x.releaseDate||''}</p>) : <p>No statements have been released yet.</p>}</article>
          <article><span className="ledger-index">03</span><h3>Legislation</h3>{data?.legislation.length ? data.legislation.slice(0,4).map((x:any)=><p key={x._id}><strong>{x.billTitle}</strong><br/>{x.status}</p>) : <p>No legislation actions have been published yet.</p>}</article>
        </div>
      </div></section>

      <section className="formal-section priorities-section" id="priorities"><div className="container">
        <div className="section-head"><div><span className="section-kicker">National Priorities</span><h2>Priorities of the Administration</h2></div><p>Only priorities approved and published by authorized staff are displayed.</p></div>
        <div className="priority-ledger">{data?.milestones.filter((x:any)=>x.category==='goal').length ? data.milestones.filter((x:any)=>x.category==='goal').map((x:any,i:number)=><article key={x._id}><span>{String(i+1).padStart(2,'0')}</span><div><h3>{x.title}</h3><p>{x.description||''}</p></div></article>) : <article><span>01</span><div><h3>No published priorities yet</h3><p>Authorized staff can publish priorities through the staff portal.</p></div></article>}</div>
      </div></section>

      <section className="formal-section newsroom-section" id="news"><div className="container news-grid">
        <div><span className="section-kicker">Presidential Newsroom</span><h2>Latest from the Presidency</h2>{data?.press.length ? data.press.slice(0,6).map((x:any)=><article className="news-item" key={x._id}><div className="news-meta">{x.statementType} {x.releaseDate ? `· ${x.releaseDate}` : ''}</div><h3>{x.headline}</h3><p>{x.body}</p></article>) : <div className="empty-state">No official newsroom items have been published yet.</div>}</div>
        <aside className="events-rail" id="events"><span className="section-kicker">State Calendar</span><h3>Public Events</h3>{data?.events.length ? data.events.map((x:any)=><div className="event-row" key={x._id}><time>{x.eventDate}</time><div><strong>{x.title}</strong><span>{x.location||''}</span></div></div>) : <p>No public events are currently scheduled.</p>}</aside>
      </div></section>

      <section className="symbols-section"><div className="container symbols-identity">
        <div className="seal-display"><img src={PRESIDENTIAL_SEAL} alt="Presidential seal and national arms" /></div>
        <div><span className="section-kicker">Symbols of Office</span><h2>The seal and Presidential Standard</h2><p>Presidential symbols are displayed with restraint and ceremony, reinforcing the visual identity of the Office across the public portal.</p></div>
        <div className="flag-display"><img src={PRESIDENTIAL_STANDARD} alt="Presidential Standard ceremonial flag" /></div>
      </div></section>

      <section className="engagement-section" id="engage"><div className="container">
        <div className="section-head light"><div><span className="section-kicker">Public Engagement</span><h2>Connect with the Office of the President</h2></div><p>Correspondence and State House visit requests are received directly through the Presidency portal.</p></div>
        <div className="forms-grid">
          <form className="formal-form" onSubmit={onContact}><h3>Send Correspondence</h3><input name="name" placeholder="Full name" required/><input name="email" type="email" placeholder="Email address" required/><input name="subject" placeholder="Subject" required/><textarea name="message" placeholder="Message" rows={5} required/><button className="gold-button" type="submit">Send Message</button><p className="form-status">{message}</p></form>
          <form className="formal-form" id="visit" onSubmit={onVisit}><h3>Request a State House Visit</h3><input name="visitorName" placeholder="Visitor / delegation name" required/><input name="email" type="email" placeholder="Email address" required/><div className="form-two"><input name="phone" placeholder="Phone"/><input name="organization" placeholder="Organization"/></div><input name="country" placeholder="Country"/><select name="visitCategory"><option value="general_tour">General tour</option><option value="educational_tour">Educational tour</option><option value="official_diplomatic">Official / diplomatic</option><option value="media_press">Media / press</option><option value="cultural_ceremonial">Cultural / ceremonial</option><option value="personal_audience">Personal audience</option></select><input name="groupSize" type="number" min="1" max="500" defaultValue="1" required/><textarea name="purpose" placeholder="Purpose of visit" rows={3} required/><div className="form-two"><label>Preferred date<input name="preferredDate" type="date" required/></label><label>Alternate date<input name="alternateDate" type="date"/></label></div><button className="gold-button" type="submit">Submit Visit Request</button><p className="form-status">{visitRef}</p></form>
        </div>
        <form className="updates-form" onSubmit={onSubscribe}><div><span className="section-kicker">Presidential Updates</span><h3>Receive official public notices</h3></div><input name="email" type="email" placeholder="Email address" required/><button className="outline-gold-button" type="submit">Subscribe</button><span>{newsletter}</span></form>
      </div></section>
    </main>

    <footer className="presidential-footer"><div className="container footer-main">
      <div className="footer-identity"><div className="seal-frame small"><img src={PRESIDENTIAL_SEAL} alt="Presidential seal footer" /></div><div><span>Republic of Uganda</span><strong>Office of the President</strong></div></div>
      <div><h4>The Presidency</h4><a href="#records">Presidential Records</a><a href="#priorities">National Priorities</a><a href="#news">Newsroom</a></div>
      <div><h4>Public Service</h4><a href="#engage">Contact the Office</a><a href="#visit">State House Visits</a><a href="/admin">Staff Portal</a></div>
      <div><h4>Official Contacts</h4><p>Verified phone, email and social-media details will appear here once supplied and approved.</p></div>
    </div><div className="container footer-bottom"><span>© 2026 Office of the President</span><span>UNG-PRESIDENT</span></div></footer>
  </div>
}
