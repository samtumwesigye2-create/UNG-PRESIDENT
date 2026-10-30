import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from 'convex/react'
import { api } from '../../convex/_generated/api'
import { OfficialDocumentVerificationView } from '../components/official-document-verification-view'

export const Route = createFileRoute('/verify/$reference')({ component: VerifyOfficialDocumentPage })

function VerifyOfficialDocumentPage() {
  const {reference}=Route.useParams()
  const result=useQuery(api.public.verifyOfficialDocument,{reference:decodeURIComponent(reference)})

  if(result===undefined) return <main className="min-h-screen bg-slate-950 text-white grid place-items-center p-6">Verifying official record…</main>
  if(!result.ok) return <main className="min-h-screen bg-slate-950 text-white grid place-items-center p-6"><div className="max-w-xl rounded-3xl border border-white/10 bg-white/5 p-8"><p className="text-xs uppercase tracking-[.2em] text-amber-300">Office of the President</p><h1 className="mt-3 text-3xl font-semibold">Official record not verified</h1><p className="mt-3 text-slate-300">{result.message}</p><p className="mt-4 text-sm text-slate-400">Reference checked: {decodeURIComponent(reference)}</p><a href="/" className="mt-6 inline-block rounded-xl border border-white/20 px-4 py-2">Return to Presidency portal</a></div></main>
  return <OfficialDocumentVerificationView document={result.document}/>
}
