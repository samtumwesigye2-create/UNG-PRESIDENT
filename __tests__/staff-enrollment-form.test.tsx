import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { StaffEnrollmentForm } from '@/components/staff-portal'

describe('staff enrollment form', () => {
  it('collects HR code and staff identity details before enrollment', () => {
    render(<StaffEnrollmentForm email="staff@gov.ug" busy={false} notice={null} onSubmit={vi.fn()} />)
    expect(screen.getByLabelText(/HR enrollment code/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Employee ID/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Full legal name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Job title/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Department/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Supervisor/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Work location/i)).toBeInTheDocument()
    expect(screen.getByRole('checkbox', {name:/security policy/i})).toBeInTheDocument()
  })
})
