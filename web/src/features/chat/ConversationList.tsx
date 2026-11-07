import { useQuery } from '@tanstack/react-query'
import { api } from '../../shared/api/client'
import type { useChat } from './useChat'

const NEW_CHAT = 'New conversation'

export function ConversationList({ chat }: { chat: ReturnType<typeof useChat> }) {
  const conversations = useQuery({ queryKey: ['conversations'], queryFn: api.conversations })
  const rows = (conversations.data ?? []).filter((c) => c.title)

  return (
    <>
      {/* Phones get a compact picker in place of the sidebar. */}
      <select
        aria-label="Conversation"
        className="border-b border-field bg-paper px-3 py-2 text-sm lg:hidden"
        disabled={chat.busy}
        value={chat.conversationId ?? ''}
        onChange={(e) => (e.target.value ? chat.open(e.target.value) : chat.newConversation())}
      >
        <option value="">{NEW_CHAT}</option>
        {rows.map((c) => (
          <option key={c.id} value={c.id}>
            {c.title}
          </option>
        ))}
      </select>

      <nav aria-label="Your conversations" className="hidden min-h-0 flex-col border-r border-rule lg:flex">
        <div className="p-3">
          <button
            type="button"
            disabled={chat.busy}
            onClick={chat.newConversation}
            className="w-full rounded-xl border border-rule bg-paper px-3 py-1.5 text-sm hover:border-cobalt disabled:opacity-50"
          >
            {NEW_CHAT}
          </button>
        </div>
        <ul className="min-h-0 flex-1 space-y-0.5 overflow-y-auto px-2 pb-3">
          {rows.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                disabled={chat.busy}
                onClick={() => chat.open(c.id)}
                aria-current={c.id === chat.conversationId ? 'true' : undefined}
                className={`w-full truncate rounded px-2.5 py-1.5 text-left text-sm disabled:opacity-50 ${
                  c.id === chat.conversationId ? 'bg-shelf font-medium' : 'text-muted hover:text-ink'
                }`}
              >
                {c.title}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </>
  )
}
