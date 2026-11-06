import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useMatch } from 'react-router'
import { api } from '../../shared/api/client'
import type { User } from '../../shared/api/types'
import { signInPath } from '../auth/next'
import { useSharedChat } from './ChatProvider'
import { MessageBubble } from './MessageBubble'
import { startersFor } from './starters'

const DESKTOP = '(min-width: 1280px)'

function usePageStarters(user: User) {
  const { pathname } = useLocation()
  const slug = useMatch('/products/:slug')?.params.slug
  const onOrders = pathname.endsWith('/orders')

  const product = useQuery({
    queryKey: ['product', slug],
    queryFn: () => api.product(slug ?? ''),
    enabled: Boolean(slug),
  })
  const categories = useQuery({
    queryKey: ['categories'],
    queryFn: api.categories,
    staleTime: Infinity,
    enabled: Boolean(slug),
  })
  const orders = useQuery({ queryKey: ['orders'], queryFn: api.orders, enabled: onOrders && user.role === 'customer' })

  const category = categories.data?.find((c) => c.slug === product.data?.category)?.name
  return startersFor({
    pathname,
    product: product.data && category ? { name: product.data.name, category } : undefined,
    latestOrderId: orders.data?.at(-1)?.order_id,
  })
}

function Conversations() {
  const chat = useSharedChat()
  const conversations = useQuery({ queryKey: ['conversations'], queryFn: api.conversations })
  const rows = (conversations.data ?? []).filter((c) => c.title)
  return (
    <select
      aria-label="Conversation"
      disabled={chat.busy}
      value={chat.conversationId ?? ''}
      onChange={(event) => (event.target.value ? chat.open(event.target.value) : chat.newConversation())}
      className="min-h-11 w-full border-b border-rule bg-paper px-4 text-sm"
    >
      <option value="">New conversation</option>
      {rows.map((c) => (
        <option key={c.id} value={c.id}>
          {c.title}
        </option>
      ))}
    </select>
  )
}

function Conversation({ user }: { user: User }) {
  const chat = useSharedChat()
  const starters = usePageStarters(user)
  const [draft, setDraft] = useState('')
  const input = useRef<HTMLTextAreaElement>(null)
  const bottom = useRef<HTMLDivElement>(null)

  useEffect(() => {
    input.current?.focus()
  }, [])
  useEffect(() => {
    bottom.current?.scrollIntoView({ block: 'end' })
  }, [chat.messages, chat.pending])

  const submit = () => {
    const text = draft.trim()
    if (!text || chat.busy) return
    setDraft('')
    void chat.send(text)
  }
  const traced = new Set(chat.turns.map((turn) => turn.id))

  return (
    <>
      <Conversations />
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
        {chat.messages.length === 0 && (
          <div>
            <p className="text-xl font-semibold">Hi {user.display_name}</p>
            <p className="mt-1 text-muted">Ask about an order or one of our policies.</p>
            <ul className="mt-4 space-y-2">
              {starters.map((starter) => (
                <li key={starter}>
                  <button
                    type="button"
                    disabled={chat.busy}
                    onClick={() => void chat.send(starter)}
                    className="min-h-11 w-full rounded border border-rule px-3 py-2 text-left hover:border-cobalt"
                  >
                    {starter}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
        {chat.messages.map((message) => {
          const turn = message.id.replace(/-assistant$/, '')
          return (
            <div key={message.id}>
              <MessageBubble message={message} plain />
              {message.role === 'assistant' && message.result && traced.has(turn) && (
                <Link
                  to={`/how-it-works/trace?turn=${turn}`}
                  onClick={() => {
                    if (!window.matchMedia(DESKTOP).matches) chat.closePanel() // it would cover the trace
                  }}
                  className="mt-1 inline-block text-sm text-cobalt underline"
                >
                  See how this was answered
                </Link>
              )}
            </div>
          )
        })}
        {chat.pending && !chat.busy && (
          <div role="status" className="border-l-4 border-warn bg-shelf p-3 text-sm">
            <p className="font-semibold">Waiting for review</p>
            <p className="mt-0.5 text-muted">
              ${chat.pending.amount.toFixed(2)} for order {chat.pending.order_id}. A support agent will decide, and the
              outcome appears here by itself.
            </p>
          </div>
        )}
        <div ref={bottom} />
      </div>
      <form
        className="flex items-end gap-2 border-t border-rule p-3"
        onSubmit={(event) => {
          event.preventDefault()
          submit()
        }}
      >
        <textarea
          ref={input}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              submit()
            }
          }}
          rows={1}
          maxLength={2000}
          aria-label="Message to support"
          placeholder="Ask about an order or policy"
          className="min-h-11 flex-1 resize-none rounded border border-field bg-paper px-3 py-2"
        />
        <button
          type="submit"
          disabled={chat.busy || !draft.trim()}
          className="min-h-11 rounded bg-cobalt px-4 font-medium text-on-cobalt disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </>
  )
}

function SignInFirst() {
  const location = useLocation()
  const link = useRef<HTMLAnchorElement>(null)
  useEffect(() => {
    link.current?.focus()
  }, [])
  const to = signInPath(location)
  return (
    <div className="p-4">
      <p className="text-xl font-semibold">Sign in to chat with support</p>
      <p className="mt-1 text-muted">Support can see your orders, so we need to know it's you.</p>
      <Link
        ref={link}
        to={to}
        className="mt-4 flex min-h-11 items-center justify-center rounded bg-cobalt px-4 font-medium text-on-cobalt hover:underline"
      >
        Sign in
      </Link>
      <Link to={to.replace('/signin', '/signup')} className="mt-3 inline-block text-cobalt underline">
        Create an account
      </Link>
    </div>
  )
}

export function ChatPanel({ user }: { user: User | null }) {
  const { panelOpen, closePanel } = useSharedChat()
  const inCheckout = useMatch('/checkout') !== null
  const show = panelOpen && !inCheckout

  useEffect(() => {
    if (!show) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') closePanel()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [show, closePanel])

  if (!show) return null

  return (
    <section
      role="dialog"
      aria-label="Support chat"
      className="chat-panel fixed inset-0 z-40 flex flex-col bg-paper xl:inset-auto xl:right-5 xl:bottom-5 xl:h-[min(640px,calc(100dvh-7rem))] xl:w-[400px] xl:border xl:border-rule xl:shadow-xl"
    >
      <div className="flex items-center justify-between border-b border-rule py-1 pr-1 pl-4">
        <h2 className="font-semibold">Support</h2>
        <button
          type="button"
          onClick={closePanel}
          aria-label="Close chat"
          className="size-11 text-xl text-muted hover:text-ink"
        >
          ×
        </button>
      </div>
      {user ? <Conversation user={user} /> : <SignInFirst />}
    </section>
  )
}
