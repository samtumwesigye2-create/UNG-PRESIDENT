import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { OfficialDocumentVerificationView } from '@/components/official-document-verification-view'

describe('official document verification view', () => {
  it('shows authenticity metadata and print/source actions', () => {
    render(<OfficialDocumentVerificationView document={{
      title:'National Policy Record',
      documentType:'policy',
      summary:'Official summary',
      body:'Official body',
      issuingOffice:'Presidential Secretariat',
      issuedBy:'Office of the President',
      reference:'OP-POL-2026-0042',
      version:'2.0',
      status:'published',
      publishedAt:1690000000000,
      updatedAt:1700000000000,
      sourceUrl:'https://example.gov/document.pdf',
    }}/>)
    expect(screen.getByText('Verified Official Record')).toBeInTheDocument()
    expect(screen.getByText('OP-POL-2026-0042')).toBeInTheDocument()
    expect(screen.getByText('Office of the President')).toBeInTheDocument()
    expect(screen.getByRole('button',{name:/print official record/i})).toBeInTheDocument()
    expect(screen.getByRole('link',{name:/source document/i})).toHaveAttribute('href','https://example.gov/document.pdf')
  })
})
