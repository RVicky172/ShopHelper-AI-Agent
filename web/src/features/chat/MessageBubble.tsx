import Markdown from 'react-markdown'
import type { Message } from './chatReducer'

// `plain` is the shop's chat: the wording only. How it works adds the sources and timing.
export function MessageBubble({ message, plain = false }: { message: Message; plain?: boolean }) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded bg-cobalt px-3 py-2 whitespace-pre-wrap text-on-cobalt">
          {message.text}
        </p>
      </div>
    )
  }

  const result = message.result
  const blocked = result?.status === 'blocked'
  return (
    <div className="max-w-[90%]">
      <div
        className={`rounded border px-3 py-2 ${
          blocked ? 'border-danger/50 bg-danger/10' : 'border-rule bg-paper'
        }`}
      >
        {message.text ? (
          <div className="markdown">
            <Markdown>{message.text}</Markdown>
          </div>
        ) : (
          message.streaming && <p className="text-muted motion-safe:animate-pulse">Working...</p>
        )}
        {message.error && <p className="text-danger">{message.error}</p>}
      </div>

      {!plain && result && (result.citations.length > 0 || result.latency_ms > 0) && (
        <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 px-1 text-xs text-muted">
          {result.citations.length > 0 && <span>Retrieved from</span>}
          {result.citations.map((source) => (
            <span key={source} className="rounded bg-rag/15 px-1.5 py-0.5 font-mono">
              {source}
            </span>
          ))}
          {result.latency_ms > 0 && <span>{(result.latency_ms / 1000).toFixed(1)}s</span>}
        </div>
      )}
    </div>
  )
}
