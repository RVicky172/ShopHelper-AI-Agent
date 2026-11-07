import Markdown from 'react-markdown'
import policy from './returns-policy.md?raw'

// A copy of knowledge/policies/returns.md, because the web container can't see that folder and a
// public API route would widen the login gate. tests/test_shop.py fails if the two ever differ.
export function ReturnsPolicy() {
  return (
    <div className="mx-auto w-full max-w-page px-gutter py-8">
      <title>Return policy · ShopHelper</title>
      <div className="max-w-3xl [&_h1]:text-title [&_h1]:font-semibold [&_li]:mt-3 [&_li]:ml-5 [&_li]:list-disc [&_strong]:font-semibold">
        <Markdown>{policy}</Markdown>
      </div>
    </div>
  )
}
