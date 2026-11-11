import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'
import { describe, expect, it } from 'vitest'

const SRC = import.meta.dirname
const read = (path: string) => readFileSync(join(SRC, path), 'utf-8')

function sources(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name)
    if (statSync(path).isDirectory()) return sources(path)
    return /\.(tsx|css)$/.test(name) && !name.includes('.test.') ? [path] : []
  })
}

/** Every line outside the one design file that breaks a rule. */
function breaking(rule: RegExp): string[] {
  return sources(SRC).flatMap((path) => {
    const name = relative(SRC, path).replaceAll('\\', '/')
    if (name === 'index.css') return []
    return readFileSync(path, 'utf-8')
      .split('\n')
      .flatMap((line, at) => (rule.test(line) ? [`${name}:${at + 1}`] : []))
  })
}

describe('one glass recipe', () => {
  const css = read('index.css')

  it('keeps blur inside the design file', () => {
    expect(breaking(/backdrop-filter|backdrop-blur|blur\(/)).toEqual([])
  })

  it('keeps raw colours inside the design file', () => {
    expect(breaking(/#[0-9a-fA-F]{6}\b|rgba?\(/)).toEqual([])
  })

  it('defines every surface', () => {
    for (const surface of ['glass-chrome', 'glass-card', 'surface-solid']) {
      expect(css).toContain(`@utility ${surface}`)
    }
  })

  it('makes every surface solid when glass is unavailable or unwanted', () => {
    expect(css).toContain('@supports not (backdrop-filter')
    expect(css).toContain('prefers-reduced-transparency: reduce')
    expect(css).toContain('forced-colors: active')
  })

  it('keeps paper under the ground, and body clear so the ground shows', () => {
    expect(css).toMatch(/html\s*\{[^}]*background: var\(--color-paper\)/)
    expect(css).toMatch(/body\s*\{[^}]*background: transparent/)
  })
})

describe('the shop', () => {
  const css = read('index.css')

  it('puts tiles and cards on glass that needs no blur, because the ground is already soft', () => {
    const tile = /@utility glass-tile\s*\{([^}]*)\}/.exec(css)?.[1] ?? ''
    expect(tile).toContain('--surface-card')
    expect(tile).not.toContain('backdrop-filter')
    expect(read('features/shop/Landing.tsx')).toContain('glass-tile')
    expect(read('features/shop/ProductGrid.tsx')).toContain('glass-tile')
    expect(read('features/shop/ProductPage.tsx')).toContain('glass-tile')
  })

  it('keeps placeholders on the same shape, so the page does not jump when products arrive', () => {
    const grid = read('features/shop/ProductGrid.tsx')
    expect(grid.match(/CARD/g)?.length).toBeGreaterThanOrEqual(3)
    expect(read('features/shop/Landing.tsx').match(/TILE/g)?.length).toBeGreaterThanOrEqual(3)
  })

  it('lifts a card only when motion is welcome', () => {
    const motion = css.slice(css.indexOf('@media (prefers-reduced-motion: no-preference)'))
    expect(motion).toContain('.card-lift:hover')
    expect(css.indexOf('.card-lift:hover')).toBe(
      css.indexOf('.card-lift:hover', css.indexOf('@media (prefers-reduced-motion')),
    )
  })

  it('keeps reading and paying on a nearly solid surface', () => {
    for (const page of [
      'features/shop/ProductPage.tsx',
      'features/cart/CartPage.tsx',
      'features/cart/CheckoutPage.tsx',
    ]) {
      expect(read(page)).toContain('surface-solid')
    }
  })
})

describe('the rest of the site', () => {
  it('leaves no old flat panel, button or field behind', () => {
    expect(breaking(/rounded border border-rule bg-paper/)).toEqual([])
    expect(breaking(/\brounded bg-cobalt/)).toEqual([])
    expect(breaking(/\brounded border border-field/)).toEqual([])
  })

  it('uses only colours that exist', () => {
    expect(breaking(/divide-line/)).toEqual([])
  })

  it('keeps reading and work on a nearly solid surface', () => {
    for (const page of [
      'features/learn/Learn.tsx',
      'features/auth/AuthPage.tsx',
      'features/shop/OrdersView.tsx',
      'features/staff/QueueView.tsx',
      'features/staff/UsersView.tsx',
      'features/how-it-works/ToolsView.tsx',
    ]) {
      expect(read(page)).toContain('surface-solid')
    }
  })

  it('puts the course map on glass, clear of the floating navbar', () => {
    const nav = read('features/learn/CourseNav.tsx')
    expect(nav).toContain('glass-tile')
    expect(nav).not.toContain('sticky top-4')
    expect(read('features/learn/Learn.tsx')).toContain('glass-tile')
  })
})

describe('the first paint', () => {
  it('holds a full screen while a page or lesson loads, so nothing below it gets pushed', () => {
    expect(read('shared/layout/Layout.tsx')).toContain('<Suspense fallback={<div className="min-h-dvh" />}>')
    expect(read('features/learn/LessonBody.tsx')).toContain('className="mt-6 min-h-dvh"')
  })

  it('keeps code colouring off the path to the first words of a lesson', () => {
    const text = read('features/learn/LessonText.tsx')
    expect(text).not.toMatch(/^import .* from 'rehype-highlight'/m)
    expect(text).toContain("import('rehype-highlight')")
  })

  it('keeps Markdown components stable, or late colouring would redraw every diagram', () => {
    expect(read('features/learn/LessonText.tsx')).toContain('useMemo(() => components(stage), [stage])')
  })
})

describe('the shell sits on glass', () => {
  it('gives the navbar its glass on a layer, so a menu inside it can still blur the page', () => {
    expect(read('shared/layout/Navbar.tsx')).toContain('glass-bar')
    expect(read('index.css')).toMatch(/@utility glass-bar\s*\{[^}]*&::before/)
  })

  it('puts menus, the chat and the phone bar on surfaces', () => {
    expect(read('shared/layout/Menu.tsx')).toContain('glass-chrome')
    expect(read('features/chat/ChatPanel.tsx')).toContain('glass-chrome')
    expect(read('features/chat/ChatLauncher.tsx')).toContain('glass-card')
    expect(read('shared/layout/Layout.tsx')).toContain('glass-card')
  })

  it('leaves no solid page behind the shell', () => {
    expect(read('shared/layout/Layout.tsx')).not.toContain('h-dvh flex-col bg-paper')
  })
})
