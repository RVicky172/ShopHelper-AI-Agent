const REPOSITORY = 'https://github.com/RVicky172/ShopHelper-AI-Agent/blob/main'

function resolvePath(base: string[], relative: string): string[] {
  const parts = [...base]
  for (const part of relative.split('/')) {
    if (part === '..') parts.pop()
    else if (part !== '.') parts.push(part)
  }
  return parts
}

/** Lessons link to each other as files, so they work on GitHub too. On the site they become routes. */
export function toHref(href: string, stage: string): string {
  if (/^[a-z]+:/i.test(href) || href.startsWith('#')) return href
  const [path, anchor] = href.split('#')
  const parts = resolvePath(['docs', 'learn', stage], path)
  const hash = anchor ? `#${anchor}` : ''
  if (parts[0] === 'docs' && parts[1] === 'learn' && parts.length === 4 && parts[3].endsWith('.md')) {
    return `/learn/${parts[2]}/${parts[3].slice(0, -3)}${hash}`
  }
  return `${REPOSITORY}/${parts.join('/')}${hash}`
}
