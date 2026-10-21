import { createFileRoute, Link } from '@tanstack/react-router'
import { useAuthActions } from '@convex-dev/auth/react'
import { FormEvent, useState } from 'react'

export const Route = createFileRoute('/reset-password')({ component: PasswordReset })

function PasswordReset() {
  const { signIn } = useAuthActions()
  const [step, setStep] = useState<'request'|'verify'|'done'>('request')
  const [email, setEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string|null>(null)

  async function requestReset(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setBusy(true); setError(null)
    const fd = new FormData(e.currentTarget); const address = String(fd.get('email') || '').trim()
    try {
      await signIn('password', { email: address, flow: 'reset' })
      setEmail(address); setStep('verify')
    } catch {
      // Keep the response generic so the screen does not disclose whether an account exists.
      setEmail(address); setStep('verify')
    } finally { setBusy(false) }
  }

  async function completeReset(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setBusy(true); setError(null)
    const fd = new FormData(e.currentTarget)
    const newPassword = String(fd.get('newPassword') || '')
    const confirm = String(fd.get('confirmPassword') || '')
    if (newPassword !== confirm) { setError('Passwords do not match.'); setBusy(false); return }
    if (newPassword.length < 8) { setError('Password must contain at least 8 characters.'); setBusy(false); return }
    try {
      await signIn('password', { email, code: String(fd.get('code') || ''), newPassword, flow: 'reset-verification' })
      setStep('done')
    } catch { setError('The reset code is invalid or expired. Request a new code and try again.') }
    finally { setBusy(false) }
  }

  return <main className="min-h-screen bg-slate-950 text-slate-100 grid place-items-center p-5">
    <section className="w-full max-w-md rounded-3xl border border-white/10 bg-white/5 p-7 shadow-2xl">
      <p className="text-xs uppercase tracking-[.25em] text-amber-200/80">Office of the President</p>
      <h1 className="mt-2 text-2xl font-semibold">Reset staff password</h1>
      {step==='request' && <form className="mt-6 space-y-4" onSubmit={requestReset}>
        <p className="text-sm leading-6 text-slate-300">Enter your official staff email. If it is registered, a verification code will be sent to that address.</p>
        <input aria-label="Official staff email" name="email" type="email" required autoComplete="email" placeholder="Official staff email" className="w-full rounded-xl border border-white/15 bg-black/20 px-4 py-3 outline-none"/>
        <button disabled={busy} className="w-full rounded-xl bg-amber-300 px-4 py-3 font-semibold text-slate-950 disabled:opacity-60">{busy?'Sending…':'Send reset code'}</button>
      </form>}
      {step==='verify' && <form className="mt-6 space-y-4" onSubmit={completeReset}>
        <p className="text-sm leading-6 text-slate-300">If the account is registered, a reset code has been sent. Enter it below with your new password.</p>
        <input name="code" inputMode="numeric" required autoComplete="one-time-code" placeholder="Verification code" className="w-full rounded-xl border border-white/15 bg-black/20 px-4 py-3 outline-none"/>
        <input name="newPassword" type="password" minLength={8} required autoComplete="new-password" placeholder="New password" className="w-full rounded-xl border border-white/15 bg-black/20 px-4 py-3 outline-none"/>
        <input name="confirmPassword" type="password" minLength={8} required autoComplete="new-password" placeholder="Confirm new password" className="w-full rounded-xl border border-white/15 bg-black/20 px-4 py-3 outline-none"/>
        {error && <p className="rounded-xl border border-rose-400/30 bg-rose-400/10 p-3 text-sm text-rose-100">{error}</p>}
        <button disabled={busy} className="w-full rounded-xl bg-amber-300 px-4 py-3 font-semibold text-slate-950 disabled:opacity-60">{busy?'Resetting…':'Reset password'}</button>
        <button type="button" onClick={()=>setStep('request')} className="w-full text-sm text-slate-300 underline">Request another code</button>
      </form>}
      {step==='done' && <div className="mt-6 space-y-4"><p className="rounded-xl border border-emerald-400/30 bg-emerald-400/10 p-4 text-sm">Password reset completed. Sign in using your new password.</p><Link to="/admin" className="block w-full rounded-xl bg-amber-300 px-4 py-3 text-center font-semibold text-slate-950">Return to staff sign in</Link></div>}
      {step!=='done' && <Link to="/admin" className="mt-5 block text-center text-sm text-slate-400 underline">Back to staff sign in</Link>}
    </section>
  </main>
}
