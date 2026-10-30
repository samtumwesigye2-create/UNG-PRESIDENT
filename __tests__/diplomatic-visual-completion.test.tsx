import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { DiplomaticFooterBand, FlagCropFrame } from '@/components/diplomatic-visual-completion'

describe('diplomatic visual completion', () => {
  it('renders flags inside a crop frame without altering the source asset', () => {
    render(<FlagCropFrame src="https://example.test/standard.jpeg" alt="Presidential Standard" />)
    const image=screen.getByAltText('Presidential Standard')
    expect(image).toHaveAttribute('src','https://example.test/standard.jpeg')
    expect(image.parentElement).toHaveClass('flag-crop-frame')
    expect(image).toHaveClass('flag-crop-image')
  })

  it('renders the national black-gold-red footer band', () => {
    const {container}=render(<DiplomaticFooterBand />)
    expect(container.querySelector('.footer-national-band')).toBeTruthy()
    expect(container.querySelectorAll('.footer-national-band span')).toHaveLength(3)
  })
})
