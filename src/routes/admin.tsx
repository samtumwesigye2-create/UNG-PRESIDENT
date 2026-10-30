import { createFileRoute } from '@tanstack/react-router'
import { StaffPortal } from '@/components/staff-portal'

export const Route = createFileRoute('/admin')({
  component: StaffPortal,
})
