import { createParser } from 'eventsource-parser'
import type { StreamEvent } from './types'

// The browser's built-in EventSource can only send GET requests, and /chat/stream is a POST
// with a JSON body. So: fetch() for the request, eventsource-parser for the SSE format.
export async function streamEvents(
  path: string,
  body: unknown,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
  if (!response.ok || !response.body) {
    throw new Error(`Request failed: ${response.status}`)
  }

  const parser = createParser({
    onEvent: ({ event, data }) => onEvent({ event, data: JSON.parse(data) } as StreamEvent),
  })

  // Network chunks don't line up with events: one read can hold half an event or three.
  // The parser buffers until a complete event has arrived.
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader()
  for (;;) {
    const { done, value } = await reader.read()
    if (done) return
    parser.feed(value)
  }
}
