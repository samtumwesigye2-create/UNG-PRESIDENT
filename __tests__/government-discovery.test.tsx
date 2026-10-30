import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { GovernmentDiscovery, searchGovernmentContent } from '@/components/government-discovery'

describe('government discovery',()=>{
  const records=[
    {title:'Executive Directive 12',kind:'Executive Directive',office:'Office of the President',status:'published',href:'#policies-regulations'},
    {title:'Office of the Vice President',kind:'Executive Office',office:'Vice President',status:'published',href:'#executive-government'},
    {title:'State Visit to Kenya',kind:'State Visit',office:'Office of the President',status:'scheduled',href:'#presidential-calendar'},
  ]

  it('searches across title, type and issuing office',()=>{
    expect(searchGovernmentContent(records,'vice')).toHaveLength(1)
    expect(searchGovernmentContent(records,'state visit')[0].title).toBe('State Visit to Kenya')
    expect(searchGovernmentContent(records,'office of the president')).toHaveLength(2)
  })

  it('provides search, A–Z directory and Government at a Glance',()=>{
    render(<GovernmentDiscovery records={records} />)
    expect(screen.getByRole('searchbox',{name:/search official presidency content/i})).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:/government at a glance/i})).toBeInTheDocument()
    expect(screen.getByRole('heading',{name:/a–z government directory/i})).toBeInTheDocument()
    fireEvent.change(screen.getByRole('searchbox',{name:/search official presidency content/i}),{target:{value:'vice'}})
    expect(screen.getByText('Office of the Vice President')).toBeInTheDocument()
  })
})
