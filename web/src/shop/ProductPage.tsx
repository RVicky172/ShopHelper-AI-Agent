import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router'
import { api, ApiError } from '../api/client'
import { AddToCart } from '../cart/AddToCart'
import { QuantitySelect } from '../cart/QuantitySelect'
import { useSharedChat } from '../chat/ChatProvider'
import { productStarters } from '../chat/starters'
import { NotFound } from '../layout/NotFound'
import { formatPrice } from './categories'
import { ProductGrid, ProductImage, Rating } from './ProductGrid'

export function ProductPage() {
  const { slug = '' } = useParams()
  const product = useQuery({ queryKey: ['product', slug], queryFn: () => api.product(slug) })
  const categories = useQuery({ queryKey: ['categories'], queryFn: api.categories, staleTime: Infinity })
  const [quantity, setQuantity] = useState(1)
  const { ask } = useSharedChat()

  if (product.error instanceof ApiError && product.error.status === 404) {
    return <NotFound title="We can't find that product" />
  }
  if (product.isError) {
    return (
      <p role="alert" className="mx-auto w-full max-w-page px-4 py-16 text-danger">
        We couldn't load this product. Please try again.
      </p>
    )
  }

  const item = product.data
  if (!item) {
    return (
      <div role="status" aria-label="Loading product" className="mx-auto w-full max-w-page px-4 py-8">
        <div className="grid gap-8 md:grid-cols-2">
          <div className="aspect-square bg-shelf" />
          <div className="h-64 bg-shelf" />
        </div>
      </div>
    )
  }

  const category = categories.data?.find((c) => c.slug === item.category)

  return (
    <div className="mx-auto w-full max-w-page px-4 py-6">
      <title>{`${item.name} · ShopHelper`}</title>
      <nav aria-label="Breadcrumb" className="text-sm text-muted">
        <Link to="/shop/all" className="underline hover:text-ink">
          Shop
        </Link>
        {' / '}
        <Link to={`/shop/${item.category}`} className="underline hover:text-ink">
          {category?.name ?? 'Category'}
        </Link>
      </nav>

      <div className="mt-4 grid gap-8 md:grid-cols-2">
        <ProductImage slug={item.slug} category={item.category} alt={item.name} eager />
        <div>
          <h1 className="text-title leading-tight font-semibold">{item.name}</h1>
          <div className="mt-2">
            <Rating rating={item.rating} count={item.rating_count} />
          </div>
          <p className="mt-4 text-title font-semibold">{formatPrice(item.price)}</p>
          <div className="mt-4 flex max-w-md items-start gap-3">
            <QuantitySelect value={quantity} onChange={setQuantity} label="Quantity" />
            <div className="flex-1">
              <AddToCart product={item} quantity={quantity} large />
            </div>
          </div>
          <p className="mt-2 text-sm text-muted">
            30-day returns.{' '}
            <Link to="/policies/returns" className="text-cobalt underline">
              Return policy
            </Link>
          </p>
        </div>
      </div>

      <section className="mt-10 max-w-3xl border-t border-rule pt-6">
        <h2 className="text-xl font-semibold">Description</h2>
        <p className="mt-2">{item.description}</p>
      </section>

      <section className="mt-8 max-w-3xl border-t border-rule pt-6">
        <h2 className="text-xl font-semibold">Specifications</h2>
        <dl className="mt-2 divide-y divide-rule">
          {Object.entries(item.specs).map(([name, value]) => (
            <div key={name} className="grid grid-cols-2 gap-4 py-2">
              <dt className="text-muted">{name}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="mt-8 max-w-3xl border-t border-rule pt-6">
        <h2 className="text-xl font-semibold">Questions before you buy?</h2>
        <ul className="mt-3 flex flex-wrap gap-2">
          {productStarters(item.name, category?.name ?? 'our products').map((question) => (
            <li key={question}>
              <button
                onClick={() => ask(question)}
                className="min-h-11 rounded border border-field px-3 py-2 text-left hover:border-cobalt"
              >
                {question}
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-10 border-t border-rule pt-6">
        <h2 className="mb-4 text-xl font-semibold">Related products</h2>
        <ProductGrid products={item.related} />
      </section>
    </div>
  )
}
