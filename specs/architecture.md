# ShopHelper — Architecture

> How the code is organised and the contracts between its parts. Read before touching shared code or adding a
> module. Each feature's verify step updates this file with what it established.

**Last updated:** 2026-11-04

## Directory Layout

```text
src/shophelper/     Backend: API, agent, tools, MCP, RAG, guardrails, storage
web/                React + TypeScript UI
knowledge/policies/ The RAG source documents
evals/              20 golden conversations and the LLM judge
tests/              Offline tests, using a scripted fake model
infra/              Terraform for AWS
scripts/            check.sh, evals_local.sh, and the AWS deploy scripts
docker/             pgAdmin configuration
docs/               Learning path and reference docs (for people)
specs/, memory/     This workflow
```

## Main Modules and Contracts

[docs/architecture.md](../docs/architecture.md) explains the system for learners. This section lists the
contracts code must keep.

| Module | Responsibility | Contract |
| ------ | -------------- | -------- |
| `service.py` | One turn: guardrail, agent, guardrail, history | Used by both the API and the evals, so they exercise one path |
| `graph.py` | Agent loop, refund node, model selection | Nodes `agent`, `tools`, `refund_approval` |
| `tools.py` | Tool logic | Read-only, and returns errors as data |
| `mcp_server.py` / `mcp_client.py` | Tools over MCP | Thin wrappers around `tools.py` |
| `orders.py`, `memory.py` | Storage | `OrderRepo` and `HistoryStore` protocols, with a backend each for memory, DynamoDB and Postgres |
| `rag.py`, `db.py`, `schema.sql` | Local RAG and Postgres | `VECTOR(768)` must match the embedding model |
| `local_api.py` | Routes for the UI | 404 unless accounts are on |
| `auth.py`, `auth_api.py` | Accounts, sessions, login gate | `UserStore` protocol; `Principal` comes only from a verified session |
| `identity.py` | The acting user during a tool call | `ContextVar`, set only by the graph |
| `conversations.py` | Conversation ownership | Server-issued ids; `ConversationStore` protocol |
| `refunds.py` | Staff queue and approval rules | `authorize_review` reads stored values only; `claim` is atomic |
| `catalog.py` | Products and categories | `ProductRepo` protocol, in memory and Postgres, which must return the same results; `sort` comes from an allowlist |
| `cart.py` | Carts, merging, checkout | `CartStore` protocol; `merge_items` is the one set of merge rules; a cart holds ids and quantities only |
| `shop_api.py` | Shop routes | 404 unless accounts are on; `POST /checkout` takes no body |
| `web/src/chat/chatReducer.ts` | All stream handling | A pure function, with no React or network |
| `web/src/chat/ChatProvider.tsx` | The chat, above every page | Keyed by user, so nothing carries over; moving between pages can't interrupt a stream |
| `web/src/cart/cartLogic.ts`, `useCart.tsx` | The cart in the browser | Storage is untrusted; a merge takes items out of storage before calling the server |
| `web/src/layout/Layout.tsx` | The page frame | The page scrolls in `#page`, above the bottom bar (D-013) |
| `web/src/shop/returns-policy.md` | The shop's copy of the return policy | A test fails if it differs from `knowledge/policies/returns.md` |

SSE events: `guardrail`, `model_step`, `tool_start`, `tool_end`, `token`, `interrupt`, `final`, `error`. `final`
always comes last and its text is authoritative, because the output guardrail may have changed what streamed.

## Isolation Contracts

These protect user data. Changing any of them needs a spec.

- **Protected by default.** `AccountsGate` wraps every request. Only `PUBLIC_PATHS` and GET on the catalogue (`is_public`) are open, and
  a test lists the exact public set.
- **Identity never passes through the model.** It flows session, `Principal`, graph config, `ContextVar`, signed header.
  It's never a tool argument, a prompt or a message.
- **Owner filters live in the query.** Customer-facing reads use `get_for_owner`. Someone else's data and missing data
  take the same path and give the same reply.
- **Fail closed.** With accounts on, a missing identity raises `NoIdentity`, and the MCP server returns "not found".
- **Refunds:** decided by staff, from stored values. The graph resumes as the customer, never as the reviewer.
- **Carts:** every statement filters on the session's user, and no route takes a user id. A signed-in cart is never stored in the browser.
- **Prices come only from `products`.** Checkout reads the cart and prices in one transaction, and `DELETE ... RETURNING` claims the
  cart, so a double click places one order.
- **The chat button never covers an Add to cart.** It has its own space, so don't float anything over `#page`.
- **Browser:** `Shell` is keyed by user id, and the query cache is cleared on login and logout.

## Conventions

- **Configuration:** every setting lives in `config.py` and defaults to AWS behaviour. Local values live in
  `docker-compose.yml`; `.env` is for AWS work and compose only reads the two model names from it.
- **Backends:** add one by implementing the protocol and extending its `get_*` selector. No `if local:` elsewhere.
- **Errors:** tools return errors as data so the model can recover. `/chat/stream` sends an `error` event.
- **Logging:** one JSON line per turn through `log_event`, which CloudWatch metric filters parse.
- **Accounts switch:** `accounts_enabled` is true whenever `DATABASE_URL` is set, and can't be turned off there.
- **Schema:** `schema.sql` is idempotent and runs on every start, so changes must be safe on an existing database.
- **Lint:** ruff, 110-character lines.
