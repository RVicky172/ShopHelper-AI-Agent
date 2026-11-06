import type { ProductSort } from '../../shared/api/types'

// Each category's flat colour, named in index.css. tests/test_shop.py checks that every category has one.
const TINTS: Record<string, string> = {
  audio: 'audio',
  'keyboards-and-mice': 'keyboards',
  'laptop-accessories': 'laptop',
  'phone-accessories': 'phone',
  'power-and-charging': 'power',
  'home-and-kitchen': 'home',
  'bags-and-travel': 'bags',
  'fitness-and-outdoors': 'fitness',
}

export const tintOf = (category: string) => `var(--color-tint-${TINTS[category] ?? 'audio'})`

export const SORTS: { value: ProductSort; label: string }[] = [
  { value: 'rating', label: 'Top rated' },
  { value: 'price_asc', label: 'Price: low to high' },
  { value: 'price_desc', label: 'Price: high to low' },
  { value: 'newest', label: 'Newest' },
]

// From the URL, so it can hold anything.
export function parseSort(value: string | null): ProductSort {
  return SORTS.find((sort) => sort.value === value)?.value ?? 'rating'
}

export const formatPrice = (price: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(price)
