import { describe, expect, it } from 'vitest'
import { addItem, buildView, changeMessage, parseGuestCart, setQuantity } from './cartLogic'

const mouse = { id: 8, slug: 'wireless-mouse', name: 'Wireless Mouse', price: 59.99, category: 'keyboards-and-mice' }
const case_ = { id: 18, slug: 'phone-case', name: 'Phone Case', price: 19.99, category: 'phone-accessories' }

describe('addItem', () => {
  it('adds a new item', () => {
    expect(addItem([], 8, 2)).toEqual([{ product_id: 8, quantity: 2 }])
  })

  it('adds to an item already there', () => {
    expect(addItem([{ product_id: 8, quantity: 2 }], 8, 3)).toEqual([{ product_id: 8, quantity: 5 }])
  })

  it('stops at ten', () => {
    expect(addItem([{ product_id: 8, quantity: 9 }], 8, 5)).toEqual([{ product_id: 8, quantity: 10 }])
    expect(addItem([], 8, 25)).toEqual([{ product_id: 8, quantity: 10 }])
  })

  it('leaves other items alone and changes nothing in place', () => {
    const before = [{ product_id: 1, quantity: 1 }]
    expect(addItem(before, 8, 1)).toEqual([
      { product_id: 1, quantity: 1 },
      { product_id: 8, quantity: 1 },
    ])
    expect(before).toEqual([{ product_id: 1, quantity: 1 }])
  })
})

describe('setQuantity', () => {
  const items = [
    { product_id: 8, quantity: 2 },
    { product_id: 18, quantity: 1 },
  ]

  it('replaces the quantity', () => {
    expect(setQuantity(items, 8, 7)[0].quantity).toBe(7)
  })

  it('removes at zero', () => {
    expect(setQuantity(items, 8, 0)).toEqual([{ product_id: 18, quantity: 1 }])
  })

  it('stops at ten', () => {
    expect(setQuantity(items, 8, 50)[0].quantity).toBe(10)
  })

  it('adds an item it has not seen', () => {
    expect(setQuantity([], 8, 3)).toEqual([{ product_id: 8, quantity: 3 }])
  })
})

describe('parseGuestCart', () => {
  it('reads a saved cart', () => {
    expect(parseGuestCart('[{"product_id":8,"quantity":2}]')).toEqual([{ product_id: 8, quantity: 2 }])
  })

  it.each([
    ['nothing', null],
    ['empty', ''],
    ['broken JSON', '[{'],
    ['the wrong shape', '{"product_id":8}'],
    ['a number', '5'],
  ])('survives %s', (_name, raw) => {
    expect(parseGuestCart(raw)).toEqual([])
  })

  it('drops entries that make no sense', () => {
    const raw = JSON.stringify([
      { product_id: 8, quantity: 1 },
      { product_id: 'x', quantity: 1 },
      { product_id: 9, quantity: 0 },
      { product_id: 10, quantity: -3 },
      { product_id: 11, quantity: 1.5 },
      { product_id: -1, quantity: 1 },
      null,
    ])
    expect(parseGuestCart(raw)).toEqual([{ product_id: 8, quantity: 1 }])
  })

  it('caps and combines what was tampered with', () => {
    const raw = JSON.stringify([
      { product_id: 8, quantity: 999 },
      { product_id: 9, quantity: 6 },
      { product_id: 9, quantity: 6 },
    ])
    expect(parseGuestCart(raw)).toEqual([
      { product_id: 8, quantity: 10 },
      { product_id: 9, quantity: 10 },
    ])
  })

  it('ignores any price stored beside an item', () => {
    expect(parseGuestCart('[{"product_id":8,"quantity":1,"price":0.01}]')).toEqual([{ product_id: 8, quantity: 1 }])
  })
})

describe('buildView', () => {
  it('totals like the server, with no floating point dust', () => {
    const view = buildView([
      { product: mouse, quantity: 3 },
      { product: case_, quantity: 1 },
    ])
    expect(view.count).toBe(4)
    expect(view.total).toBe(199.96)
    expect(view.items[0].line_total).toBe(179.97)
  })

  it('orders lines by product, as the server does', () => {
    const view = buildView([
      { product: case_, quantity: 1 },
      { product: mouse, quantity: 1 },
    ])
    expect(view.items.map((line) => line.product.id)).toEqual([8, 18])
  })

  it('is empty when nothing is in it', () => {
    expect(buildView([])).toEqual({ items: [], count: 0, total: 0 })
  })
})

describe('changeMessage', () => {
  it('explains each kind of change', () => {
    const name = 'Wireless Mouse'
    expect(changeMessage({ kind: 'combined', product_id: 8, name, quantity: 5 })).toMatch(/Wireless Mouse.*5/)
    expect(changeMessage({ kind: 'capped', product_id: 8, name, quantity: 10 })).toMatch(/Wireless Mouse.*10/)
    expect(changeMessage({ kind: 'unavailable', product_id: 8, name })).toMatch(/Wireless Mouse/)
  })

  it('copes with a product that no longer exists', () => {
    expect(changeMessage({ kind: 'unavailable', product_id: 999, name: null })).toMatch(/An item/)
  })
})
