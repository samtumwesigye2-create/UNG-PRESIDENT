import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { PublicServiceUX } from '@/components/public-service-ux'

describe('public service UX',()=>{
  it('renders an emergency banner only when an active notice exists',()=>{
    const {rerender}=render(<PublicServiceUX notice={null} onSubscribe={vi.fn()} />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    rerender(<PublicServiceUX notice={{title:'Public Information',message:'Official advisory',severity:'information'}} onSubscribe={vi.fn()} />)
    expect(screen.getByRole('alert')).toHaveTextContent('Official advisory')
  })

  it('supports low-bandwidth mode and categorized subscriptions',()=>{
    render(<PublicServiceUX notice={null} onSubscribe={vi.fn()} />)
    expect(screen.getByRole('button',{name:/low-bandwidth mode/i})).toBeInTheDocument()
    expect(screen.getByLabelText(/newsroom updates/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/presidential diary/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button',{name:/low-bandwidth mode/i}))
    expect(document.documentElement).toHaveAttribute('data-low-bandwidth','true')
  })
})
