import { describe, expect, it } from 'vitest'
import { safeNext, signInPath } from './next'

describe('safeNext', () => {
  it.each([
    ['/cart', '/cart'],
    ['/products/phone-case', '/products/phone-case'],
    ['/shop/audio?sort=price_asc', '/shop/audio?sort=price_asc'],
    ['/how-it-works/trace?turn=3#step', '/how-it-works/trace?turn=3#step'],
  ])('keeps a path on this site: %s', (next, expected) => {
    expect(safeNext(next)).toBe(expected)
  })

  it.each([
    ['nothing', null],
    ['empty', ''],
    ['another site', 'https://evil.example'],
    ['a protocol-relative link', '//evil.example'],
    ['a backslash, which browsers read as a slash', '/\\evil.example'],
    ['two backslashes', '\\\\evil.example'],
    ['a tab hidden between the slashes', '/\t/evil.example'],
    ['a newline hidden between the slashes', '/\n/evil.example'],
    ['a script link', 'javascript:alert(1)'],
    ['a data link', 'data:text/html,hello'],
    ['no leading slash', 'evil.example'],
  ])('goes home for %s', (_name, next) => {
    expect(safeNext(next)).toBe('/')
  })

  it.each(['/signin', '/signup', '/signin?next=/cart'])("doesn't loop back to %s", (next) => {
    expect(safeNext(next)).toBe('/')
  })
})

describe('signInPath', () => {
  it('remembers the current page', () => {
    expect(signInPath({ pathname: '/shop/audio', search: '?sort=rating' })).toBe(
      '/signin?next=%2Fshop%2Faudio%3Fsort%3Drating',
    )
  })

  it('leaves out the home page', () => {
    expect(signInPath({ pathname: '/', search: '' })).toBe('/signin')
  })

  it('keeps the page already being returned to', () => {
    expect(signInPath({ pathname: '/signup', search: '?next=%2Fcart' })).toBe('/signin?next=%2Fcart')
  })
})
