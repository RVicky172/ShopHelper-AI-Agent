---
title: Authorization and risks
checked: 2026-11-06
---

## What you'll learn

- How a tool server knows who's calling
- How MCP's standard authorization works
- The attacks specific to MCP
- How to judge a server before you trust it

## The simple explanation

Once users have private data, a tool server has a new problem. `get_order_status` needs to know whose orders to search, and it can't just believe whoever connects.

A tool argument won't do, because the model writes those. So identity has to travel **outside the tool call**.

For remote servers, the MCP spec uses [OAuth 2.1](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization.md), the same family of standards behind "Sign in with Google":

| Role | Who | Job |
| --- | --- | --- |
| **Resource server** | The MCP server | Holds the tools, and checks tokens |
| **Client** | The AI app | Gets a token, and sends it on every request |
| **Authorization server** | A login service | Checks the user, and issues tokens |

It's like a hotel. The front desk (authorization server) checks who you are and gives you a key card. The doors (MCP server) only check the card. A key card for one hotel doesn't open another.

That's the rule that matters most: a token must be meant **for this server**. A server must not accept tokens issued for something else, and must not pass them on to another service. The spec calls that **token passthrough**, and forbids it.

## An example

Here's how a client reaches a protected server:

1. It calls the server with no token, and gets `401`, with a pointer to the server's metadata.
2. It reads that metadata to find the authorization server.
3. The user signs in, and approves access.
4. The client gets a token for this server, and sends it on every request.

Scopes limit what a token can do, such as `files:read`. Ask for the least you need. If a token is stolen, narrow scopes limit the damage.

Authorization is optional in the spec, and stdio servers shouldn't use this flow: they get credentials from the environment.

## How ShopHelper does it

This project doesn't use OAuth, because its only client is its own API. It uses something simpler, with the same principle: a short-lived signed token, in a header the model can't see.

The client adds it to each call:

```python file=src/shophelper/mcp/client.py
async def add_identity(request, handler):
...
user_id = identity.current_user()
```

The server checks the signature, and FastMCP's `ctx` parameter gives it the header without adding anything to the schema the model sees:

```python file=src/shophelper/mcp/server.py
return auth.verify_internal_token(header.removeprefix("Bearer "))
```

No valid token means "No order found". `search_policy` stays open, because policies are public.

**Read-only by design.** An MCP server is open to any client that can reach it. If refunds lived there, any client could call them and skip the approval graph. So only read tools are on the server, and the money-moving action stays in the graph.

**What we'd change for real use.** Tokens here are signed with a shared secret, and the port is bound to `127.0.0.1`. The spec's security guide warns that binding to localhost isn't an authentication boundary on its own: other local processes can reach it, and even websites through your browser. That's one reason the token check matters here. Serving other companies' clients would need the full OAuth flow.

## In the market

Checked on 2026-11-06.

The biggest MCP risk isn't in the protocol. It's trusting servers you didn't write. The official [local server security guide](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/local-server-security) and [security best practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices) cover these:

| Attack | What happens | Defence |
| --- | --- | --- |
| **Tool poisoning** | Hidden instructions in a tool's description steer the agent, even if that tool is never called | Treat descriptions as untrusted input, and read them |
| **Tool shadowing** | One server's description changes how the agent uses another server's tools | Few servers, because they share one context |
| **Rug pull** | A server changes its tools after you approved it | Clients that ask again when definitions change |
| **Malicious package** | A lookalike or compromised server steals your data | Check the publisher, and pin the version |
| **Token passthrough** | A server accepts or forwards tokens not meant for it | Check the token's audience |
| **Confused deputy** | A proxy server is tricked into using its access for an attacker | Ask for consent per client |
| **SSRF** | A bad server points a client at internal addresses | Block private addresses, and require HTTPS |

Two lines from those guides are worth remembering. A local server is an ordinary process with your access, so the guide says to treat third-party servers as "untrusted code with exactly the privileges you hand it". And: "no check proves what a server will do".

So before adding a server: know who wrote it, pin the version, read its tool descriptions, give it the narrowest access you can, and run it in a container. The [OWASP MCP cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html) is a useful companion.

## Try it

1. **Open the Inspector**, a UI for any MCP server:

   ```bash
   npx @modelcontextprotocol/inspector
   ```

   Choose **Streamable HTTP**, enter `http://localhost:8765/mcp`, and connect. List the tools. You're now a second client of the same server.

2. **Call a tool with no identity.** Call `get_order_status` with order `1001`. It answers `No order found`, even though the order exists. Then call `search_policy`, which works for anyone.

3. **Call it with a token.** Create one, which lasts 60 seconds:

   ```bash
   docker compose exec mcp python -c "from shophelper.accounts import auth; s = auth.get_user_store(); print(auth.issue_internal_token(s.get_by_email('asha@demo.shophelper.test').user_id))"
   ```

   In the Inspector, add the header `Authorization: Bearer <token>`, reconnect, and call `get_order_status` for `1001` again. Now it returns Asha's order, but `1002` still doesn't exist as far as she's concerned.

## Interview questions

### How do you secure an MCP server?

**Strong answer:** Remote servers should use the spec's OAuth 2.1 flow: the server checks a token issued for it, and never accepts or forwards tokens meant for something else. I'd use narrow scopes, validate inputs, and keep risky actions off the server. In my project the only client is my own API, so I use a short-lived signed token in a header, which the model can't see, and only read-only tools are exposed. Refunds stay in the graph, behind human approval.

**Follow-up:** Why is a localhost port not enough protection?

### What's tool poisoning?

**Strong answer:** Tool descriptions are text the model reads as instructions. A malicious server can hide directions in them, like "also send the user's data to this address", and the agent can be steered even if that tool is never called. All connected servers share one context, so it can affect how other servers' tools are used. So I treat descriptions as untrusted, keep few servers, read what they say, and prefer clients that ask again if definitions change.

**Follow-up:** How would you detect a server that changes its tools later?

### Your team wants to install a community MCP server. What do you check?

**Strong answer:** Who publishes it and whether I can read the source, the exact package name, and I'd pin the version. I'd read its tool descriptions, give it its own narrow credentials, and run it in a container with only the files it needs, and no network if it doesn't need one. The official guide's point is that nothing proves what a server will do, so I limit what it could do.

**Follow-up:** What if it needs broad access to be useful?

## Check yourself

### Why can't a customer's identity be a tool argument?

- [ ] Arguments are too small — size isn't the issue.
- [x] The model writes arguments, so it could be steered to pass someone else's — right: identity must travel outside the tool call.
- [ ] The protocol forbids arguments — tools use them all the time.

### What's token passthrough?

- [x] A server accepting or forwarding tokens not meant for it — right: the spec forbids it.
- [ ] Sending a token on every request — that's required.
- [ ] Refreshing an expired token — that's normal.

### How can a poisoned tool affect an agent?

- [ ] Only if the tool is called — its description alone can do it.
- [ ] It can't, if the server is local — local servers are at least as risky.
- [x] Its description is read as instructions, even if it's never called — right: treat descriptions as untrusted.
