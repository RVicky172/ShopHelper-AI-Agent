import type { SystemInfo } from '../../shared/api/types'

export function ToolsView({ system }: { system?: SystemInfo }) {
  if (!system) return <p className="p-6 text-sm text-muted">Waiting for the API...</p>

  const wiring = [
    ['Chat model', system.chat_model],
    ['Embedding model', system.embedding_model],
    ['Model server', system.llm_base_url],
    ['Tool transport', system.mcp_url ? `${system.tools_transport} at ${system.mcp_url}` : system.tools_transport],
    ['Guardrails', system.guardrails],
    ['Max model calls per turn', String(system.max_steps)],
  ]

  return (
    <div className="min-h-0 flex-1 overflow-y-auto">
      <div className="mx-auto w-full max-w-page space-y-8 px-gutter py-8">
        <section>
          <h2 className="text-lg font-semibold">Tools the model can ask for</h2>
          <p className="mt-1 text-sm text-muted">
            The model only sees each name, description and argument list. That text is how it decides what to call, so
            it matters as much as the code behind it.
          </p>
          <ul className="mt-3 space-y-2">
            {system.tools.map((tool) => (
              <li key={tool.name} className="surface-solid p-3">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="font-mono text-sm font-medium">{tool.name}</span>
                  <span className="rounded bg-shelf px-1.5 py-0.5 text-xs text-muted">via {tool.via}</span>
                </div>
                <p className="mt-1 text-sm text-muted">{tool.description}</p>
                <p className="mt-2 font-mono text-xs">
                  {Object.entries(tool.args)
                    .map(([name, schema]) => `${name}: ${schema.type ?? 'any'}`)
                    .join(', ')}
                </p>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold">How this instance is wired</h2>
          <dl className="mt-3 surface-solid divide-y divide-edge text-sm">
            {wiring.map(([label, value]) => (
              <div key={label} className="flex flex-wrap justify-between gap-x-4 px-3 py-2">
                <dt className="text-muted">{label}</dt>
                <dd className="font-mono text-xs break-all">{value}</dd>
              </div>
            ))}
          </dl>
        </section>
      </div>
    </div>
  )
}
