import { useQuery } from '@tanstack/react-query'
import { Navigate, NavLink, Route, Routes } from 'react-router'
import { api } from '../../shared/api/client'
import type { ServiceCheck, User } from '../../shared/api/types'
import { NotFound } from '../../shared/layout/NotFound'
import { ChatView } from './ChatView'
import { RagView } from './RagView'
import { ToolsView } from './ToolsView'

// Absolute: inside a `*` route, a relative link resolves against the whole URL, not the parent.
const SECTIONS = [
  { to: '/how-it-works/trace', label: 'Step trace' },
  { to: '/how-it-works/rag', label: 'RAG explorer' },
  { to: '/how-it-works/tools', label: 'Tools' },
]

function Status({ label, check }: { label: string; check?: ServiceCheck }) {
  const color = !check ? 'var(--color-muted)' : check.ok ? 'var(--color-guard)' : 'var(--color-danger)'
  return (
    <span className="flex items-center gap-1.5 text-sm text-muted" title={check?.detail}>
      <span className="size-2 rounded-full" style={{ background: color }} />
      {label}
    </span>
  )
}

// The learning tools. Loaded on its own, so shoppers don't download them with the landing page.
export function HowItWorks({ user }: { user: User }) {
  const system = useQuery({ queryKey: ['system'], queryFn: api.system, refetchInterval: 10_000 })
  const services = system.data?.services

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <title>How it works · ShopHelper</title>
      <h1 className="sr-only">How it works</h1>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 border-b border-rule bg-shelf px-4 py-1">
        <nav aria-label="How it works" className="flex flex-wrap gap-x-5">
          {SECTIONS.map((section) => (
            <NavLink
              key={section.to}
              to={section.to}
              className={({ isActive }) =>
                `flex min-h-10 items-center text-sm ${isActive ? 'font-medium text-cobalt' : 'hover:text-cobalt'}`
              }
            >
              {section.label}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto flex flex-wrap items-center gap-x-4">
          <Status label="LM Studio" check={services?.llm} />
          <Status label="Postgres" check={services?.database} />
          <a
            href="http://localhost:5050"
            target="_blank"
            rel="noreferrer"
            className="flex min-h-6 items-center text-sm text-muted underline hover:text-ink"
          >
            pgAdmin
          </a>
        </div>
      </div>

      {services?.llm.ok === false && (
        <p role="alert" className="border-b border-danger/40 bg-danger/10 px-4 py-2 text-sm">
          LM Studio is not responding. Start its server with `lms server start`.
        </p>
      )}

      <Routes>
        <Route index element={<Navigate to="/how-it-works/trace" replace />} />
        <Route path="trace" element={<ChatView user={user} />} />
        <Route path="rag" element={<RagView />} />
        <Route path="tools" element={<ToolsView system={system.data} />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  )
}
