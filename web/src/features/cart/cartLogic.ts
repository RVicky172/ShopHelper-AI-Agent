import type { CartProduct, CartView, MergeChange } from '../../shared/api/types'

export const MAX_QUANTITY = 10

// What a guest's browser keeps: ids and quantities, never prices.
export interface GuestItem {
  product_id: number
  quantity: number
}

const cap = (quantity: number) => Math.min(quantity, MAX_QUANTITY)

export function addItem(items: GuestItem[], productId: number, quantity: number): GuestItem[] {
  const current = items.find((item) => item.product_id === productId)?.quantity ?? 0
  return setQuantity(items, productId, current + quantity)
}

export function setQuantity(items: GuestItem[], productId: number, quantity: number): GuestItem[] {
  if (quantity <= 0) return items.filter((item) => item.product_id !== productId)
  if (!items.some((item) => item.product_id === productId)) {
    return [...items, { product_id: productId, quantity: cap(quantity) }]
  }
  return items.map((item) => (item.product_id === productId ? { ...item, quantity: cap(quantity) } : item))
}

// Browser storage can be edited by anyone, so nothing in it is trusted.
export function parseGuestCart(raw: string | null): GuestItem[] {
  let saved: unknown
  try {
    saved = JSON.parse(raw ?? '[]')
  } catch {
    return []
  }
  if (!Array.isArray(saved)) return []
  let items: GuestItem[] = []
  for (const entry of saved as Partial<GuestItem>[]) {
    const { product_id: id, quantity } = entry ?? {}
    if (Number.isInteger(id) && Number.isInteger(quantity) && id! > 0 && quantity! > 0) {
      items = addItem(items, id!, quantity!)
    }
  }
  return items
}

const cents = (amount: number) => Math.round(amount * 100)

// The same sums as the server, in whole cents. For display only: checkout prices it again.
export function buildView(lines: { product: CartProduct; quantity: number }[]): CartView {
  const items = [...lines]
    .sort((a, b) => a.product.id - b.product.id)
    .map(({ product, quantity }) => ({
      product,
      quantity,
      line_total: cents(product.price * quantity) / 100,
    }))
  return {
    items,
    count: items.reduce((sum, line) => sum + line.quantity, 0),
    total: items.reduce((sum, line) => sum + cents(line.line_total), 0) / 100,
  }
}

export function changeMessage(change: MergeChange): string {
  const name = change.name ?? 'An item'
  if (change.kind === 'combined') {
    return `${name} was already in your cart, so we added them together. You now have ${change.quantity}.`
  }
  if (change.kind === 'capped') return `${name}: the limit is ${change.quantity}, so your cart has ${change.quantity}.`
  return `${name} is no longer available, so we left it out.`
}
