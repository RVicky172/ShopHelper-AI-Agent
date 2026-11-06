import type {
  ChatResponse,
  GuardrailData,
  HistoryRow,
  ModelStepData,
  PendingRefund,
  StreamEvent,
  ToolEndData,
  ToolStartData,
} from '../../shared/api/types'

// Every stream event goes through this one pure function. The UI only renders the state,
// so a whole conversation can be replayed in a test with no server and no browser.

export interface Message {
  id: string
  role: 'user' | 'assistant'
  text: string
  streaming?: boolean
  result?: ChatResponse
  error?: string
}

export type TraceItem =
  | { kind: 'guardrail'; at: number; data: GuardrailData }
  | { kind: 'model'; at: number; data: ModelStepData }
  | { kind: 'tool'; at: number; start: ToolStartData; end?: ToolEndData }
  | { kind: 'answer'; at: number; tokens: number; step?: ModelStepData }
  | { kind: 'interrupt'; at: number; data: PendingRefund }
  | { kind: 'final'; at: number; data: ChatResponse }
  | { kind: 'error'; at: number; message: string }

export interface Turn {
  id: string
  label: string
  startedAt: number
  items: TraceItem[]
}

export interface ChatState {
  messages: Message[]
  turns: Turn[]
  busy: boolean
  pending: PendingRefund | null // a refund in this conversation is waiting for staff
}

export const initialState: ChatState = { messages: [], turns: [], busy: false, pending: null }

export type Action =
  | { type: 'hydrate'; rows: HistoryRow[]; pending: PendingRefund | null }
  | { type: 'start'; id: string; label: string; at: number; userText?: string }
  | { type: 'event'; event: StreamEvent; at: number }
  | { type: 'failed'; message: string; at: number }
  | { type: 'done' }
  | { type: 'reset' }

function updateLast<T>(list: T[], update: (item: T) => T): T[] {
  return list.length ? [...list.slice(0, -1), update(list[list.length - 1])] : list
}

function applyToTrace(items: TraceItem[], event: StreamEvent, at: number): TraceItem[] {
  switch (event.event) {
    case 'guardrail':
      return [...items, { kind: 'guardrail', at, data: event.data }]
    case 'model_step': {
      // The model's last step is the answer it just streamed: fold it into that row.
      const last = items[items.length - 1]
      if (last?.kind === 'answer' && event.data.tool_calls.length === 0) {
        return [...items.slice(0, -1), { ...last, step: event.data }]
      }
      // It wrote some text and then asked for a tool: that was a preamble, not the answer.
      const kept = last?.kind === 'answer' ? items.slice(0, -1) : items
      return [...kept, { kind: 'model', at, data: event.data }]
    }
    case 'tool_start':
      return [...items, { kind: 'tool', at, start: event.data }]
    case 'tool_end': {
      const started = items.some((item) => item.kind === 'tool' && item.start.id === event.data.id)
      if (!started) {
        // Resuming after approval: this tool started in the previous turn, before the pause.
        const { id, name } = event.data
        return [...items, { kind: 'tool', at, start: { id, name, args: {} }, end: event.data }]
      }
      return items.map((item) =>
        item.kind === 'tool' && item.start.id === event.data.id ? { ...item, end: event.data } : item,
      )
    }
    case 'token': {
      const last = items[items.length - 1]
      if (last?.kind === 'answer') return [...items.slice(0, -1), { ...last, tokens: last.tokens + 1 }]
      return [...items, { kind: 'answer', at, tokens: 1 }]
    }
    case 'interrupt':
      return [...items, { kind: 'interrupt', at, data: event.data }]
    case 'final':
      return [...items, { kind: 'final', at, data: event.data }]
    case 'error':
      return [...items, { kind: 'error', at, message: event.data }]
  }
}

function applyToMessage(message: Message, event: StreamEvent): Message {
  switch (event.event) {
    case 'token':
      return { ...message, text: message.text + event.data }
    case 'model_step':
      // Some models say "Let me check" before calling a tool. Drop it so it doesn't run
      // into the real answer, which comes after the tool result.
      return event.data.tool_calls.length > 0 ? { ...message, text: '' } : message
    case 'final':
      // Authoritative text: the output guardrail may have changed what was streamed.
      return { ...message, text: event.data.answer, result: event.data, streaming: false }
    case 'error':
      return { ...message, error: event.data, streaming: false }
    default:
      return message
  }
}

export function chatReducer(state: ChatState, action: Action): ChatState {
  switch (action.type) {
    case 'hydrate':
      return {
        ...state,
        pending: action.pending,
        messages: action.rows.map((row, i) => ({ id: `history-${i}`, role: row.role, text: row.text })),
      }
    case 'start': {
      const user: Message[] = action.userText ? [{ id: `${action.id}-user`, role: 'user', text: action.userText }] : []
      return {
        ...state,
        busy: true,
        messages: [
          ...state.messages,
          ...user,
          { id: `${action.id}-assistant`, role: 'assistant', text: '', streaming: true },
        ],
        turns: [...state.turns, { id: action.id, label: action.label, startedAt: action.at, items: [] }],
      }
    }
    case 'event':
      return {
        ...state,
        pending: action.event.event === 'final' ? action.event.data.pending_refund : state.pending,
        messages: updateLast(state.messages, (m) => applyToMessage(m, action.event)),
        turns: updateLast(state.turns, (t) => ({
          ...t,
          items: applyToTrace(t.items, action.event, action.at - t.startedAt),
        })),
      }
    case 'failed':
      return chatReducer(state, {
        type: 'event',
        event: { event: 'error', data: action.message },
        at: action.at,
      })
    case 'done':
      return {
        ...state,
        busy: false,
        messages: updateLast(state.messages, (m) => ({ ...m, streaming: false })),
      }
    case 'reset':
      return initialState
  }
}
