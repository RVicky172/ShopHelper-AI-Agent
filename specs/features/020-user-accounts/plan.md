# 020 — User Accounts and Data Isolation · Implementation Plan

**Spec:** `./spec.md` · **Status:** Approved

## Approach

### §1 One switch, failing closed

Accounts are on when `DATABASE_URL` is set, the same switch that selects the local stack. With it unset, nothing here
runs and AWS behaves as it does today (Constitution VI).

A `Principal` (user id, email, role) describes who is acting. With accounts on, any order access without a `Principal`
**raises an error** rather than returning data. A forgotten argument must fail loudly, never leak.

### §2 Browser sessions

Login sets an opaque random token in an `HttpOnly`, `SameSite=Strict` cookie. Postgres stores only its SHA-256 hash and
an expiry. Page scripts can't read the cookie (NFR), and deleting the row ends the session at once (AC-3).

A JWT would not satisfy AC-3, because a signed token stays valid until it expires. Every request reads the user's role
from the database, so a level change applies on the next request (AC-21).

Cross-site protection: `SameSite=Strict`, plus middleware refusing state-changing requests whose `Origin` isn't
`WEB_ORIGIN`.

### §3 One gate for every route

`FastAPI(dependencies=[Depends(require_session)])` applies to all routes, with an explicit allowlist: `/health`,
`/auth/signup`, `/auth/login`, `/auth/demo-accounts`. A new route is protected by default, and the AC-8 test walks
`app.routes` to prove it. `require_role(...)` adds level checks on top.

### §4 Identity reaches tools outside the model's view

This is the core of the feature.

```text
cookie → require_session → Principal → service → graph config (configurable.user_id)
       → run_tool sets a ContextVar → MCP interceptor signs a 60-second token → Authorization header
       → MCP server verifies it → orders WHERE order_id = ? AND owner_id = ?
```

- `user_id` is never in a tool schema, a prompt or a message, so the model can't see or set it (AC-10).
- The token is created at call time and never stored in config or checkpoints.
- The MCP server trusts only the signature, and returns "not found" without a valid token (AC-13). `search_policy`
  stays open because policies are public.
- A missing order and someone else's order run the same query and give the same reply (AC-9). There is no
  "belongs to someone else" branch to leak through.
- `refund_approval` reads the same identity from its config, so refunds get the same check (AC-11).

### §5 Conversations

A new `conversations` table owns each session id. With accounts on, ids come from the server (`POST /conversations`),
and any id the caller doesn't own returns 404, exactly like an unknown id (AC-12). Client-chosen ids would leak: a taken
id would fail while a free one worked. Existing rows have no owner, so nobody can reach them (AC-20).

### §6 Refund queue

A `refund_requests` table is written when the graph pauses, and is the source of truth for review:

1. `POST /approve` loads the pending request by session.
2. Rules run from the **stored** amount and owner, never request data: staff only, over $200 needs admin, never your own.
3. One atomic `UPDATE ... WHERE status = 'pending'` claims it, so two reviewers can't both decide.
4. The graph resumes **as the customer**, because it's their conversation. The reviewer is only recorded.

The reviewer name in the request is ignored (AC-17). The customer's reply appears in their history, and the UI polls
while a refund is pending (AC-18).

### §7 Database

`schema.sql` stays idempotent, so `setup` upgrades an existing database (AC-20): new tables, `ALTER TABLE orders ADD
COLUMN IF NOT EXISTS owner_id`, and a backfill from demo customer names. Sample orders use a sequence starting at 2001.

Demo users are created only with `SEED_DEMO_USERS=true`, which only `docker-compose.yml` sets (Q6).

### §8 Offline tests

Unit tests must stay offline, so accounts follow the existing pattern: a `UserStore` protocol with in-memory and
Postgres backends. A separate `auth_enabled` setting lets tests turn accounts on without a database.

### §9 Frontend

No router library: signed-out users see the login page, and signed-in users get tabs for their level. New tabs are
Refund queue (staff) and Users (admin). A conversation list sits beside the chat. The approval card moves to the queue,
and customers see a "waiting for review" state instead.

## Files

| File | Change | Purpose |
| ---- | ------ | ------- |
| `src/shophelper/auth.py` | new | `Principal`, hashing, sessions, lockout, `UserStore` backends, internal tokens |
| `src/shophelper/auth_api.py` | new | `/auth/*`, `/admin/users`, route dependencies, Origin middleware |
| `src/shophelper/conversations.py` | new | Ownership store: in-memory and Postgres backends |
| `src/shophelper/refunds.py` | new | Refund queue, approval rules, atomic claim |
| `src/shophelper/api.py` | modify | Global gate, ownership checks, conversation and refund routes |
| `src/shophelper/local_api.py` | modify | Role rules on `/orders`, `/demo/reset` |
| `src/shophelper/service.py` | modify | Pass `Principal`, write refund requests, resume as the customer |
| `src/shophelper/graph.py` | modify | Read identity from config in `run_tool` and `_decide_refund` |
| `src/shophelper/tools.py` | modify | Owner-scoped `get_order_status` |
| `src/shophelper/orders.py` | modify | `get_for_owner`, `owner_id`, sample orders |
| `src/shophelper/mcp_server.py` | modify | Verify the token through FastMCP `Context` |
| `src/shophelper/mcp_client.py` | modify | Interceptor adds the signed header |
| `src/shophelper/schemas.py` | modify | Auth models; `reviewer` becomes optional |
| `src/shophelper/config.py` | modify | `auth_enabled`, `internal_token_secret`, `web_origin`, `seed_demo_users` |
| `src/shophelper/schema.sql` | modify | New tables and `owner_id` |
| `src/shophelper/setup_local.py` | modify | Seed demo users, backfill owners |
| `docker-compose.yml` | modify | New settings |
| `pyproject.toml`, `uv.lock`, `requirements.txt` | modify | `argon2-cffi`, direct `pyjwt` |
| `web/src/auth/*` | new | `useAuth`, login and sign-up pages |
| `web/src/views/QueueView.tsx`, `UsersView.tsx` | new | Staff and admin tabs |
| `web/src/components/ConversationList.tsx` | new | Own conversations |
| `web/src/App.tsx`, `chat/useChat.ts`, `chat/chatReducer.ts`, `api/*`, `components/MessageBubble.tsx`, `views/OrdersView.tsx` | modify | Accounts in the UI |
| `tests/test_auth.py`, `tests/test_isolation.py`, `tests/test_refund_queue.py` | new | Unit tests |
| `evals/golden_cases.yaml`, `evals/test_golden.py` | modify | Act as a user; add cross-user cases |
| `evals/test_integration.py` | new | Real Postgres and MCP checks |
| `docs/learn/11-accounts-and-isolation.md` | new | The new chapter |
| `docs/learn/03-mcp.md`, `05-*.md`, `07-frontend.md`, `10-*.md`, `docs/local-setup.md`, `docs/architecture.md`, `docs/README.md`, `README.md` | modify | Updated exercises and diagrams |
| `specs/architecture.md`, `specs/tech-stack.md`, `specs/testing-strategy.md` | modify | New contracts |

## Data Structures & Interfaces

```sql
users            (id, email UNIQUE, password_hash, role, display_name, created_at)
auth_sessions    (token_hash PK, user_id, created_at, expires_at)
login_attempts   (email, attempted_at)
conversations    (session_id PK, owner_id, title, created_at, updated_at)
refund_requests  (id, session_id, order_id, owner_id, amount, reason, needs_supervisor,
                  status, reviewer_id, note, created_at, decided_at)
orders           + owner_id
```

```python
@dataclass(frozen=True)
class Principal:
    user_id: int
    email: str
    role: Literal["customer", "support", "admin"]

ShopHelperService.chat(session_id, message, principal: Principal | None = None)
ShopHelperService.stream(session_id, message, principal: Principal | None = None)
OrderRepo.get_for_owner(order_id, owner_id) -> dict | None
authorize_review(request, reviewer: Principal) -> None   # raises Forbidden
```

| Route | Access |
| ----- | ------ |
| `POST /auth/signup`, `/auth/login` | Public |
| `GET /auth/demo-accounts` | Public; empty unless `SEED_DEMO_USERS` |
| `POST /auth/logout`, `GET /auth/me` | Signed in |
| `GET, POST /conversations`, `GET /conversations/{id}` | Owner only |
| `GET /refunds/pending` | Support, admin |
| `POST /approve`, `/approve/stream` | Support, admin, by the §6 rules |
| `GET /admin/users`, `PATCH /admin/users/{id}` | Admin |
| `GET /orders` | Own orders for customers, all for staff |
| `POST /demo/reset` | Admin |

## Techniques

- **Passwords:** Argon2id through `argon2-cffi`. Unknown emails still run a hash, so timing doesn't reveal which emails
  exist (AC-2). Passwords use `SecretStr` so they stay out of reprs.
- **Internal token:** a 60-second HS256 JWT, signed with `INTERNAL_TOKEN_SECRET`. It's a good fit here: short-lived and
  needs no revocation, unlike browser sessions.
- **Time as an input:** session expiry and lockout functions take `now`, so AC-4 and AC-5 need no sleeps.
- **Emails:** lower-cased, then checked with a simple pattern. No extra validation library.
- **Reset:** `/demo/reset` restores seeded orders and cancels pending requests, so stale approvals return 409.
- **Not used:** Postgres row-level security. It's a good second layer, but one enforced path is easier to learn first.
  The new chapter explains it, and it goes in the backlog.

## Test Approach

| AC | Test file | Type |
| -- | --------- | ---- |
| AC-1, 2, 3, 4, 5, 7 | `tests/test_auth.py` | unit |
| AC-2 (reload), 22, 24, 25 | Browser check, results recorded in `tasks.md` | manual e2e |
| AC-6 | `tests/test_auth.py`, then a pgAdmin check | unit + manual |
| AC-8 | `tests/test_isolation.py`, walking `app.routes` | unit |
| AC-9, 10, 11, 12 | `tests/test_isolation.py`, with the scripted model | unit |
| AC-9, 14 | `evals/golden_cases.yaml` | e2e |
| AC-13 | `evals/test_integration.py` | integration |
| AC-15, 16, 17, 21 | `tests/test_refund_queue.py`, `tests/test_auth.py` | unit |
| AC-15, 16, 18, 23 | Browser check for the UI, plus the unit tests above for server rules | manual e2e |
| AC-19, 20 | `evals/test_integration.py`, with a pre-feature database | integration |
| AC-26 | `tests/test_local_stack.py`, then `git status infra` | unit + manual |
| AC-27 | `scripts/evals_local.sh` | e2e |
| AC-28, 29 | Each Try it step run by hand | manual |
| NFR: under 20 ms | Measured against the running stack | measurement |

Each security test also gets a sabotage check: remove the owner filter, confirm the test fails, restore it.

No browser test tool is added to the repo in this feature, by the owner's decision on 2026-11-04. It stays in the
roadmap backlog. Until then, UI checks are repeated by hand, so a UI regression won't be caught automatically. The
security rules themselves are still covered by automated unit tests and evals.

## Risks & Mitigations

- **Interceptors may not see per-call context inside a graph node.** Spike first: prove that a `ContextVar` set in
  `run_tool` reaches the header and the server. Fallback: a short-lived MCP client per call.
- **The 20 evals assume no owners.** Each case gets an `as:` user. Some expected answers could change, such as case 19,
  which asks for every customer's orders. Any change to an expected result is logged, never quietly loosened.
- **A claimed refund could fail while resuming.** The request stays `claimed` and is shown to staff, rather than risking
  a double refund through a retry.
- **Cookies treat `localhost` and `127.0.0.1` as different sites.** Docs and `WEB_ORIGIN` use `localhost` for the
  browser. Scripts that use `127.0.0.1` keep their own cookie.
- **SSE needs the cookie through the Vite proxy.** It's same-origin, so it should work. Covered by the spike.
- **Size.** This touches most backend files. Tasks stay small and each passes the gate on its own.

## Constitution Check

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Spec before code | ✅ | Spec Approved on 2026-11-04 |
| II. Test-gated delivery | ✅ | Every AC has a test or measurement; evals run after agent changes |
| III. Small dependencies | ⚠️ | One new package, `argon2-cffi`: hand-rolled password hashing is unsafe. `pyjwt` is already installed through `mcp`, and becomes direct |
| IV. Memory maintained | ✅ | Decision logged when dependencies are approved |
| V. The model asks, code acts | ✅ | Identity never reaches the model. This strengthens the principle |
| VI. AWS stays the default | ✅ | Off unless `DATABASE_URL` is set; `infra/` unchanged. New packages enlarge the image slightly |
| VII. Local first | ✅ | No external identity or email service |
| VIII. Built to learn | ✅ | New chapter, and exercises re-run |
| IX. Stream changes additive | ✅ | No event renamed. `/chat/stream` gains a 401 and 404 for bad access |
