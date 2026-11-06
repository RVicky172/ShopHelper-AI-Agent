import { lazy, type ReactNode, Suspense, useEffect, useState } from 'react'
import Markdown, { type Components } from 'react-markdown'
import { Link } from 'react-router'
import rehypeHighlight from 'rehype-highlight'
import remarkGfm from 'remark-gfm'
import { CheckYourself } from './CheckYourself'
import type { Lesson } from './course'
import { checkQuestions, interviewQuestions, type ParsedLesson, parseLesson } from './lessons'
import { toHref } from './links'

// Lessons come one at a time. The largest piece, Mermaid, comes only with a lesson that has a diagram.
const files = import.meta.glob('../../../../docs/learn/*/*.md', { query: '?raw', import: 'default' })
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

function Text({ stage, children }: { stage: string; children: string }) {
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

function Interview({ stage, body }: { stage: string; body: string }) {
  return (
    <div className="mt-3 space-y-2">
      {interviewQuestions(body).map((item) => (
        <details key={item.question} className="rounded border border-rule px-4 py-2">
          <summary className="min-h-11 cursor-pointer py-2 font-medium">{item.question}</summary>
          <div className="pb-2">
            <p className="text-sm font-medium text-muted">A strong answer</p>
            <Text stage={stage}>{item.answer}</Text>
            <p className="mt-3 text-sm font-medium text-muted">Likely follow-up</p>
            <Text stage={stage}>{item.followUp}</Text>
          </div>
        </details>
      ))}
    </div>
  )
}

function Part({ stage, title, body }: { stage: string; title: string; body: string }): ReactNode {
  const heading = <h2>{title}</h2>
  if (title === 'Interview questions') {
    return (
      <section>
        {heading}
        <Interview stage={stage} body={body} />
      </section>
    )
  }
  if (title === 'Check yourself') {
    return (
      <section>
        {heading}
        <CheckYourself questions={checkQuestions(body)} />
      </section>
    )
  }
  return (
    <section>
      {heading}
      <Text stage={stage}>{body}</Text>
    </section>
  )
}

export function LessonBody({ lesson }: { lesson: Lesson }) {
  const [parsed, setParsed] = useState<ParsedLesson | null>(null)

  useEffect(() => {
    let current = true
    const load = files[`../../../../docs/learn/${lesson.stage}/${lesson.id}.md`]
    load?.().then((text) => {
      if (current) setParsed(parseLesson(text as string))
    })
    return () => {
      current = false
    }
  }, [lesson.stage, lesson.id])

  if (!parsed) return <div className="mt-6 min-h-96" aria-hidden="true" />
  return (
    <div className="lesson mt-4">
      {parsed.intro.trim() && <Text stage={lesson.stage}>{parsed.intro}</Text>}
      {parsed.sections.map((section) => (
        <Part key={section.title} stage={lesson.stage} title={section.title} body={section.body} />
      ))}
    </div>
  )
}
