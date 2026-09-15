import { createFileRoute, Link } from '@tanstack/react-router'
import { StaffPortal } from '@/components/staff-portal'

export const Route = createFileRoute('/admin')({
  component: AdminRoute,
})

function AdminRoute() {
  return <>
    <StaffPortal />
    <Link
      to="/reset-password"
      className="fixed bottom-12 left-1/2 z-50 -translate-x-1/2 rounded-lg bg-slate-950/90 px-4 py-2 text-xs text-amber-200 underline shadow-lg"
    >
      Forgot password? Reset it
    </Link>
  </>
}
