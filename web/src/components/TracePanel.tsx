import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'
import type { Passage } from '../api/types'
import type { TraceItem, Turn } from '../chat/chatReducer'

const seconds = (ms: number) => `${(ms / 1000).toFixed(2)}s`

const passagesOf = (result: unknown): Passage[] | null => {
  const passages = (result as { passages?: Passage[] } | null)?.passages
  return Array.isArray(passages) ? passages : null
}

function Row({
  tone,
  title,
  at,
  why,
  children,
}: {
  tone: string
  title: string
  at: number
  why?: string
  children?: ReactNode
}) {
  return (
    <li className="relative pl-6 pb-4 last:pb-0">
      <span className="absolute left-0 top-1 size-2.5 rounded-full" style={{ background: tone }} />
      <span className="absolute left-[4.5px] top-4 bottom-0 w-px bg-rule" />
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-sm font-medium">{title}</p>
        <span className="font-mono text-xs text-muted tabular-nums">{seconds(at)}</span>
      </div>
      {why && <p className="mt-0.5 text-xs text-muted">{why}</p>}
      {children && <div className="mt-2">{children}</div>}
    </li>
  )
}

function Json({ value }: { value: unknown }) {
  const text = typeof value === 'string' ? value : JSON.stringify(value, null, 2)
  return (
    <pre className="max-h-48 overflow-auto rounded bg-shelf p-2 font-mono text-xs whitespace-pre-wrap break-words">
      {text}
    </pre>
  )
}

function Passages({ passages }: { passages: Passage[] }) {
  return (
    <ul className="space-y-1.5">
      {passages.map((p) => (
        <li key={`${p.source}-${p.chunk_index}`}>
          <details className="rounded bg-shelf px-2 py-1.5 text-xs">
            <summary className="flex cursor-pointer items-center gap-2">
              <span className="min-w-0 flex-1 truncate font-mono">{p.source}</span>
              <span className="h-1.5 w-12 overflow-hidden rounded-full bg-rule">
                <span
                  className="block h-full bg-rag"
                  style={{ width: `${Math.max(0, p.score) * 100}%` }}
                />
              </span>
              <span className="font-mono tabular-nums">{p.score.toFixed(3)}</span>
            </summary>
            <p className="mt-1.5 whitespace-pre-wrap text-muted">{p.text}</p>
          </details>
        </li>
      ))}
    </ul>
  )
}

function Item({ item }: { item: TraceItem }) {
  switch (item.kind) {
    case 'guardrail': {
      const { stage, action, reasons } = item.data
      const stopped = action === 'blocked'
      return (
        <Row
          tone={stopped ? 'var(--color-danger)' : 'var(--color-guard)'}
          title={`${stage === 'input' ? 'Input' : 'Output'} guardrail: ${action}`}
          at={item.at}
          why={
            stopped
              ? 'Stopped here. The model never sees this message.'
              : stage === 'input'
                ? 'Checks the message before the model sees it.'
                : 'Checks the finished answer before it is final.'
          }
        >
          {reasons.length > 0 && <Json value={reasons.join('\n')} />}
        </Row>
      )
    }
    case 'model':
      return (
        <Row
          tone="var(--color-cobalt)"
          title={`Model call ${item.data.step}: chose ${item.data.tool_calls.join(', ')}`}
          at={item.at}
          why={`The model doesn't run tools. It asks for one, and our code runs it. ${item.data.input_tokens} tokens in, ${item.data.output_tokens} out, ${seconds(item.data.ms)}.`}
        />
      )
    case 'tool': {
      const passages = item.end && passagesOf(item.end.result)
      const isRag = item.start.name === 'search_policy'
      return (
        <Row
          tone={isRag ? 'var(--color-rag)' : 'var(--color-tool)'}
          title={`Tool: ${item.start.name}`}
          at={item.at}
          why={
            !item.end
              ? item.start.name === 'request_refund'
                ? 'Not run by the model: the refund node checks policy, then asks a human.'
                : 'Running...'
              : item.start.name === 'request_refund'
                ? "The human's decision is applied, and the result goes back to the model."
                : isRag
                ? `RAG: the question was embedded and pgvector returned the nearest chunks. ${seconds(item.end.ms)}.`
                : `Finished in ${seconds(item.end.ms)}. The result goes back to the model.`
          }
        >
          <div className="space-y-1.5">
            {Object.keys(item.start.args).length > 0 && <Json value={item.start.args} />}
            {passages ? <Passages passages={passages} /> : item.end && <Json value={item.end.result} />}
          </div>
        </Row>
      )
    }
    case 'answer':
      return (
        <Row
          tone="var(--color-cobalt)"
          title={item.step ? `Model call ${item.step.step}: final answer` : 'Model is writing...'}
          at={item.at}
          why={
            item.step
              ? `First token at ${seconds(item.at)}. ${item.step.input_tokens} tokens in, ${item.step.output_tokens} out.`
              : `${item.tokens} chunks received so far.`
          }
        />
      )
    case 'interrupt':
      return (
        <Row
          tone="var(--color-warn)"
          title="Paused for human approval"
          at={item.at}
          why="The graph stopped and saved its state to Postgres. It stays paused until staff decide."
        />
      )
    case 'final':
      return (
        <Row
          tone="var(--color-muted)"
          title="Turn finished"
          at={item.at}
          why={`${item.data.status}. ${item.data.input_tokens + item.data.output_tokens} tokens in total.`}
        />
      )
    case 'error':
      return <Row tone="var(--color-danger)" title="Error" at={item.at} why={item.message} />
  }
}

export function TracePanel({ turns, focus }: { turns: Turn[]; focus?: string | null }) {
  const focused = useRef<HTMLDetailsElement>(null)
  useEffect(() => {
    focused.current?.scrollIntoView({ block: 'start' })
  }, [focus])

  if (turns.length === 0) {
    return (
      <div className="p-5 text-sm text-muted">
        <p className="font-medium text-ink">Under the hood</p>
        <p className="mt-1">
          Send a message and every step appears here live: guardrails, model calls, tools, retrieved
          chunks and approvals.
        </p>
      </div>
    )
  }
  return (
    <div className="space-y-2 p-3">
      {[...turns].reverse().map((turn, index) => (
        <details
          key={turn.id}
          ref={turn.id === focus ? focused : undefined}
          open={focus ? turn.id === focus : index === 0}
          className="rounded border border-rule bg-paper"
        >
          <summary className="cursor-pointer truncate px-3 py-2 text-sm font-medium">{turn.label}</summary>
          <ol className="px-3 pt-1 pb-3">
            {turn.items.map((item, i) => (
              <Item key={i} item={item} />
            ))}
          </ol>
        </details>
      ))}
    </div>
  )
}
