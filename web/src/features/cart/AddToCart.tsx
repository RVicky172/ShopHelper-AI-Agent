import { useEffect, useState } from 'react'
import type { CartProduct } from '../../shared/api/types'
import { MAX_QUANTITY } from './cartLogic'
import { useCart } from './useCart'

const SHOW_MS = 3000

export function AddToCart({
  product,
  quantity = 1,
  large = false,
}: {
  product: CartProduct
  quantity?: number
  large?: boolean
}) {
  const { add } = useCart()
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!message) return
    const timer = setTimeout(() => setMessage(''), SHOW_MS)
    return () => clearTimeout(timer)
  }, [message])

  const onClick = () => {
    const count = add(product, quantity)
    setMessage(count > 0 ? 'Added to cart' : `Your cart already has ${MAX_QUANTITY} of these`)
  }

  return (
    <div>
      <button
        onClick={onClick}
        className={`w-full rounded bg-cobalt font-medium text-on-cobalt hover:underline ${
          large ? 'min-h-14 px-8 text-xl font-semibold' : 'min-h-11 px-3'
        }`}
      >
        Add to cart
      </button>
      {/* Always present, and sized, so a screen reader hears it and the page doesn't move. */}
      <p role="status" className="mt-1 min-h-5 text-sm text-muted">
        {message}
      </p>
    </div>
  )
}
