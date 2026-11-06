---
title: Transports and the current spec
checked: 2026-11-06
---

## What you'll learn

- How MCP messages travel
- What changed in the July 2026 spec, and why
- Where this project stands against it, as measured
- How old and new versions work together

## The simple explanation

MCP messages need a way to travel. That's the **transport**:

| | stdio | Streamable HTTP |
| --- | --- | --- |
| How | The client starts the server as a child process, and they talk over stdin and stdout | The server runs by itself, and clients connect over HTTP |
| Good for | Local tools, one client | Shared servers, many clients |
| Startup | A few seconds per process | None: it's already running |
| Used here | ECS on AWS | Local Docker |
| Gotcha | Never `print()` in the server: stdout *is* the protocol | Needs a port, and real auth in production |

MCP is also a young standard, and it changes. Each revision is named by date. The current one is **2026-07-28**, and it made the biggest change so far.

Older versions worked like a phone call. You dial first (`initialize`), agree the terms, get a session id, and every message after that belongs to the call. If the server forgets the call, you start again.

The new spec works like posting letters. Each request carries everything needed: its version, who's sending and what they support. Any server can answer any request.

Why? Scale. With sessions, a client has to keep reaching the same server, or servers have to share storage. Without them, a load balancer can send each request anywhere.

## An example

The main changes in [the 2026-07-28 spec](https://blog.modelcontextprotocol.io/posts/2026-07-28/):

| Area | Before | Now |
| --- | --- | --- |
| Starting | `initialize` handshake | None: each request carries its version in `_meta` |
| Sessions | `Mcp-Session-Id` header | Removed |
| Finding out about a server | From `initialize` | `server/discover` |
| Routing | Parse the JSON body | `Mcp-Method` and `Mcp-Name` headers |
| Version mismatch | Agreed at the handshake | `UnsupportedProtocolVersionError`, listing what's supported |
| Client registration | Dynamic Client Registration | Client ID Metadata Documents preferred |
| The old HTTP+SSE transport | Allowed | Deprecated |

If a server needs state now, it creates its own handle, such as a cart id, and passes it back as a normal tool argument.

## How ShopHelper does it

Locally the server runs on its own, and the client connects over HTTP:

```python file=src/shophelper/mcp/client.py
{"shophelper": {"transport": "streamable_http", "url": url}}, tool_interceptors=[add_identity]
```

**This project is one version behind.** Here's what we measured against the running server, using `mcp` 1.30.0:

| Test | Result |
| --- | --- |
| Newest version the library knows | `2025-11-25` |
| Asked for `2026-07-28` | Replied `2025-11-25` |
| Session header issued? | Yes, `mcp-session-id` |
| `tools/list` with no session | `400 Missing session ID` |
| `tools/list` with the new headers, no session | `400 Missing session ID` |

So it speaks the older, handshake-based protocol. The spec calls this **legacy**, and the newer form **modern**.

Does that matter? It depends who's talking to whom:

| Client | Server | Result |
| --- | --- | --- |
| Legacy | Legacy | Works. This is ShopHelper |
| Modern | Modern | Works |
| Legacy | Modern only | Fails |
| Modern only | Legacy | Fails |
| Supports both | Either | Works |

Today nothing is broken, because this project controls both ends. But another team's modern-only client couldn't connect, and that's when you'd upgrade. `mcp` 2.x exists, so this would be a real migration, not a version bump. It's listed in the project backlog.

Knowing this kind of thing, and being able to say "here's what we're on, here's what it costs", is what engineers do.

## In the market

Checked on 2026-11-06. From the [release post](https://blog.modelcontextprotocol.io/posts/2026-07-28/) and the [versioning spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning.md).

- Python, TypeScript, Go and C# SDKs support the new revision, and Rust has it in beta.
- A server can be **dual-era**, serving old and new clients on one endpoint, which is a sensible way to migrate.
- Deprecated features stay for at least 12 months.
- Some spec pages still show older versions, so check the date on what you're reading.

## Try it

1. See the session for yourself. With the stack running, send an `initialize` request:

   ```bash
   curl -s -i -X POST http://localhost:8765/mcp \
     -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2026-07-28","capabilities":{},"clientInfo":{"name":"me","version":"1"}}}'
   ```

2. In the reply, find the `mcp-session-id` header and the `protocolVersion`. You asked for `2026-07-28`. What did it answer?
3. Send a request with no session:

   ```bash
   curl -s -X POST http://localhost:8765/mcp \
     -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
     -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
   ```

## Interview questions

### What's the difference between stdio and Streamable HTTP?

**Strong answer:** With stdio, the client starts the server as a child process and they talk over stdin and stdout. It's simple, and good for one local client. Streamable HTTP is for a shared server that many clients reach over a network. It needs real auth. In my project I use HTTP locally, partly because per-user identity travels in a header, and a subprocess has no HTTP headers.

**Follow-up:** How would you scale an MCP server?

### What changed in the latest MCP spec?

**Strong answer:** The July 2026 revision made the protocol stateless: the `initialize` handshake and session id are gone, and each request carries its version and client details. So a load balancer can send requests to any instance. There's also `server/discover`, routing headers, and a shift in how clients register. I checked my own project: `mcp` 1.30.0 only speaks the older revision, so it's legacy. It works because I control both ends, but a modern-only client couldn't connect, so upgrading is on my backlog.

**Follow-up:** How would you migrate without breaking existing clients?

### How would you upgrade a live MCP server to a new protocol version?

**Strong answer:** I'd make it dual-era first, so it serves both old and new clients on the same endpoint. Then I'd check what depends on sessions, because state needs an explicit handle now. I'd move clients over, watch which versions are in use, and drop the old path only when nothing needs it. The spec gives deprecated features at least 12 months.

**Follow-up:** What would you measure during the migration?

## Check yourself

### Why did MCP remove sessions?

- [x] So any server can answer any request — right: that makes scaling much simpler.
- [ ] Sessions were insecure — scale was the main reason.
- [ ] To reduce the size of messages — each request now carries more, not less.

### ShopHelper's server replied with `2025-11-25` when asked for `2026-07-28`. What does that show?

- [ ] It's broken — it works fine with its own client.
- [x] It's one version behind — right: `mcp` 1.30.0 doesn't know the newer revision.
- [ ] Version numbers don't matter — they decide who can talk to whom.

### Who can't connect to a legacy server?

- [ ] A legacy client — they work together.
- [x] A modern-only client — right: and a client supporting both can.
- [ ] A client supporting both — it falls back.
