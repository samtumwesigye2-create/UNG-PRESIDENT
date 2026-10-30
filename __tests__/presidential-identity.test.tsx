import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

vi.mock('convex/react', () => ({
  useQuery: () => ({ executiveOrders:[], press:[], events:[], milestones:[], legislation:[], gallery:[], youthPrograms:[] }),
  useMutation: () => vi.fn(),
}))

import { PresidentHome } from '@/routes/index'

describe('presidential public identity', () => {
  it('renders presidential identity imagery in the header and hero', () => {
    render(<PresidentHome />)
    expect(screen.getAllByAltText(/Presidential seal/i).length).toBeGreaterThan(0)
    expect(screen.getAllByAltText(/Presidential Standard/i).length).toBeGreaterThan(0)
  })

  it('presents the formal public information hierarchy', () => {
    render(<PresidentHome />)
    expect(screen.getAllByText('The Presidency').length).toBeGreaterThan(0)
    expect(screen.getByText(/Official actions and public documents/i)).toBeInTheDocument()
    expect(screen.getByText(/Latest from the Presidency/i)).toBeInTheDocument()
    expect(screen.getByText(/Connect with the Office of the President/i)).toBeInTheDocument()
  })
})
