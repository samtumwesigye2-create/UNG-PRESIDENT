export type StaffRole = 'president' | 'admin' | 'staff' | 'protocol' | 'press'

export type Permission =
  | 'executive_orders.create'
  | 'executive_orders.issue'
  | 'executive_orders.rescind'
  | 'appointments.create'
  | 'appointments.status'
  | 'honours.create'
  | 'honours.status'
  | 'petitions.create'
  | 'petitions.update'
  | 'milestones.create'
  | 'milestones.archive'
  | 'legislation.create'
  | 'legislation.status'
  | 'contact_messages.status'
  | 'youth_programs.create'
  | 'youth_programs.status'
  | 'state_functions.create'
  | 'state_functions.status'
  | 'state_visits.create'
  | 'state_visits.status'
  | 'visitor_requests.status'
  | 'press_statements.create'
  | 'press_statements.release'
  | 'gallery.create'
  | 'gallery.archive'
  | 'staff.manage'
  | 'audit.read'

const rolePermissions: Record<Exclude<StaffRole, 'admin' | 'president'>, ReadonlySet<Permission>> = {
  staff: new Set([
    'appointments.create', 'appointments.status', 'honours.create', 'petitions.create', 'petitions.update',
    'milestones.create', 'milestones.archive', 'legislation.create', 'contact_messages.status',
    'youth_programs.create', 'youth_programs.status',
  ]),
  protocol: new Set([
    'state_functions.create', 'state_functions.status', 'state_visits.create', 'state_visits.status',
    'visitor_requests.status',
  ]),
  press: new Set([
    'press_statements.create', 'press_statements.release', 'gallery.create', 'gallery.archive',
  ]),
}

export function canPerform(role: StaffRole, permission: Permission): boolean {
  if (role === 'admin' || role === 'president') return true
  return rolePermissions[role]?.has(permission) ?? false
}
