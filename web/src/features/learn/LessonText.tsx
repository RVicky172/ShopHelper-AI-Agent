import { lazy, Suspense, useEffect, useMemo, useState } from 'react'
import Markdown, { type Components, type Options } from 'react-markdown'
import { Link } from 'react-router'
import remarkGfm from 'remark-gfm'
import { toHref } from './links'

// The largest piece, Mermaid, comes only with a lesson that has a diagram.
const Diagram = lazy(() => import('./Diagram').then((m) => ({ default: m.Diagram })))

type Plugins = NonNullable<Options['rehypePlugins']>
let colouring: Plugins | undefined

// Code colours are a large download that nobody needs to start reading, so they arrive after the words.
// They only change colour, so nothing moves when they land.
function useColouring(needed: boolean) {
  const [plugins, setPlugins] = useState(colouring)

  useEffect(() => {
    if (!needed || plugins) return
    let current = true
    void import('rehype-highlight').then(({ default: rehypeHighlight }) => {
      colouring = [[rehypeHighlight, { plainText: ['mermaid', 'text'] }]]
      if (current) setPlugins(colouring)
    })
    return () => {
      current = false
    }
  }, [needed, plugins])

  return plugins
}

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
  const plugins = useColouring(children.includes('```'))
  // New functions here would remount every code block and diagram when the colours land.
  const parts = useMemo(() => components(stage), [stage])
  return (
    <Markdown remarkPlugins={[remarkGfm]} rehypePlugins={plugins} components={parts}>
      {children}
    </Markdown>
  )
}
