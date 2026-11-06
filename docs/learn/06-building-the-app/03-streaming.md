---
title: Streaming
checked: 2026-11-06
---

## What you'll learn

- Why streaming changes how fast an app feels
- How to choose between polling, SSE and WebSockets
- What travels over the wire, and how it's built
- What streaming does to safety, and what breaks it

## The simple explanation

Think of a slow restaurant. If nothing happens for ten minutes, you start to worry. If a waiter brings bread and says the food is coming, the same wait feels fine.

Streaming sends each piece of a response as soon as it exists. The total time doesn't change, but the *felt* wait does, because something is always happening. For an agent there's a second benefit: people see each step, so the wait makes sense.

There are three ways to get data from server to browser:

| Option | Direction | Good for | Here |
| --- | --- | --- | --- |
| Polling | Client asks repeatedly | Slow changes | Only for refund outcomes |
| **Server-Sent Events** | Server to client | Streaming a response | **Chosen for chat** |
| WebSockets | Both ways | Chat between people, games | More than we need |

The traffic here is one-way: the client sends one request, then only receives. That's what **SSE** does. It's plain HTTP, so proxies and browser tools understand it, and most LLM APIs stream this way too.

SSE is a text format. Each event is a couple of lines, ended by a blank line:

```text
event: tool_start
data: {"id": "call_1", "name": "search_policy", "args": {"query": "restocking fee"}}

event: token
data: "There"

event: final
data: {"status": "answered", "answer": "There is a 10% restocking fee."}
```

## An example

We timed one real question through this API, "How long do refunds take?":

| Moment | Time |
| --- | --- |
| First event, the input guardrail | 2.07 s |
| First text token | 2.33 s |
| `search_policy` starts | 3.20 s |
| `search_policy` ends | 3.24 s |
| Finished, after 60 token events | 4.86 s |

Without streaming, the screen stays still for 4.86 seconds. With it, something moves after about 2. That's one run on one local machine, and a second question came out about the same, at 5.2 seconds. It's the shape that matters: **the search took 0.04 seconds, and nearly all the rest was the model.**

Notice the tokens that came before the tool. The model wrote "I'll check the refund policy for you" first, then called it. The screen clears that text when the tool call arrives, so it doesn't run into the real answer.

## How ShopHelper does it

Every step of a turn is one event type:

| Event | Sent when |
| --- | --- |
| `guardrail` | Input or output has been checked |
| `model_step` | A model call finished, or [code chose a tool itself](../03-agents/02-the-agent-loop.md) |
| `tool_start`, `tool_end` | A tool ran |
| `token` | The model wrote more of its answer |
| `interrupt` | The graph paused for approval |
| `final` | The turn is over, with the complete response |
| `error` | Something failed |

Clients can ignore events they don't recognise, so adding one doesn't break an older client.

The path has four layers, each passing events up:

```mermaid
flowchart LR
    m["LM Studio<br/>SSE tokens"] --> g["LangGraph<br/>astream()"]
    g --> s["service.py<br/>makes events"]
    s --> a["app.py<br/>formats as SSE"]
    a --> v["Vite proxy"]
    v --> b["Browser"]
```

LangGraph gives two views of the same run at once. `messages` is model output as it's generated, and `updates` is each node's result:

```python file=src/shophelper/agent/service.py
async for mode, payload in self.graph.astream(
graph_input, config, stream_mode=["messages", "updates"]
```

The API turns each pair into SSE text. It's an async generator, so each `yield` goes out immediately:

```python file=src/shophelper/api/app.py
yield f"event: {kind}\ndata: {json.dumps(payload)}\n\n"
```

`json.dumps` matters. A token can contain a newline, which would otherwise break the line-based format.

The login check is plain ASGI middleware for the same reason. Some middleware styles hold a response until it's complete, which would quietly undo all of this:

```python file=src/shophelper/api/auth_routes.py
"""Plain ASGI middleware, so it doesn't buffer streamed responses."""
```

**Streaming and safety.** Here's the real cost. Tokens reach the user before the output guardrail has seen the full answer, because it needs the complete text. So the `final` event carries the approved text, and the client replaces what it showed. Unsafe text could appear briefly. That's a trade-off, and it's why `/chat`, which doesn't stream, still exists. Other options are checking sentence by sentence, or not streaming.

## In the market

Checked on 2026-11-06.

Some limits worth knowing, from [MDN](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events):

- Over HTTP/1, a browser allows only 6 open SSE connections per domain, across all tabs. HTTP/2 raises that, with a default of 100 streams.
- The browser's `EventSource` reconnects by itself. But it only sends GET, with no body, so POST endpoints like this one use `fetch`.

Things between you and the client may hold your data until the response ends:

| Where | What happens | Fix |
| --- | --- | --- |
| API Gateway with Lambda | Everything arrives at once | Use a load balancer, or Lambda response streaming |
| nginx | Buffers by default | `proxy_buffering off` |
| Compression | Waits to fill blocks | Turn it off for `text/event-stream` |

If your stream arrives all at once, look for the buffer in the middle, and test each hop with `curl -N`.

## Try it

1. See it raw. curl keeps the session in a cookie file, and a conversation has to exist first:

```bash
curl -c jar.txt http://localhost:8000/auth/login -H 'content-type: application/json' \
  -d '{"email":"ravi@demo.shophelper.test","password":"shophelper-demo"}'

curl -b jar.txt -X POST http://localhost:8000/conversations   # copy the id it returns

curl -N -b jar.txt http://localhost:8000/chat/stream -H 'content-type: application/json' \
  -d '{"session_id":"PASTE-THE-ID","message":"Where is order 1002?"}'
```

2. `-N` turns off curl's buffering. Run the last command without it, and compare. Delete `jar.txt` afterwards, since it's a live session.
3. In the shop, open browser dev tools, then **Network**. Send a chat message, and click the `stream` request to see the events.
4. On **How it works**, find the gap between the last tool finishing and the first token. That's the model reading its prompt.

## Interview questions

### Why SSE rather than WebSockets for an LLM response?

**Strong answer:** The traffic is one-way after the request, which is what SSE is for. It's plain HTTP, so load balancers, proxies and auth work as normal. WebSockets need more machinery, like connection state and their own reconnect logic. I'd choose them if the client had to send during a turn, like interrupting a voice call. I built mine on `fetch`, since `EventSource` can only do GET.

**Follow-up:** How would you handle a dropped connection mid-answer?

### How does streaming affect guardrails?

**Strong answer:** Output checks often need the full text, but tokens are already on screen. In my project the final event carries the checked answer, and the client replaces what it showed, so unsafe text can flash briefly. A non-streaming route exists for when that isn't acceptable. Other options are checking per sentence, or holding back the first part. It's a trade-off between speed and safety, so it depends on the harm.

**Follow-up:** Which would you choose for a medical bot?

### A stream works locally, but arrives all at once in production. What do you check?

**Strong answer:** Something in the middle is buffering. I'd test each hop with `curl -N`: the app directly, then the load balancer, then the CDN. Common causes are nginx buffering, compression, or API Gateway with Lambda. My own AWS plan notes that API Gateway buffers, so streaming goes through the load balancer. I'd also check for middleware in the app that reads the whole response.

**Follow-up:** How would you keep this from regressing?

## Check yourself

### What does streaming change?

- [ ] The total time — that stays the same.
- [x] How long it feels — right: something is always happening.
- [ ] The cost — the same tokens are generated.

### Why not use the browser's `EventSource` here?

- [x] It can only send GET, and this endpoint is a POST — right: so `fetch` reads the stream.
- [ ] It doesn't support text — SSE is text.
- [ ] It's been removed from browsers — it's still there.

### Why does the `final` event carry the whole answer?

- [ ] The tokens might get lost — that isn't the main reason.
- [ ] To make the response bigger — size isn't a goal.
- [x] The output guardrail may have changed it — right: the client replaces what it showed.
