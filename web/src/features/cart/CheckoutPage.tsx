import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRef } from 'react'
import { Navigate, useNavigate } from 'react-router'
import { api } from '../../shared/api/client'
import type { User } from '../../shared/api/types'
import { formatPrice } from '../shop/categories'
import { useCart } from './useCart'

export function CheckoutPage({ user }: { user: User }) {
  const { view, loading } = useCart()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const placed = useRef(false)
  const sending = useRef(false) // set at once: a disabled button only takes effect after a render

  const place = useMutation({
    mutationFn: api.checkout, // sends nothing: the server reads the cart and the prices itself
    onSuccess: (order) => {
      placed.current = true
      const orders = user.role === 'customer' ? '/account/orders' : '/staff/orders'
      navigate(`${orders}?placed=${order.order_id}`, { replace: true })
      queryClient.setQueryData(['cart'], { items: [], count: 0, total: 0 })
      void queryClient.invalidateQueries({ queryKey: ['orders'] })
    },
    onError: () => {
      sending.current = false
      void queryClient.invalidateQueries({ queryKey: ['cart'] })
    },
  })

  if (placed.current) return null
  if (!loading && view.items.length === 0) return <Navigate to="/cart" replace />

  return (
    <div className="mx-auto w-full max-w-xl px-4 py-8">
      <title>Place order · ShopHelper</title>
      <h1 className="text-title font-semibold">Review your order</h1>
      <ul className="mt-6 border-t border-rule">
        {view.items.map(({ product, quantity, line_total }) => (
          <li key={product.id} className="flex justify-between gap-4 border-b border-rule py-3">
            <span>
              {product.name} <span className="text-muted">x {quantity}</span>
            </span>
            <span>{formatPrice(line_total)}</span>
          </li>
        ))}
      </ul>
      <div className="mt-4 flex items-baseline justify-between">
        <h2 className="text-xl font-semibold">Total</h2>
        <p className="text-title font-semibold">{formatPrice(view.total)}</p>
      </div>
      <p className="mt-1 text-sm text-muted">This is a pretend shop, so nothing is charged or shipped.</p>
      {place.isError && (
        <p role="alert" className="mt-3 text-danger">
          {place.error.message}
        </p>
      )}
      <button
        onClick={() => {
          if (sending.current) return
          sending.current = true
          place.mutate()
        }}
        disabled={place.isPending || loading}
        className="mt-4 min-h-14 w-full rounded bg-cobalt px-4 font-semibold text-on-cobalt hover:underline disabled:opacity-50"
      >
        Place order
      </button>
    </div>
  )
}
