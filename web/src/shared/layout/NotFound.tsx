import { Link } from 'react-router'

export function NotFound({ title = "We can't find that page" }: { title?: string }) {
  return (
    <div className="mx-auto w-full max-w-page px-gutter py-16">
      <title>Not found · ShopHelper</title>
      <h1 className="text-title font-semibold">{title}</h1>
      <p className="mt-2 text-muted">It may have moved, or the link may be wrong.</p>
      <Link to="/shop/all" className="mt-4 inline-block text-cobalt underline">
        See all products
      </Link>
    </div>
  )
}
