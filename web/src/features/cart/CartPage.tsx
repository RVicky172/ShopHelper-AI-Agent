import { Link } from 'react-router'
import type { User } from '../../shared/api/types'
import { formatPrice } from '../shop/categories'
import { ProductImage } from '../shop/ProductGrid'
import { QuantitySelect } from './QuantitySelect'
import { useCart } from './useCart'

export function CartPage({ user }: { user: User | null }) {
  const { view, loading, setQuantity } = useCart()

  return (
    <div className="mx-auto w-full max-w-page px-gutter py-8">
      <title>Cart · ShopHelper</title>
      <h1 className="text-title font-semibold">Your cart</h1>

      {!loading && view.items.length === 0 && (
        <div className="mt-6">
          <p>Your cart is empty.</p>
          <Link to="/shop/all" className="mt-2 inline-block text-cobalt underline">
            See all products
          </Link>
        </div>
      )}

      {view.items.length > 0 && (
        <div className="mt-6 grid gap-8 lg:grid-cols-[minmax(0,1fr)_320px]">
          <ul className="surface-solid divide-y divide-edge self-start px-4">
            {view.items.map(({ product, quantity, line_total }) => (
              <li key={product.id} className="flex gap-4 py-4">
                <Link to={`/products/${product.slug}`} tabIndex={-1} aria-hidden="true" className="w-24 shrink-0">
                  <ProductImage slug={product.slug} category={product.category} />
                </Link>
                <div className="flex min-w-0 flex-1 flex-wrap items-start justify-between gap-x-6 gap-y-2">
                  <div className="min-w-40 flex-1">
                    <Link to={`/products/${product.slug}`} className="hover:text-cobalt hover:underline">
                      {product.name}
                    </Link>
                    <p className="text-sm text-muted">{formatPrice(product.price)} each</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <QuantitySelect
                      value={quantity}
                      label={`Quantity of ${product.name}`}
                      onChange={(next) => setQuantity(product, next)}
                    />
                    <button
                      type="button"
                      onClick={() => setQuantity(product, 0)}
                      aria-label={`Remove ${product.name}`}
                      className="min-h-11 px-1 text-sm text-muted underline hover:text-ink"
                    >
                      Remove
                    </button>
                  </div>
                  <p className="ml-auto w-24 text-right font-semibold">{formatPrice(line_total)}</p>
                </div>
              </li>
            ))}
          </ul>

          <aside aria-label="Order summary" className="surface-solid self-start p-5">
            <div className="flex items-baseline justify-between">
              <h2 className="text-xl font-semibold">Total</h2>
              <p className="text-title font-semibold">{formatPrice(view.total)}</p>
            </div>
            <p className="mt-1 text-sm text-muted">
              {view.count} {view.count === 1 ? 'item' : 'items'}. This is a pretend shop, so nothing is charged.
            </p>
            <Link
              to={user ? '/checkout' : '/signin?next=%2Fcart'}
              className="mt-4 flex min-h-14 items-center justify-center rounded-xl bg-cobalt px-4 text-center font-semibold text-on-cobalt hover:underline"
            >
              {user ? 'Review and place order' : 'Sign in to place your order'}
            </Link>
          </aside>
        </div>
      )}
    </div>
  )
}
