import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { api } from '../../shared/api/client'
import type { Category } from '../../shared/api/types'
import { tintOf } from './categories'
import { ProductGrid, ProductGridPlaceholder, ProductImage } from './ProductGrid'

const TOP_RATED = 4
const CATEGORY_COUNT = 8

// The one bold moment on the site: the whole shop on one printed page.
function CategoryTile({ category }: { category: Category }) {
  return (
    <li>
      <Link to={`/shop/${category.slug}`} className="block h-full" style={{ background: tintOf(category.slug) }}>
        <ProductImage slug={category.cover.slug} category={category.slug} eager wide />
        <span className="block px-3 pb-3">
          <span className="block text-xl font-semibold">{category.name}</span>
          <span className="block text-sm">{category.cover.name}</span>
        </span>
      </Link>
    </li>
  )
}

function TilePlaceholder() {
  return (
    <li aria-hidden="true" className="bg-shelf">
      <div className="aspect-[4/3]" />
      <div className="h-[3.75rem]" />
    </li>
  )
}

export function Landing() {
  const categories = useQuery({ queryKey: ['categories'], queryFn: api.categories, staleTime: Infinity })
  const top = useQuery({
    queryKey: ['products', 'top', TOP_RATED],
    queryFn: () => api.products(null, 'rating', 0, TOP_RATED),
  })

  return (
    <div className="mx-auto w-full max-w-page px-4 py-8">
      <title>ShopHelper</title>
      <h1 className="text-display leading-none font-semibold tracking-tight text-balance">
        Everything for your desk, bag and home.
      </h1>

      <ul className="mt-8 grid grid-cols-2 gap-px bg-rule lg:grid-cols-4">
        {categories.data
          ? categories.data.map((category) => <CategoryTile key={category.slug} category={category} />)
          : Array.from({ length: CATEGORY_COUNT }, (_, index) => <TilePlaceholder key={index} />)}
      </ul>

      <div className="mt-12 mb-4 flex items-baseline justify-between gap-4">
        <h2 className="text-title font-semibold">Top rated</h2>
        <Link to="/shop/all" className="text-cobalt underline">
          See all {top.data?.total ?? ''} products
        </Link>
      </div>
      {top.data ? <ProductGrid products={top.data.items} /> : <ProductGridPlaceholder count={TOP_RATED} />}
    </div>
  )
}
