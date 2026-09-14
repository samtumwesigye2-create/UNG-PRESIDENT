import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, test } from 'vitest'

const read = (path: string) => readFileSync(join(process.cwd(), path), 'utf8')

describe('presidential identity artwork ownership', () => {
  test('homepage no longer depends on Macaly-hosted imagery', () => {
    const source = read('src/routes/index.tsx')
    expect(source).not.toContain('macaly-user-data.dev')
    expect(source).toContain('PRESIDENTIAL_SEAL_DATA_URI')
    expect(source).toContain('NATIONAL_FLAG_DATA_URI')
  })

  test('staff portal uses repository-owned presidential seal', () => {
    const source = read('src/components/staff-portal.tsx')
    expect(source).not.toContain('macaly-user-data.dev')
    expect(source).toContain('PRESIDENTIAL_SEAL_DATA_URI')
  })

  test('vice-president identity uses dedicated fixed seal artwork', () => {
    const source = read('src/components/vice-president-seal.tsx')
    expect(source).not.toContain('macaly-user-data.dev')
    expect(source).toContain('VICE_PRESIDENTIAL_SEAL_DATA_URI')
  })

  test('package metadata contains no Macaly runtime or dev dependency', () => {
    const source = read('package.json')
    expect(source).not.toContain('@macaly/')
  })
})
