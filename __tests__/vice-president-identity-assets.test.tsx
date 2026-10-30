import { describe, expect, it } from 'vitest'
import fs from 'node:fs'

// Regression coverage for the approved generated-image identity target.
describe('presidential identity assets', () => {
  it('uses the uploaded three-symbol plate for the presidential seal crop', () => {
    const page = fs.readFileSync('src/routes/index.tsx','utf8')
    expect(page).toContain('cMhdH8PnCuRMUuhn-17ua.png')
    expect(page).toContain('identity-crop-president')
  })

  it('uses the uploaded VP flag with a clean VP seal replacement over its original center emblem', () => {
    const vp = fs.readFileSync('src/components/vice-president-seal.tsx','utf8')
    expect(vp).toContain('GUw1ndiVyLrDsjz-TCzjF.jpeg')
    expect(vp).toContain('cMhdH8PnCuRMUuhn-17ua.png')
    expect(vp).toContain('vp-flag-seal-cover')
    expect(vp).toContain('vp-seal-from-identity-plate')
  })

  it('contains no obsolete defense ministry artwork', () => {
    const directory = fs.readFileSync('src/components/executive-government-directory.tsx','utf8')
    const vp = fs.readFileSync('src/components/vice-president-seal.tsx','utf8')
    expect(directory.toLowerCase()).not.toContain('defence')
    expect(directory.toLowerCase()).not.toContain('defense')
    expect(vp.toLowerCase()).not.toContain('defence')
    expect(vp.toLowerCase()).not.toContain('defense')
  })
})
