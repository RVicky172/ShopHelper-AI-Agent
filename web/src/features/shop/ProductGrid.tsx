import { useState } from 'react'
import { Link } from 'react-router'
import type { Product } from '../../shared/api/types'
import { AddToCart } from '../cart/AddToCart'
import { formatPrice, tintOf } from './categories'

export function ProductImage({
  slug,
  category,
  alt = '',
  eager = false,
  wide = false,
}: {
  slug: string
  category: string
  alt?: string
  eager?: boolean
  wide?: boolean
}) {
  const [missing, setMissing] = useState(false)
  // Square and sized up front, so the page doesn't jump when the image arrives.
  return (
    <div className={wide ? 'aspect-[4/3]' : 'aspect-square'} style={{ background: tintOf(category) }}>
      {!missing && (
        <img
          src={`/products/${slug}.svg`}
          alt={alt}
          width={400}
          height={400}
          loading={eager ? 'eager' : 'lazy'}
          onError={() => setMissing(true)}
          className="size-full object-contain"
        />
      )}
    </div>
  )
}

export function Rating({ rating, count }: { rating: number; count: number }) {
  return (
    <p role="img" className="flex items-center gap-1 text-sm" aria-label={`Rated ${rating} out of 5, from ${count} ratings`}>
      <span aria-hidden="true" className="text-marigold">
        ★
      </span>
      <span aria-hidden="true">
        {rating.toFixed(1)} <span className="text-muted">({count})</span>
      </span>
    </p>
  )
}

function ProductCell({ product, index, eager }: { product: Product; index: number; eager: boolean }) {
  const to = `/products/${product.slug}`
  return (
    <li data-product-index={index} className="flex flex-col border-r border-b border-rule">
      <Link to={to} tabIndex={-1} aria-hidden="true">
        <ProductImage slug={product.slug} category={product.category} eager={eager} />
      </Link>
      <div className="flex flex-1 flex-col gap-1 p-3">
        <h3 className="min-h-12 line-clamp-2">
          <Link to={to} className="hover:text-cobalt hover:underline">
            {product.name}
          </Link>
        </h3>
        <Rating rating={product.rating} count={product.rating_count} />
        <p className="text-xl font-semibold">{formatPrice(product.price)}</p>
        <div className="mt-auto pt-1">
          <AddToCart product={product} />
        </div>
      </div>
    </li>
  )
}

function PlaceholderCell() {
  return (
    <li aria-hidden="true" className="flex flex-col border-r border-b border-rule">
      <div className="aspect-square bg-shelf" />
      <div className="flex flex-1 flex-col gap-1 p-3">
        <div className="min-h-12">
          <div className="h-4 w-3/4 bg-shelf" />
        </div>
        <div className="h-5 w-1/3 bg-shelf" />
        <div className="h-7 w-1/2 bg-shelf" />
        <div className="mt-1 h-11 bg-shelf" />
        <div className="mt-1 min-h-5" />
      </div>
    </li>
  )
}

const GRID = 'grid grid-cols-2 border-t border-l border-rule lg:grid-cols-4'

export function ProductGrid({ products, eagerCount = 0 }: { products: Product[]; eagerCount?: number }) {
  return (
    <ul className={GRID}>
      {products.map((product, index) => (
        <ProductCell key={product.id} product={product} index={index} eager={index < eagerCount} />
      ))}
    </ul>
  )
}

// Same shape as the real grid, so the page doesn't move when the products arrive.
export function ProductGridPlaceholder({ count }: { count: number }) {
  return (
    <ul className={GRID} role="status" aria-label="Loading products">
      {Array.from({ length: count }, (_, index) => (
        <PlaceholderCell key={index} />
      ))}
    </ul>
  )
}
