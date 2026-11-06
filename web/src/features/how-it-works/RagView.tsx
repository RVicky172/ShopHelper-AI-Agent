import { useMutation, useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { api } from '../../shared/api/client'
import type { Chunk } from '../../shared/api/types'

export function RagView() {
  const [query, setQuery] = useState('Can I return an opened laptop stand?')
  const [k, setK] = useState(4)
  const search = useMutation({ mutationFn: () => api.ragSearch(query.trim(), k) })
  const chunks = useQuery({ queryKey: ['chunks'], queryFn: api.chunks })

  const bySource = useMemo(() => {
    const groups = new Map<string, Chunk[]>()
    for (const chunk of chunks.data ?? []) {
      groups.set(chunk.source, [...(groups.get(chunk.source) ?? []), chunk])
    }
    return [...groups.entries()]
  }, [chunks.data])

  const result = search.data
  const maxAbs = Math.max(...(result?.embedding_preview.map(Math.abs) ?? [1]))

  return (
    <div className="min-h-0 flex-1 overflow-y-auto">
      <div className="mx-auto w-full max-w-page space-y-8 px-4 py-8">
        <section>
          <h2 className="text-lg font-semibold">Search the vector database</h2>
          <p className="mt-1 text-sm text-muted">
            This is the agent's retrieval step on its own, with no language model writing anything. Your text becomes a
            vector, and Postgres finds the chunks nearest to it.
          </p>
          <form
            className="mt-3 flex flex-wrap gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              if (query.trim()) search.mutate()
            }}
          >
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              maxLength={500}
              aria-label="Search text"
              className="min-w-0 flex-1 basis-64 rounded border border-field bg-paper px-3 py-2 text-sm"
            />
            <label className="flex items-center gap-2 text-sm text-muted">
              Top
              <select
                value={k}
                onChange={(e) => setK(Number(e.target.value))}
                className="rounded border border-field bg-paper px-2 py-2 text-ink"
              >
                {[2, 4, 8, 12].map((n) => (
                  <option key={n}>{n}</option>
                ))}
              </select>
            </label>
            <button
              type="submit"
              disabled={search.isPending || !query.trim()}
              className="rounded bg-cobalt px-4 py-2 text-sm font-medium text-on-cobalt disabled:opacity-50"
            >
              {search.isPending ? 'Searching...' : 'Search'}
            </button>
          </form>
          {search.isError && <p className="mt-2 text-sm text-danger">{search.error.message}</p>}
        </section>

        {result && (
          <>
            <section>
              <h3 className="text-sm font-semibold">1. Your text as {result.embedding_dimensions} numbers</h3>
              <p className="mt-0.5 text-xs text-muted">
                The first 8 values, embedded in {result.embed_ms} ms. Meaning lives in the pattern across all of them,
                so no single number means anything alone.
              </p>
              <div className="mt-2 grid grid-cols-8 gap-1">
                {result.embedding_preview.map((value, i) => (
                  <div key={i} className="rounded bg-shelf p-1 text-center">
                    <div className="relative mx-auto h-10 w-2">
                      <span
                        className="absolute left-0 w-2 rounded-sm bg-rag"
                        style={{
                          height: `${(Math.abs(value) / maxAbs) * 50}%`,
                          ...(value >= 0 ? { bottom: '50%' } : { top: '50%' }),
                        }}
                      />
                    </div>
                    <span className="font-mono text-[10px] tabular-nums">{value.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </section>

            <section>
              <h3 className="text-sm font-semibold">2. The nearest chunks</h3>
              <p className="mt-0.5 text-xs text-muted">
                Score is cosine similarity: 1 means the same direction, near 0 means unrelated.
              </p>
              <ol className="mt-2 space-y-2">
                {result.passages.map((p) => (
                  <li key={`${p.source}-${p.chunk_index}`} className="rounded border border-rule bg-paper p-3">
                    <div className="flex items-center gap-3 text-xs">
                      <span className="font-mono">
                        {p.source} #{p.chunk_index}
                      </span>
                      <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-rule">
                        <span className="block h-full bg-rag" style={{ width: `${Math.max(0, p.score) * 100}%` }} />
                      </span>
                      <span className="font-mono tabular-nums">{p.score.toFixed(3)}</span>
                    </div>
                    <p className="mt-2 text-sm whitespace-pre-wrap">{p.text}</p>
                  </li>
                ))}
              </ol>
            </section>
          </>
        )}

        <section>
          <h2 className="text-lg font-semibold">What's stored</h2>
          <p className="mt-1 text-sm text-muted">
            {chunks.data?.length ?? 0} chunks from {bySource.length} documents, in the{' '}
            <code className="font-mono">policy_chunks</code> table.
          </p>
          <div className="mt-3 space-y-2">
            {bySource.map(([source, list]) => (
              <details key={source} className="rounded border border-rule bg-paper">
                <summary className="cursor-pointer px-3 py-2 font-mono text-sm">
                  {source} <span className="text-muted">({list.length})</span>
                </summary>
                <ol className="space-y-2 px-3 pb-3">
                  {list.map((chunk) => (
                    <li key={chunk.chunk_index} className="rounded bg-shelf p-2 text-xs whitespace-pre-wrap">
                      {chunk.text}
                    </li>
                  ))}
                </ol>
              </details>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
