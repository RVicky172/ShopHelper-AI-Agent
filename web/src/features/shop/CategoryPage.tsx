import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import { useParams, useSearchParams } from 'react-router'
import { api, ApiError } from '../../shared/api/client'
import { NotFound } from '../../shared/layout/NotFound'
import { parseSort, SORTS } from './categories'
import { ProductGrid, ProductGridPlaceholder } from './ProductGrid'

const PAGE = 12

export function CategoryPage() {
  const { category = 'all' } = useParams()
  const [params, setParams] = useSearchParams()
  const sort = parseSort(params.get('sort'))
  const filter = category === 'all' ? null : category

  const categories = useQuery({ queryKey: ['categories'], queryFn: api.categories, staleTime: Infinity })
  const products = useInfiniteQuery({
    queryKey: ['products', filter, sort],
    queryFn: ({ pageParam }) => api.products(filter, sort, pageParam),
    initialPageParam: 0,
    getNextPageParam: (last, pages) => {
      const loaded = pages.reduce((sum, page) => sum + page.items.length, 0)
      return loaded < last.total ? loaded : undefined
    },
  })

  // Load more removes itself on the last page, so focus moves to the first new product.
  const grid = useRef<HTMLDivElement>(null)
  const shown = useRef(0)
  const items = products.data?.pages.flatMap((page) => page.items) ?? []
  useEffect(() => {
    if (shown.current > 0 && items.length > shown.current) {
      grid.current?.querySelector<HTMLElement>(`[data-product-index="${shown.current}"] h3 a`)?.focus()
    }
    shown.current = items.length
  }, [items.length])

  if (products.error instanceof ApiError && products.error.status === 404) {
    return <NotFound title="We can't find that category" />
  }

  const name = filter ? categories.data?.find((c) => c.slug === filter)?.name : 'All products'
  const total = products.data?.pages[0].total

  return (
    <div className="mx-auto w-full max-w-page px-4 py-8">
      <title>{`${name ?? 'Shop'} · ShopHelper`}</title>
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
        <div>
          <h1 className="min-h-10 text-title font-semibold">{name}</h1>
          <p className="min-h-6 text-muted">{total !== undefined && `${total} products`}</p>
        </div>
        <label className="flex items-center gap-2">
          Sort by
          <select
            value={sort}
            onChange={(event) => {
              const next = new URLSearchParams(params)
              next.set('sort', event.target.value)
              setParams(next, { replace: true })
            }}
            className="min-h-11 rounded border border-field bg-paper px-2"
          >
            {SORTS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <h2 className="sr-only">Products</h2>
      <div ref={grid} className="mt-6">
        {products.data ? <ProductGrid products={items} eagerCount={4} /> : <ProductGridPlaceholder count={PAGE} />}
      </div>

      {products.isError && (
        <p role="alert" className="mt-6 text-danger">
          We couldn't load these products. Please try again.
        </p>
      )}

      {total !== undefined && (
        <div className="mt-6 flex items-center gap-4">
          <p className="text-muted" role="status">
            Showing {items.length} of {total}
          </p>
          {products.hasNextPage && (
            <button type="button"
              onClick={() => void products.fetchNextPage()}
              disabled={products.isFetchingNextPage}
              className="min-h-11 rounded border border-field px-4 hover:border-cobalt disabled:opacity-50"
            >
              Load more
            </button>
          )}
        </div>
      )}
    </div>
  )
}
