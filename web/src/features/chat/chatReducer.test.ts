import { describe, expect, it } from 'vitest'
import type { ChatResponse, StreamEvent } from '../../shared/api/types'
import { type ChatState, chatReducer, initialState } from './chatReducer'

const final = (over: Partial<ChatResponse> = {}): ChatResponse => ({
  session_id: 's',
  status: 'answered',
  answer: 'Final text',
  tools_used: [],
  citations: [],
  pending_refund: null,
  input_tokens: 0,
  output_tokens: 0,
  latency_ms: 0,
  guardrail_action: 'passed',
  guardrail_reasons: [],
  ...over,
})

function replay(events: StreamEvent[]): ChatState {
  const started = chatReducer(initialState, {
    type: 'start',
    id: 't1',
    label: 'q',
    at: 1000,
    userText: 'q',
  })
  return events.reduce((s, event, i) => chatReducer(s, { type: 'event', event, at: 1000 + i }), started)
}

describe('chatReducer', () => {
  it('appends tokens as they stream', () => {
    const state = replay([
      { event: 'token', data: 'Hel' },
      { event: 'token', data: 'lo' },
    ])
    expect(state.messages.at(-1)?.text).toBe('Hello')
    expect(state.messages.at(-1)?.streaming).toBe(true)
    expect(state.turns[0].items).toMatchObject([{ kind: 'answer', tokens: 2 }])
  })

  it('lets the final event replace streamed text', () => {
    const state = replay([
      { event: 'token', data: 'my email is a@b.com' },
      { event: 'final', data: final({ answer: 'my email is {EMAIL}' }) },
    ])
    expect(state.messages.at(-1)?.text).toBe('my email is {EMAIL}')
    expect(state.messages.at(-1)?.streaming).toBe(false)
  })

  it('pairs tool_end with its tool_start by id', () => {
    const state = replay([
      { event: 'tool_start', data: { id: 'a', name: 'get_order_status', args: {} } },
      { event: 'tool_start', data: { id: 'b', name: 'search_policy', args: {} } },
      { event: 'tool_end', data: { id: 'b', name: 'search_policy', status: 'success', result: 1, ms: 5 } },
    ])
    const [first, second] = state.turns[0].items
    expect(first).toMatchObject({ kind: 'tool', start: { id: 'a' } })
    expect(first).not.toHaveProperty('end')
    expect(second).toMatchObject({ kind: 'tool', end: { result: 1 } })
  })

  it('shows a tool that finishes in a later turn than it started', () => {
    const end = { id: 'r', name: 'request_refund', status: 'success' as const, result: 'APPROVED', ms: 5 }
    const state = replay([{ event: 'tool_end', data: end }])
    expect(state.turns[0].items).toMatchObject([{ kind: 'tool', start: { id: 'r' }, end }])
  })

  it('folds the last model step into the streamed answer', () => {
    const step = { step: 2, tool_calls: [], input_tokens: 9, output_tokens: 3, ms: 40 }
    const state = replay([
      { event: 'token', data: 'x' },
      { event: 'model_step', data: step },
    ])
    expect(state.turns[0].items).toMatchObject([{ kind: 'answer', step }])
  })

  it('keeps a model step that asked for tools as its own row', () => {
    const step = { step: 1, tool_calls: ['search_policy'], input_tokens: 9, output_tokens: 3, ms: 40 }
    const state = replay([{ event: 'model_step', data: step }])
    expect(state.turns[0].items).toMatchObject([{ kind: 'model' }])
  })

  it('drops text written before a tool call', () => {
    const step = { step: 1, tool_calls: ['search_policy'], input_tokens: 9, output_tokens: 3, ms: 40 }
    const state = replay([
      { event: 'token', data: 'Let me check.' },
      { event: 'model_step', data: step },
      { event: 'token', data: 'The fee is 10%.' },
    ])
    expect(state.messages.at(-1)?.text).toBe('The fee is 10%.')
    expect(state.turns[0].items.map((item) => item.kind)).toEqual(['model', 'answer'])
  })

  it('records times relative to the start of the turn', () => {
    const state = replay([{ event: 'token', data: 'a' }])
    expect(state.turns[0].items[0].at).toBe(0)
  })

  const refund = {
    order_id: '1001',
    item: 'Wireless Mouse',
    order_total: 59.99,
    amount: 59.99,
    reason: 'damaged',
    needs_supervisor: false,
  }

  it('remembers a refund that is waiting for review', () => {
    const state = replay([
      { event: 'interrupt', data: refund },
      { event: 'final', data: final({ status: 'pending_approval', pending_refund: refund }) },
    ])
    expect(state.pending).toEqual(refund)
  })

  it('loads a reopened conversation with its pending refund', () => {
    const rows = [
      { role: 'user' as const, text: 'refund please' },
      { role: 'assistant' as const, text: 'Submitted.' },
    ]
    const state = chatReducer(initialState, { type: 'hydrate', rows, pending: refund })
    expect(state.messages.map((m) => m.text)).toEqual(['refund please', 'Submitted.'])
    expect(state.pending).toEqual(refund)
  })

  it('clears the pending refund when a refresh shows it was decided', () => {
    const waiting = chatReducer(initialState, { type: 'hydrate', rows: [], pending: refund })
    const rows = [{ role: 'assistant' as const, text: 'Your refund was approved.' }]
    const state = chatReducer(waiting, { type: 'hydrate', rows, pending: null })
    expect(state.pending).toBeNull()
    expect(state.messages.at(-1)?.text).toBe('Your refund was approved.')
  })

  it('keeps nothing after a reset', () => {
    const used = replay([
      { event: 'token', data: 'private text' },
      { event: 'final', data: final({ status: 'pending_approval', pending_refund: refund }) },
    ])
    expect(chatReducer(used, { type: 'reset' })).toEqual(initialState)
  })

  it('shows a failed request on the assistant message and stops being busy', () => {
    const started = replay([])
    const failed = chatReducer(started, { type: 'failed', message: 'offline', at: 1500 })
    const done = chatReducer(failed, { type: 'done' })
    expect(done.messages.at(-1)).toMatchObject({ error: 'offline', streaming: false })
    expect(done.busy).toBe(false)
  })
})
