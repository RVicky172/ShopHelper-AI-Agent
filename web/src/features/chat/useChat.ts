import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useReducer, useRef, useState } from 'react'
import { api } from '../../shared/api/client'
import { streamEvents } from '../../shared/api/sse'
import type { User } from '../../shared/api/types'
import { chatReducer, initialState } from './chatReducer'

const POLL_MS = 4000

// Per user, so one person's open conversation is never offered to the next. It's only an id:
// the server decides who may open it.
const storageKey = (user: User) => `shophelper.conversation.${user.id}`

function remember(user: User | null, id: string | null) {
  if (!user) return
  try {
    if (id) localStorage.setItem(storageKey(user), id)
    else localStorage.removeItem(storageKey(user))
  } catch {
    // storage blocked: the chat still works, it just won't reopen after a reload
  }
}

function recall(user: User | null): string | null {
  if (!user) return null
  try {
    return localStorage.getItem(storageKey(user))
  } catch {
    return null
  }
}

export function useChat(user: User | null) {
  const [state, dispatch] = useReducer(chatReducer, initialState)
  const [conversationId, setConversationId] = useState(() => recall(user))
  const queryClient = useQueryClient()
  const turnCounter = useRef(0)
  const createdHere = useRef<string | null>(null)

  // A conversation lives on the server, so opening one is always a fetch.
  useEffect(() => {
    if (!conversationId || createdHere.current === conversationId) return
    let current = true
    api
      .conversation(conversationId)
      .then((c) => {
        if (current) dispatch({ type: 'hydrate', rows: c.messages, pending: c.pending_refund })
      })
      .catch(() => {
        if (!current) return
        remember(user, null)
        setConversationId(null)
      })
    return () => {
      current = false
    }
  }, [conversationId, user])

  // While a refund waits for staff, check for the outcome so it appears without sending a message.
  const waiting = Boolean(state.pending) && !state.busy
  useEffect(() => {
    if (!conversationId || !waiting) return
    let current = true
    const timer = setInterval(() => {
      api
        .conversation(conversationId)
        .then((c) => {
          if (!current || c.pending_refund) return
          dispatch({ type: 'hydrate', rows: c.messages, pending: null })
          queryClient.invalidateQueries({ queryKey: ['orders'] })
          queryClient.invalidateQueries({ queryKey: ['conversations'] })
        })
        .catch(() => {}) // the next tick retries
    }, POLL_MS)
    return () => {
      current = false
      clearInterval(timer)
    }
  }, [conversationId, waiting, queryClient])

  const send = useCallback(
    async (message: string) => {
      const id = `turn-${(turnCounter.current += 1)}`
      dispatch({ type: 'start', id, label: message, at: performance.now(), userText: message })
      try {
        let session = conversationId
        if (!session) {
          session = (await api.createConversation()).id
          createdHere.current = session // don't reload what's being streamed right now
          remember(user, session)
          setConversationId(session)
        }
        await streamEvents('/api/chat/stream', { session_id: session, message }, (event) =>
          dispatch({ type: 'event', event, at: performance.now() }),
        )
      } catch (error) {
        const text = error instanceof Error ? error.message : 'The stream failed'
        dispatch({ type: 'failed', message: text, at: performance.now() })
        queryClient.invalidateQueries({ queryKey: ['me'] }) // the session may have ended
      } finally {
        dispatch({ type: 'done' })
        queryClient.invalidateQueries({ queryKey: ['conversations'] })
        queryClient.invalidateQueries({ queryKey: ['refunds'] })
      }
    },
    [conversationId, queryClient, user],
  )

  const open = useCallback(
    (id: string) => {
      if (id === conversationId) return
      createdHere.current = null
      dispatch({ type: 'reset' })
      remember(user, id)
      setConversationId(id)
    },
    [conversationId, user],
  )

  const newConversation = useCallback(() => {
    createdHere.current = null
    dispatch({ type: 'reset' })
    remember(user, null)
    setConversationId(null)
  }, [user])

  return { ...state, conversationId, send, open, newConversation }
}
