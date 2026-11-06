import { describe, expect, it } from 'vitest'
import { formatPrice, parseSort, tintOf } from './categories'

describe('parseSort', () => {
  it.each(['rating', 'price_asc', 'price_desc', 'newest'])('keeps %s', (sort) => {
    expect(parseSort(sort)).toBe(sort)
  })

  it.each([null, '', 'cheapest', 'price_asc; DROP TABLE products'])('falls back to top rated for %s', (sort) => {
    expect(parseSort(sort)).toBe('rating')
  })
})

describe('formatPrice', () => {
  it.each([
    [59.99, '$59.99'],
    [129, '$129.00'],
    [45.5, '$45.50'],
    [1234.5, '$1,234.50'],
  ])('%s', (price, text) => {
    expect(formatPrice(price)).toBe(text)
  })
})

describe('tintOf', () => {
  it('names the category colour', () => {
    expect(tintOf('keyboards-and-mice')).toBe('var(--color-tint-keyboards)')
  })
})
