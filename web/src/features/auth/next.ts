const BASE = 'http://this-site.invalid'
const AUTH_PAGES = ['/signin', '/signup']

// `next` arrives in the URL, so anyone can craft it. Asking the URL parser where it really points
// catches what a text check misses: browsers also read `/\` as `//`, and they drop tabs and newlines.
export function safeNext(next: string | null): string {
  if (!next?.startsWith('/')) return '/'
  try {
    const url = new URL(next, BASE)
    if (url.origin !== BASE || AUTH_PAGES.includes(url.pathname)) return '/'
    return url.pathname + url.search + url.hash
  } catch {
    return '/'
  }
}

export function signInPath({ pathname, search }: { pathname: string; search: string }): string {
  const here = AUTH_PAGES.includes(pathname)
    ? new URLSearchParams(search).get('next')
    : pathname + search
  const next = safeNext(here)
  return next === '/' ? '/signin' : `/signin?next=${encodeURIComponent(next)}`
}
