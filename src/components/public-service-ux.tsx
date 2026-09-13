import { FormEvent, useState } from 'react'

type Notice={title:string;message:string;severity:'information'|'warning'|'emergency'}
type Props={notice:Notice|null;onSubscribe:(input:{email:string;categories:string[]})=>Promise<unknown>|unknown}

export function PublicServiceUX({notice,onSubscribe}:Props){
  const [lowBandwidth,setLowBandwidth]=useState(false)
  const [status,setStatus]=useState('')
  function toggleBandwidth(){
    const next=!lowBandwidth
    setLowBandwidth(next)
    document.documentElement.setAttribute('data-low-bandwidth',String(next))
  }
  async function submit(e:FormEvent<HTMLFormElement>){
    e.preventDefault()
    const form=new FormData(e.currentTarget)
    const categories=['newsroom','diary','policies'].filter(category=>form.get(category)==='on')
    const email=String(form.get('email')||'')
    if(!email.includes('@')||categories.length===0){setStatus('Enter a valid email and choose at least one category.');return}
    try{await onSubscribe({email,categories});setStatus('Subscription preferences saved.');e.currentTarget.reset()}catch{setStatus('Unable to save subscription preferences.')}
  }
  return <section className="public-service-ux" aria-labelledby="public-service-title">
    {notice?<div className={`public-information-banner severity-${notice.severity}`} role="alert"><strong>{notice.title}</strong><span>{notice.message}</span></div>:null}
    <div className="container public-service-grid">
      <div><span className="section-kicker">Public Access</span><h2 id="public-service-title">Public information services</h2><p>Choose a lighter page mode for slower connections and subscribe only to the official categories you want.</p><button type="button" className="outline-gold-button bandwidth-toggle" aria-pressed={lowBandwidth} onClick={toggleBandwidth}>{lowBandwidth?'Standard mode':'Low-bandwidth mode'}</button></div>
      <form className="subscription-preferences" onSubmit={submit}><h3>Official subscriptions</h3><input name="email" type="email" aria-label="Subscription email" placeholder="Email address" required/><label><input type="checkbox" name="newsroom"/> Newsroom updates</label><label><input type="checkbox" name="diary"/> Presidential Diary</label><label><input type="checkbox" name="policies"/> Policies & Regulations</label><button className="gold-button" type="submit">Save subscriptions</button><p aria-live="polite">{status}</p></form>
      <div className="public-feed-links"><h3>Calendar & feeds</h3><a href="#presidential-calendar">Presidential calendar</a><a href="#news">Newsroom archive</a><a href="#policies-regulations">Policies & regulations</a><p>Machine-readable calendar and RSS endpoints will be activated only when the backend feed service is deployed.</p></div>
    </div>
  </section>
}
