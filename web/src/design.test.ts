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
