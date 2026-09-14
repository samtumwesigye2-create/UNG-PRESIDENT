import { useAuthActions } from '@convex-dev/auth/react'
import { Authenticated, AuthLoading, Unauthenticated, useMutation, useQuery } from 'convex/react'
import { useState, type FormEvent } from 'react'
import { api } from '../../convex/_generated/api'
import { PRESIDENTIAL_SEAL_DATA_URI } from '../lib/presidential-assets'

const EXECUTIVE_SEAL = PRESIDENTIAL_SEAL_DATA_URI

type LoginProps = { busy:boolean; error:string|null; onSubmit:(event:FormEvent<HTMLFormElement>)=>void }
type EnrollmentProps = { email:string; busy:boolean; notice:string|null; onSubmit:(event:FormEvent<HTMLFormElement>)=>void }

export function StaffEnrollmentForm({email,busy,notice,onSubmit}:EnrollmentProps) {
  const field='mt-2 w-full rounded-xl border border-white/15 bg-black/20 px-4 py-3 outline-none'
  return <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-5">
    <div className="w-full max-w-4xl rounded-3xl border border-white/10 bg-white/5 p-7 shadow-2xl">
      <div className="flex items-center gap-4 border-b border-white/10 pb-5">
        <img src={EXECUTIVE_SEAL} alt="Executive seal" className="h-20 w-20 rounded-full object-cover" />
        <div><p className="text-xs uppercase tracking-[.25em] text-amber-200/80">Office of the President</p><h1 className="text-2xl font-semibold">First-time staff enrollment</h1><p className="mt-1 text-sm text-slate-300">HR authorization and verified identity are required before access can be activated.</p></div>
      </div>
      <form className="mt-6 grid gap-4 md:grid-cols-2" onSubmit={onSubmit}>
        <label className="text-sm">HR enrollment code<input aria-label="HR enrollment code" name="code" required autoComplete="off" className={field}/></label>
        <label className="text-sm">Official staff email<input aria-label="Official staff email" name="email" type="email" required defaultValue={email} className={field}/></label>
        <label className="text-sm">Employee ID<input aria-label="Employee ID" name="employeeId" required className={field}/></label>
        <label className="text-sm">Full legal name<input aria-label="Full legal name" name="fullName" required className={field}/></label>
        <label className="text-sm">Preferred/display name<input name="preferredName" className={field}/></label>
        <label className="text-sm">Phone number<input name="phone" type="tel" required className={field}/></label>
        <label className="text-sm">Job title<input aria-label="Job title" name="jobTitle" required className={field}/></label>
        <label className="text-sm">Department / Ministry<input aria-label="Department" name="department" required className={field}/></label>
        <label className="text-sm">Office<input name="office" required className={field}/></label>
        <label className="text-sm">Supervisor<input aria-label="Supervisor" name="supervisor" required className={field}/></label>
        <label className="text-sm">Work location<input aria-label="Work location" name="workLocation" required className={field}/></label>
        <label className="text-sm">Employment type<select name="employmentType" required className={field}><option value="employee">Employee</option><option value="appointee">Appointee</option><option value="contractor">Contractor</option><option value="secondment">Secondment</option></select></label>
        <label className="text-sm">Start date<input name="startDate" type="date" required className={field}/></label>
        <label className="md:col-span-2 flex items-start gap-3 rounded-xl border border-white/10 p-4 text-sm"><input aria-label="security policy acknowledgement" name="acceptSecurityPolicy" type="checkbox" required className="mt-1"/><span>I acknowledge the Presidency information-security, acceptable-use, records and confidentiality requirements. Enrollment does not grant access until authorized activation.</span></label>
        {notice?<p className="md:col-span-2 text-sm text-amber-100">{notice}</p>:null}
        <button disabled={busy} className="md:col-span-2 rounded-xl bg-amber-300 px-4 py-3 font-semibold text-slate-950 disabled:opacity-60">{busy?'Submitting enrollment…':'Submit secure enrollment'}</button>
      </form>
    </div>
  </div>
}

export function StaffLoginPanel({busy,error,onSubmit}:LoginProps) {
  return <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-5">
    <div className="w-full max-w-md rounded-3xl border border-white/10 bg-white/5 p-7 shadow-2xl">
      <div className="mb-7 flex items-center gap-4"><img src={EXECUTIVE_SEAL} alt="Executive seal" className="h-16 w-16 rounded-full object-cover"/><div><p className="text-xs uppercase tracking-[.25em] text-amber-200/80">Office of the President</p><h1 className="text-2xl font-semibold">Secure Staff Portal</h1></div></div>
      <p className="mb-6 text-sm leading-6 text-slate-300">Authorized Presidency personnel only. Activity is subject to security monitoring and audit.</p>
      <form className="space-y-4" onSubmit={onSubmit}>
        <label className="block text-sm font-medium">Email<input aria-label="Email" name="email" type="email" required autoComplete="email" className="mt-2 w-full rounded-xl border border-white/15 bg-black/20 px-4 py-3 outline-none"/></label>
        <label className="block text-sm font-medium">Password<input aria-label="Password" name="password" type="password" required minLength={8} autoComplete="current-password" className="mt-2 w-full rounded-xl border border-white/15 bg-black/20 px-4 py-3 outline-none"/></label>
        <input type="hidden" name="flow" value="signIn"/>
        {error?<p className="rounded-xl border border-rose-400/30 bg-rose-400/10 p-3 text-sm text-rose-100">{error}</p>:null}
        <button type="submit" disabled={busy} className="w-full rounded-xl bg-amber-300 px-4 py-3 font-semibold text-slate-950 disabled:opacity-60">{busy?'Signing in…':'Sign in'}</button>
      </form>
    </div>
  </div>
}

function UnauthenticatedPortal() {
  const {signIn}=useAuthActions(); const [busy,setBusy]=useState(false); const [error,setError]=useState<string|null>(null); const [mode,setMode]=useState<'signin'|'signup'|'verify'>('signin'); const [email,setEmail]=useState('')
  const submit=async(e:FormEvent<HTMLFormElement>,flow:'signin'|'signup'|'verify')=>{e.preventDefault();setBusy(true);setError(null);const fd=new FormData(e.currentTarget);try{if(flow==='signin')await signIn('password',fd);if(flow==='signup'){const em=String(fd.get('email')||'');await signIn('password',fd);setEmail(em);setMode('verify')}if(flow==='verify')await signIn('resend-otp',fd)}catch(err){setError(err instanceof Error?err.message:'Authentication failed')}finally{setBusy(false)}}
  if(mode==='verify')return <div className="min-h-screen bg-slate-950 text-white grid place-items-center p-5"><form className="w-full max-w-md space-y-4 rounded-3xl border border-white/10 bg-white/5 p-7" onSubmit={e=>void submit(e,'verify')}><h1 className="text-2xl font-semibold">Verify staff email</h1><p className="text-sm text-slate-300">Enter the code sent to {email}.</p><input name="email" type="hidden" value={email}/><input name="flow" type="hidden" value="email-verification"/><input name="code" type="text" inputMode="numeric" required className="w-full rounded-xl border border-white/15 bg-black/20 px-4 py-3" placeholder="6-digit verification code"/>{error?<p className="text-rose-200">{error}</p>:null}<button className="w-full rounded-xl bg-amber-300 px-4 py-3 font-semibold text-slate-950">{busy?'Verifying…':'Verify'}</button></form></div>
  if(mode==='signup')return <div className="min-h-screen bg-slate-950 text-white grid place-items-center p-5"><form className="w-full max-w-md space-y-4 rounded-3xl border border-white/10 bg-white/5 p-7" onSubmit={e=>void submit(e,'signup')}><h1 className="text-2xl font-semibold">Create verified credential</h1><p className="text-sm text-slate-300">This creates a credential only. Staff access still requires an unused HR enrollment code and authorized activation.</p><input name="email" type="email" required placeholder="Official email" className="w-full rounded-xl border border-white/15 bg-black/20 px-4 py-3"/><input name="password" type="password" minLength={8} required placeholder="Password" className="w-full rounded-xl border border-white/15 bg-black/20 px-4 py-3"/><input name="flow" type="hidden" value="signUp"/>{error?<p className="text-rose-200">{error}</p>:null}<button className="w-full rounded-xl bg-amber-300 px-4 py-3 font-semibold text-slate-950">Create credential</button><button type="button" onClick={()=>setMode('signin')} className="w-full text-sm text-slate-300">Back to sign in</button></form></div>
  return <div><StaffLoginPanel busy={busy} error={error} onSubmit={e=>void submit(e,'signin')}/><button onClick={()=>setMode('signup')} className="fixed bottom-5 left-1/2 -translate-x-1/2 text-xs text-slate-400 underline">First-time staff credential setup</button></div>
}

function AuthorizedPortal() {
  const {signOut}=useAuthActions()
  const me=useQuery(api.staff.me,{})
  const dashboard=useQuery(api.staff.dashboard,me?.ok?{}:'skip')
  const privileged=me?.ok&&(me.profile.role==='admin'||me.profile.role==='president')
  const profiles=useQuery(api.staff.listProfiles,privileged?{}:'skip')
  const approvals=useQuery(api.staff.listPendingApprovals,privileged?{}:'skip')
  const enrollmentApi=(api as any).enrollment
  const enroll=useMutation(enrollmentApi.enroll)
  const issueInvitation=useMutation(enrollmentApi.issueInvitation)
  const changeStatus=useMutation(api.staff.changeStatus)
  const reviewApproval=useMutation(api.staff.reviewApproval)
  const bootstrap=useMutation(api.staff.bootstrap)
  const [notice,setNotice]=useState<string|null>(null); const [busy,setBusy]=useState(false)

  if(me===undefined)return <div className="min-h-screen bg-slate-950 text-white grid place-items-center">Checking secure staff authorization…</div>
  if(!me.ok){
    if(me.code==='PENDING'||me.code==='SUSPENDED'||me.code==='REVOKED')return <div className="min-h-screen bg-slate-950 text-white grid place-items-center p-6"><div className="max-w-xl rounded-3xl border border-white/10 bg-white/5 p-8"><img src={EXECUTIVE_SEAL} alt="Executive seal" className="h-20 w-20 rounded-full object-cover"/><h1 className="mt-5 text-2xl font-semibold">Staff security status: {me.code}</h1><p className="mt-3 text-slate-300">{me.message}</p><button onClick={()=>void signOut()} className="mt-6 rounded-xl border border-white/20 px-4 py-2">Sign out</button></div></div>
    return <StaffEnrollmentForm email="" busy={busy} notice={notice} onSubmit={async e=>{e.preventDefault();setBusy(true);setNotice(null);const fd=new FormData(e.currentTarget);const r=await enroll({code:String(fd.get('code')),email:String(fd.get('email')),employeeId:String(fd.get('employeeId')),fullName:String(fd.get('fullName')),preferredName:String(fd.get('preferredName')||'')||undefined,phone:String(fd.get('phone')),jobTitle:String(fd.get('jobTitle')),department:String(fd.get('department')),office:String(fd.get('office')),supervisor:String(fd.get('supervisor')),workLocation:String(fd.get('workLocation')),employmentType:String(fd.get('employmentType')),startDate:String(fd.get('startDate')),acceptSecurityPolicy:fd.get('acceptSecurityPolicy')==='on'});setNotice(r.message);setBusy(false)}}/>
  }

  return <div className="min-h-screen bg-slate-100 text-slate-900">
    <header className="bg-slate-950 text-white"><div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4"><div className="flex items-center gap-3"><img src={EXECUTIVE_SEAL} alt="Executive seal" className="h-14 w-14 rounded-full object-cover"/><div><p className="text-xs uppercase tracking-[.22em] text-amber-300">UNG-PRESIDENT</p><h1 className="text-xl font-semibold">Presidential Staff Security Center</h1></div></div><div className="flex items-center gap-4"><div className="text-right text-sm"><strong>{me.profile.fullName}</strong><div className="text-slate-400">{me.profile.role.toUpperCase()}{me.profile.office?` · ${me.profile.office}`:''}</div></div><button onClick={()=>void signOut()} className="rounded-lg border border-white/20 px-3 py-2 text-sm">Sign out</button></div></div></header>
    <main className="mx-auto max-w-7xl space-y-6 p-5">
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{dashboard?.ok?Object.entries(dashboard.counts).map(([key,value])=><div key={key} className="rounded-2xl bg-white p-5 shadow-sm"><p className="text-xs uppercase tracking-wide text-slate-500">{key.replaceAll(/([A-Z])/g,' $1')}</p><strong className="mt-2 block text-3xl">{value}</strong></div>):<div className="col-span-full rounded-2xl bg-white p-5">Loading operations…</div>}</section>
      {privileged?<>
        <section className="rounded-2xl bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold">Issue HR enrollment invitation</h2><p className="mt-1 text-sm text-slate-500">Codes are single-use, identity-bound and expire automatically.</p><form className="mt-4 grid gap-3 md:grid-cols-3" onSubmit={async e=>{e.preventDefault();const f=e.currentTarget,fd=new FormData(f);const hours=Math.max(1,Number(fd.get('hours')||24));const r=await issueInvitation({code:String(fd.get('code')),email:String(fd.get('email')),employeeId:String(fd.get('employeeId')||'')||undefined,intendedRole:String(fd.get('role')) as any,office:String(fd.get('office')||'')||undefined,department:String(fd.get('department')||'')||undefined,expiresAt:Date.now()+hours*3600000});setNotice(r.ok?'HR enrollment invitation issued.':r.message);if(r.ok)f.reset()}}><input name="code" required placeholder="HR code" className="rounded-xl border px-3 py-2"/><input name="email" type="email" required placeholder="authorized email" className="rounded-xl border px-3 py-2"/><input name="employeeId" placeholder="employee ID" className="rounded-xl border px-3 py-2"/><input name="office" placeholder="office" className="rounded-xl border px-3 py-2"/><input name="department" placeholder="department" className="rounded-xl border px-3 py-2"/><select name="role" className="rounded-xl border px-3 py-2"><option value="staff">Staff</option><option value="protocol">Protocol</option><option value="press">Press</option><option value="admin">Admin</option><option value="president">President</option></select><input name="hours" type="number" min="1" max="168" defaultValue="24" className="rounded-xl border px-3 py-2"/><button className="rounded-xl bg-slate-950 px-3 py-2 font-semibold text-white">Issue secure code</button></form></section>
        <section className="rounded-2xl bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold">Staff account lifecycle</h2><div className="mt-4 overflow-x-auto"><table className="w-full text-sm"><thead><tr className="border-b text-left text-slate-500"><th className="py-2">Name</th><th>Email</th><th>Role</th><th>Status</th><th>Security action</th></tr></thead><tbody>{profiles&&profiles.ok?profiles.profiles.map((p:any)=><tr key={p._id} className="border-b"><td className="py-3 font-medium">{p.fullName}</td><td>{p.email}</td><td>{p.role}</td><td>{p.status}</td><td className="py-2"><div className="flex flex-wrap gap-2">{p.status==='pending'?<button onClick={async()=>{const r=await changeStatus({profileId:p._id,status:'active',reason:'Authorized administrative activation'});setNotice(r.ok?'Staff account activated.':r.message)}} className="rounded border px-2 py-1">Activate</button>:null}{p.status==='active'?<button onClick={async()=>{const r=await changeStatus({profileId:p._id,status:'suspended',reason:'Administrative security suspension'});setNotice(r.ok?'Staff account suspended.':r.message)}} className="rounded border px-2 py-1">Suspend</button>:null}{p.status==='suspended'?<button onClick={async()=>{const r=await changeStatus({profileId:p._id,status:'active',reason:'Authorized reactivation'});setNotice(r.ok?'Staff account reactivated.':r.message)}} className="rounded border px-2 py-1">Reactivate</button>:null}{p.status!=='revoked'?<button onClick={async()=>{const r=await changeStatus({profileId:p._id,status:'revoked',reason:'Administrative access revocation'});setNotice(r.ok?'Staff access revoked.':r.message)}} className="rounded border px-2 py-1">Revoke</button>:null}</div></td></tr>):null}</tbody></table></div></section>
        <section className="rounded-2xl bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold">Privileged approvals</h2><p className="mt-1 text-sm text-slate-500">A requester cannot approve their own high-risk action.</p><div className="mt-4 space-y-3">{approvals&&approvals.ok&&approvals.approvals.length?approvals.approvals.map((a:any)=><article key={a._id} className="rounded-xl border p-4"><strong>{a.action}</strong><p className="text-sm text-slate-500">{a.entity}{a.entityId?` · ${a.entityId}`:''}</p><p className="mt-2 text-sm">{a.reason||'No reason supplied.'}</p><div className="mt-3 flex gap-2"><button onClick={async()=>{const r=await reviewApproval({approvalId:a._id,decision:'approved',reason:'Approved by privileged reviewer'});setNotice(r.ok?'Privileged action approved.':r.message)}} className="rounded border px-3 py-1">Approve</button><button onClick={async()=>{const r=await reviewApproval({approvalId:a._id,decision:'rejected',reason:'Rejected by privileged reviewer'});setNotice(r.ok?'Privileged action rejected.':r.message)}} className="rounded border px-3 py-1">Reject</button></div></article>):<p className="text-sm text-slate-500">No pending privileged approvals.</p>}</div></section>
      </>:null}
      {notice?<p className="rounded-xl bg-white p-4 text-sm shadow-sm">{notice}</p>:null}
      {!privileged?<section className="grid gap-6 lg:grid-cols-2"><div className="rounded-2xl bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold">Recent public messages</h2><p className="mt-3 text-sm text-slate-500">Operational information is available according to your assigned role.</p></div><div className="rounded-2xl bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold">Security status</h2><p className="mt-3 text-sm text-slate-500">Account active · role {me.profile.role}</p></div></section>:null}
    </main>
  </div>
}

export function StaffPortal(){return <><AuthLoading><div className="min-h-screen bg-slate-950 text-white grid place-items-center">Checking secure session…</div></AuthLoading><Unauthenticated><UnauthenticatedPortal/></Unauthenticated><Authenticated><AuthorizedPortal/></Authenticated></>}
