import { createContext, type ReactNode, type RefObject, useContext, useMemo, useRef, useState } from 'react'
import type { User } from '../../shared/api/types'
import { useChat } from './useChat'

interface SharedChat extends ReturnType<typeof useChat> {
  panelOpen: boolean
  openPanel: () => void
  closePanel: () => void
  ask: (question: string) => void
  launcher: RefObject<HTMLButtonElement | null>
}

const ChatContext = createContext<SharedChat | null>(null)

// Sits above the pages, so moving between them can't interrupt a stream or lose a conversation.
// Give it a key from the user: that rebuilds it when the user changes, so no chat carries over.
export function ChatProvider({ user, children }: { user: User | null; children: ReactNode }) {
  const chat = useChat(user)
  const [panelOpen, setPanelOpen] = useState(false)
  const launcher = useRef<HTMLButtonElement>(null)

  const value = useMemo<SharedChat>(
    () => ({
      ...chat,
      panelOpen,
      launcher,
      openPanel: () => setPanelOpen(true),
      closePanel: () => {
        setPanelOpen(false)
        launcher.current?.focus()
      },
      ask: (question) => {
        setPanelOpen(true)
        if (user && !chat.busy) void chat.send(question)
      },
    }),
    [chat, panelOpen, user],
  )

  return <ChatContext value={value}>{children}</ChatContext>
}

export function useSharedChat(): SharedChat {
  const chat = useContext(ChatContext)
  if (!chat) throw new Error('useSharedChat needs a ChatProvider above it')
  return chat
}
