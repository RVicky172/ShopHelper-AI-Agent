// Every starter must be something the agent can really answer, and it knows only orders and policies.
// It has no catalogue, so a product starter names the category: that's how the policies describe products.

export function productStarters(name: string, category: string): string[] {
  const where = category.toLowerCase()
  return [`What's the warranty on the ${name} (${where})?`, `How do returns work for the ${name} (${where})?`]
}

// Measured against the live agent: "How long does delivery take?" made it ask for an order number,
// and "What is your delivery policy?" retrieved a passage with no delivery times in it.
const GENERAL = [
  'What are your shipping options and delivery times?',
  'What is your return policy?',
  'How long do refunds take?',
]

export function startersFor({
  pathname,
  product,
  latestOrderId,
}: {
  pathname: string
  product?: { name: string; category: string }
  latestOrderId?: string
}): string[] {
  if (pathname.startsWith('/products/') && product) return productStarters(product.name, product.category)
  if (pathname === '/cart') return GENERAL.slice(0, 2)
  if (pathname.endsWith('/orders')) {
    const help = ['How long do refunds take?', 'What is your cancellation policy?']
    return latestOrderId ? [`Where is order ${latestOrderId}?`, ...help] : help
  }
  return GENERAL
}
