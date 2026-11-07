import { lazy, Suspense } from 'react'
import Markdown, { type Components } from 'react-markdown'
import { Link } from 'react-router'
import rehypeHighlight from 'rehype-highlight'
import remarkGfm from 'remark-gfm'
import { toHref } from './links'

// The largest piece, Mermaid, comes only with a lesson that has a diagram.
const Diagram = lazy(() => import('./Diagram').then((m) => ({ default: m.Diagram })))

type HastNode = { type?: string; value?: string; tagName?: string; children?: HastNode[]; data?: { meta?: string } }

function textOf(node?: HastNode): string {
  if (!node) return ''
  return node.value ?? (node.children ?? []).map(textOf).join('')
}

function components(stage: string): Components {
  return {
    a({ href = '', children }) {
      const target = toHref(href, stage)
      if (target.startsWith('/learn/')) return <Link to={target}>{children}</Link>
      return (
        <a href={target} target={target.startsWith('#') ? undefined : '_blank'} rel="noreferrer">
          {children}
        </a>
      )
    },
    pre({ node, children }) {
      const code = (node as HastNode | undefined)?.children?.find((child) => child.tagName === 'code')
      const className = String((code as { properties?: { className?: string[] } })?.properties?.className ?? '')
      if (className.includes('language-mermaid')) {
        return (
          <Suspense fallback={<div className="diagram-space" />}>
            <Diagram source={textOf(code)} />
          </Suspense>
        )
      }
      const file = /file=(\S+)/.exec(code?.data?.meta ?? '')?.[1]
      return (
        <figure>
          {file && <figcaption>{file}</figcaption>}
          {/* biome-ignore lint/a11y/noNoninteractiveTabindex: a long code line must be reachable by keyboard */}
          <pre tabIndex={0}>{children}</pre>
        </figure>
      )
    },
    table({ children }) {
      return (
        // biome-ignore lint/a11y/noNoninteractiveTabindex: a wide table must be reachable by keyboard
        <div className="lesson-table" tabIndex={0}>
          <table>{children}</table>
        </div>
      )
    },
  }
}

export function Text({ stage, children }: { stage: string; children: string }) {
  return (
    <Markdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[[rehypeHighlight, { plainText: ['mermaid', 'text'] }]]}
      components={components(stage)}
    >
      {children}
    </Markdown>
  )
}
