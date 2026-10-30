import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StaffLoginPanel } from '@/components/staff-portal'

describe('UNG-PRESIDENT staff portal', () => {
  it('renders a real staff sign-in surface instead of a demo placeholder', () => {
    render(<StaffLoginPanel busy={false} error={null} onSubmit={() => undefined} />)
    expect(screen.getByRole('heading', { name: /staff portal/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    expect(screen.queryByText(/demo/i)).not.toBeInTheDocument()
  })
})
