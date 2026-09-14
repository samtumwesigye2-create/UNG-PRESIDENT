import { describe, expect, test } from 'vitest'
import { PRESIDENTIAL_SEAL_DATA_URI, VICE_PRESIDENTIAL_SEAL_DATA_URI, NATIONAL_FLAG_DATA_URI } from '../src/lib/presidential-assets'

describe('repository-owned presidential asset paths', () => {
  test('all fixed identity artwork is served locally', () => {
    expect(PRESIDENTIAL_SEAL_DATA_URI).toBe('/assets/presidential-seal.webp')
    expect(VICE_PRESIDENTIAL_SEAL_DATA_URI).toBe('/assets/vice-presidential-seal.webp')
    expect(NATIONAL_FLAG_DATA_URI).toBe('/assets/national-flag.webp')
  })
})
