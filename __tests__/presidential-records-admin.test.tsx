import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { PresidentialRecordsAdmin } from '@/components/presidential-records-admin'

describe('PresidentialRecordsAdmin', () => {
  it('provides controlled forms for classified events and official documents', () => {
    render(<PresidentialRecordsAdmin onSaveEvent={vi.fn()} onSaveDocument={vi.fn()} />)
    expect(screen.getByRole('heading',{name:/Presidential event publishing/i})).toBeTruthy()
    expect(screen.getByLabelText(/Domestic or international/i)).toBeTruthy()
    expect(screen.getByLabelText(/Event type/i)).toBeTruthy()
    expect(screen.getByRole('heading',{name:/Policies & Regulations publishing/i})).toBeTruthy()
    expect(screen.getByLabelText(/Official document reference/i)).toBeTruthy()
    expect(screen.getByLabelText(/Publication status/i)).toBeTruthy()
  })
})
