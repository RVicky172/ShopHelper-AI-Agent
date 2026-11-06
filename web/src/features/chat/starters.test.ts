import { describe, expect, it } from 'vitest'
import { productStarters, startersFor } from './starters'

describe('productStarters', () => {
  const starters = productStarters('Yoga Mat', 'Fitness and outdoors')

  it('names the product and its category, because the agent only knows the policies', () => {
    for (const starter of starters) {
      expect(starter).toContain('Yoga Mat')
      expect(starter).toContain('fitness and outdoors')
    }
  })

  it('covers warranty and returns', () => {
    expect(starters.join(' ')).toMatch(/warranty/i)
    expect(starters.join(' ')).toMatch(/return/i)
  })
})

describe('startersFor', () => {
  it('uses the product on a product page', () => {
    const starters = startersFor({
      pathname: '/products/yoga-mat',
      product: { name: 'Yoga Mat', category: 'Fitness and outdoors' },
    })
    expect(starters[0]).toContain('Yoga Mat')
  })

  it('falls back while the product is loading', () => {
    expect(startersFor({ pathname: '/products/yoga-mat' }).length).toBeGreaterThanOrEqual(2)
  })

  it('helps with orders on the orders page', () => {
    const starters = startersFor({ pathname: '/account/orders', latestOrderId: '1001' })
    expect(starters[0]).toBe('Where is order 1001?')
  })

  it('still helps on the orders page with no orders', () => {
    const starters = startersFor({ pathname: '/account/orders' })
    expect(starters.length).toBeGreaterThanOrEqual(2)
    expect(starters.join(' ')).not.toContain('undefined')
  })

  it('talks about delivery and returns in the cart', () => {
    const text = startersFor({ pathname: '/cart' }).join(' ')
    expect(text).toMatch(/deliver/i)
    expect(text).toMatch(/return/i)
  })

  it.each(['/', '/shop/audio', '/cart', '/account/orders', '/products/x', '/how-it-works/trace'])(
    'offers 2 or 3 starters on %s',
    (pathname) => {
      const count = startersFor({ pathname }).length
      expect(count).toBeGreaterThanOrEqual(2)
      expect(count).toBeLessThanOrEqual(3)
    },
  )
})
