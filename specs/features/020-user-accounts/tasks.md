# 020 — User Accounts and Data Isolation · Tasks

**Plan:** `./plan.md`
Legend: `[P]` = can run in parallel with the previous task. Each task lists files and the proving test.
Test-first: each "tests" task must fail before its paired implementation makes it pass.
When a task is done, tick it and add an indented **Result (YYYY-MM-DD):** note: what was done, numbers measured,
anything surprising or deferred.

Gate after each task: `scripts/check.sh`. Also run `scripts/evals_local.sh` after any task marked **(evals)**.

## Setup

- [x] **T001** — Spike (throwaway): prove a `ContextVar` set inside a graph node reaches an MCP interceptor's header
      and the server's `Context`, and that a cookie passes through the Vite proxy on an SSE request. Record the result;
      use the plan's fallback if it fails · files: scratch only · test: the spike's own output
  - **Result (2026-11-04):** Passed; the fallback isn't needed. A `ContextVar` set in a node reached the interceptor and
    the server as `Authorization`. Two parallel graph runs kept `alice` and `bob` separate. The tool schema showed only
    `order_id`, and a smuggled `user_id` or `ctx` argument was ignored. `request.runtime` is `None` here, so a
    `ContextVar` is required. Outside a node the header was `Bearer None`, so T033 must refuse to call with no identity.
    Through the Vite proxy, the request cookie, `Origin` and `Set-Cookie` all passed, and SSE arrived at 0.3 s intervals
    with no buffering.
- [x] **T002** — Add `argon2-cffi` and direct `pyjwt`, re-export `requirements.txt`, update `specs/tech-stack.md` ·
      files: `pyproject.toml`, `uv.lock`, `requirements.txt`, `specs/tech-stack.md` · test: `scripts/check.sh`
  - **Result (2026-11-04):** Packages added, `requirements.txt` re-exported, tech stack updated, gate green, and
    `argon2` and `jwt` import in the container. The real Dockerfile built in 35 s, through a one-off local proxy, with
    all 84 downloads hash-checked. The slow build was not Docker: this ISP's IPv4 route to `files.pythonhosted.org`
    runs at about 35 KB/s, while IPv6 reaches 2.7-7.4 MB/s, and containers only have IPv4.
- [x] **T003** — Add settings with defaults that keep AWS behaviour, and extend `test_defaults_are_the_aws_path` ·
      files: `config.py`, `tests/conftest.py`, `tests/test_local_stack.py`, `docker-compose.yml` ·
      test: `test_defaults_are_the_aws_path`
  - **Result (2026-11-04):** Tests failed first, then passed; gate green at 37 backend and 9 frontend tests. Added
    `accounts_enabled` as a computed property, slightly different from a plain flag: a database always turns accounts
    on and `AUTH_ENABLED=false` can't turn them off, so the local stack can't run without logins. Compose sets the new
    values; nothing reads them yet.

## Accounts

- [x] **T010** — Failing tests: sign-up, sample orders, chosen role ignored, login, identical login errors · files:
      `tests/test_auth.py`
- [x] **T011** — Failing tests: logout, 24-hour expiry, lockout after 5 failures, hashes only, with time as an input ·
      files: `tests/test_auth.py`
- [x] **T012** — `Principal`, Argon2 hashing, in-memory `UserStore`, sessions and lockout · files: `auth.py` ·
      test: T010, T011
- [x] **T013** — `/auth/*` routes, the cookie, Origin middleware · files: `auth_api.py`, `schemas.py`, `api.py` ·
      test: T010, T011, plus a new test for cross-site refusal
- [x] **T014** — Failing test, then the global route gate with its allowlist, and `require_role` · files: `api.py`,
      `auth_api.py`, `tests/test_isolation.py` · test: the route-walking test; sabotage: unprotect a route
  - **Result (2026-11-04), T010-T014:** Tests failed first; 90 backend tests now pass. Four sabotage checks were caught:
    open gate (15 failures), any role allowed (2), logout keeping the session (1), no Origin check (1). Two departures
    from the plan: the gate is plain ASGI middleware rather than a global dependency, because dependencies don't cover
    `/docs` or `/openapi.json` and AC-8 requires them; and `Origin` is checked on public routes too, which also stops
    cross-site login. The first route-walking test silently skipped included routers; a sanity test exposed it, and
    it now walks the OpenAPI schema as well. Sample orders work in memory; the Postgres version is T021.
- [x] **T015** — Admin routes: list users, change level, keep the last admin · files: `auth_api.py`,
      `tests/test_auth.py` · test: level change applies on the next request
  - **Result (2026-11-04):** Done: 6 tests, covering admin-only access, the next-request level change, and the last
    admin. In-memory store only until T021.

## Data

- [x] **T020** — Tables, `owner_id`, order sequence, idempotent upgrade · files: `schema.sql` · test: run twice on a
      copy of an existing database with no error
  - **Result (2026-11-04):** Five new tables, `orders.owner_id` and the order sequence. Proven by an integration test
    that builds the pre-feature schema with rows, then applies the new one twice. Your real database also upgraded in
    place with no wipe. `refund_requests` has a partial unique index, so the database itself allows one open request
    per conversation.
- [x] **T021** — Postgres `UserStore`, and demo seeding behind `SEED_DEMO_USERS`, with the owner backfill · files:
      `auth.py`, `setup_local.py`, `orders.py` · test: T030
  - **Result (2026-11-04):** `PostgresUserStore`, seeding, owner backfill and `/auth/demo-accounts`. On the real
    database, 9 accounts exist, all 7 orders have owners, and login works through the Vite proxy (wrong password 401,
    other origin 403). `reset()` changed from delete-and-insert to an upsert, so owners and sign-ups' orders survive it.
    This task is proven by T022 rather than T030, which needs the isolation code. Sabotage caught: seeding without the
    setting, and reset clearing owners.
- [x] **T022** — `evals/test_integration.py`: real tables, seeded accounts, upgrade from an old database, ownerless
      conversations hidden, seeding refused without the setting · files: `evals/test_integration.py`,
      `scripts/evals_local.sh` · test: itself
  - **Result (2026-11-04):** 13 integration tests in a throwaway database; the demo data is untouched. Full run: 33
    passed (20 golden, 13 integration), faithfulness 5.0, in 71 s. `evals_local.sh` now resets orders directly, because
    `/demo/reset` needs an admin session. "Ownerless conversations hidden" is proven at table level here; the route
    level comes with T035.

## Isolation

- [x] **T030** — Failing tests: another user's order matches a missing order; a scripted model passing another
      identity gets nothing; missing `Principal` raises · files: `tests/test_isolation.py`
- [x] **T031** — `get_for_owner` in each order backend, and the owner-scoped tool · files: `orders.py`, `tools.py` ·
      test: T030; sabotage: remove the owner filter
- [x] **T032** — Pass `Principal` through service and graph config, with `run_tool` setting the identity · files:
      `service.py`, `graph.py` · test: T030 **(evals)**
  - **Result (2026-11-04), T030-T032:** Done, with one process failure: a shell error dropped the tests, so this code
    went in before its tests and they were never seen failing first. To make up for it, each protection was removed in
    turn: 10 of 10 sabotage checks were caught (owner filter in memory and SQL, tool check, missing identity, graph
    identity, refund check, service check, conversation check, token check, MCP check). 20 parallel users kept
    separate. `ContextVar` lives in a new `identity.py`.
- [x] **T033** — Failing test, then the signed internal token, the MCP interceptor and server verification · files:
      `auth.py`, `mcp_client.py`, `mcp_server.py`, `evals/test_integration.py` · test: an MCP call without a valid
      token returns no order data; sabotage: skip verification
  - **Result (2026-11-04):** Forged, expired, garbage and missing tokens all return "No order found". Tool schema shows
    only `order_id`. A false alarm cost time: a valid token was refused because my `reset()` sabotage ran through
    `evals_local.sh` and cleared real owners. Setup repaired it. A second one: the MCP container didn't reload after the
    last sabotage was restored, so it kept treating everyone as user 2, which invalidated one live attack run. After a
    restart, the rerun gave 0 leaks across 6 attacks, with each real user seeing their own order.
- [x] **T034** — Failing tests, then refund requests scoped to the owner · files: `graph.py`, `tests/test_isolation.py`
      · test: a refund on another user's order creates no request
  - **Result (2026-11-04):** Done. The reply is identical to a missing order, and the order is unchanged.
- [x] **T035** — Failing tests, then the conversations store, routes and 404 for other users' ids · files:
      `conversations.py`, `api.py`, `tests/test_isolation.py` · test: B's id behaves like an unknown id on every route
  - **Result (2026-11-04):** Ids now come from `POST /conversations`, and ownership is checked in the API. Identical
    404s on `/chat`, `/chat/stream`, history and open. Titles come from the masked first message.
    **Still open until T042-T043:** any signed-in user can call `/approve`, and `/orders` lists everyone's orders.

## Refund queue

- [x] **T040** — Failing tests: every approval rule, reviewer name ignored, double decision refused, resume runs as
      the customer · files: `tests/test_refund_queue.py`
- [x] **T041** — `refund_requests` store, `authorize_review`, atomic claim, `/refunds/pending` · files: `refunds.py`,
      `api.py` · test: T040; sabotage: remove the self-approval rule
  - **Result (2026-11-04), T040-T041:** Tests seen failing first; 28 unit tests and 4 Postgres tests added. 8 reviewers
    racing on real Postgres produce exactly one winner. 16 of 16 sabotage checks were caught, using unit tests or the
    scratch database, so no real data was touched.
- [x] **T042** — Wire `/approve` and `/approve/stream`, optional `reviewer`, reset cancels pending requests · files:
      `api.py`, `service.py`, `local_api.py`, `schemas.py` · test: T040 **(evals)**
  - **Result (2026-11-04):** Live run through the real model: Kabir's $249 refund paused; Kabir, Asha and Support each
    got 403 with the order unchanged; Admin approved; the order became `refunded`; the database recorded Admin as
    reviewer although the request said "mallory"; Kabir saw the reply without sending anything; a second approval got
    409. Added beyond the plan: `queue_pending_refund`, because a resumed turn can pause on a second refund while the
    first is still open. Known limit: a conversation paused when a demo reset cancels its request stays paused, so the
    customer starts a new one. A claimed request whose resume crashes stays claimed, by design (see plan risks).
- [x] **T043** — Role rules on `/orders` and `/demo/reset` · files: `local_api.py`, `tests/test_isolation.py` ·
      test: customer sees only their own orders; reset needs admin
  - **Result (2026-11-04):** Done, live and in tests. Both gaps left open by T035 are closed. `local_api.py` now keys off
    `accounts_enabled`. 148 backend tests, 9 frontend tests, 20 evals and 21 integration tests pass.

## Evals

- [x] **T050** — Run the original 20 cases as users (`as:` field). Log any changed expected result · files:
      `evals/golden_cases.yaml`, `evals/test_golden.py` · test: `scripts/evals_local.sh`, 20 of 20 **(evals)**
  - **Result (2026-11-04):** Done early, because evals need a user once identity is required. Each case runs as the
    owner of its order. No expected result changed. 20 of 20 evals and 17 integration tests pass, in 68 s.
- [x] **T051** — Add at least 5 cross-user cases, including injection · files: `evals/golden_cases.yaml` · test:
      `scripts/evals_local.sh`, run 3 times **(evals)**
  - **Result (2026-11-04):** 7 cross-user cases added, 27 of 27 passing in 4 runs out of 4, about 90 s each. All 7 reached
    `get_order_status`, so no guardrail was doing the work. With the owner checks removed, all 7 failed: the model handed
    over the data, and one refund reached `pending_approval`. Isolation holds because of the query, not the model.
    Cross-user cases skip with accounts off, so the AWS evals stay at 20. For chapter 11: use this as the main lesson.

## Frontend

- [x] **T060** — API types and client calls for accounts, conversations and refunds · files: `web/src/api/*` ·
      test: `npm run typecheck`
- [x] **T061** — `useAuth`, login and sign-up pages, demo account list, signed-out redirect, header identity and logout
      · files: `web/src/auth/*`, `App.tsx` · test: browser check, recorded here
- [x] **T062** — Tabs by level · files: `App.tsx` · test: browser check as each level, with the server refusing direct
      requests (T043)
- [x] **T063** — Failing reducer tests, then conversations in `useChat`: server ids, reopening, the pending state ·
      files: `chat/*` · test: `npm test`
- [x] **T064** — Conversation list, and "waiting for review" with polling · files: `ConversationList.tsx`,
      `MessageBubble.tsx`, `views/ChatView.tsx` · test: browser check that a decision appears without sending a message
- [x] **T065** [P] — Refund queue tab · files: `views/QueueView.tsx` · test: browser check as support and admin
- [x] **T066** [P] — Users tab, and Orders tab by level · files: `views/UsersView.tsx`, `views/OrdersView.tsx` ·
      test: browser check as admin and customer
  - **Result (2026-11-04), T060-T066:** Reducer tests seen failing first; 13 frontend tests pass. A throwaway browser
    script (not committed, by the owner's decision) ran 4 people in separate browsers: 30 checks, all met. The one
    reported failure was the script's filter: every failed response was listed by URL and each is deliberate (`/auth/me`
    401 when signed out, bad login, short password, last admin, stolen conversation). Client-side isolation: after Asha
    logged out and Ravi logged in on the same tab, the page held nothing of Asha's, and Ravi saw his own order. How:
    `Shell` is keyed by user id, logout and login clear the query cache, and the stored conversation id is per user.
    Also: approval moved from the chat to the queue, examples are built from what the user owns, and a "Data isolation"
    example replaced "Policy check", which depended on another customer's order. Trace history isn't stored, so a
    reopened conversation shows an empty trace. Browsers log any 4xx as a console error, so signed-out page loads show
    one for `/auth/me`; DoD item 7 is read as "no unexpected errors". My test accounts and chats were removed.

## Docs

- [x] **T070** — Chapter 11: authentication, authorization, isolation, why a prompt can't provide it, identity
      providers, row-level security. Run every Try it step · files: `docs/learn/11-accounts-and-isolation.md`,
      `docs/README.md`
  - **Result (2026-11-04):** Chapter 11 opens with the measured 7-attack experiment. Its Try it steps were run: attacks,
    positive control, `document.cookie` empty, cookie `HttpOnly` and `SameSite=Strict`, SQL queries, level change
    reaching an open app in 29.7 s, and the sabotage step (done during T051).
- [x] **T071** [P] — Update and re-run chapters 3, 5, 7 and 10, then `docs/local-setup.md`, `docs/architecture.md`,
      `README.md` · files: listed
  - **Result (2026-11-04):** 19 scripted checks of the changed exercises pass (chapters 2, 5, 8, 11), plus the chapter 6
    curl flow. 20 diagrams render and 148 links resolve. Running them found real problems: the old curl example returned
    401, "Policy check" no longer existed, and a troubleshooting row was wrong (`127.0.0.1` gives "Cross-site request
    refused", not a sign-out). **Not run: chapter 3 steps 1-3, the MCP Inspector.** `npx` was blocked as external code.
    The server behaviour they show is proven by `evals/test_integration.py`, but the Inspector steps themselves are
    untested, including how it passes the header. The owner should try them.
- [x] **T072** — Add row-level security to the roadmap backlog · files: `specs/roadmap.md`
  - **Result (2026-11-04):** Added, along with accounts on AWS and clearing a refund stuck in `claimed`.

## Verify

- [x] **T090** — Measure the identity check (under 20 ms) and confirm no password in the database, logs, history or
      checkpoints · test: recorded numbers and queries
  - **Result (2026-11-04):** Closed by D-010: AC-6 narrowed, limit documented. Identity check over 300 requests: median
    14.6 ms, p95 18.8 ms, so within the 20 ms limit, with little margin (it opens two database connections per request).
    Passwords: login and sign-up leave nothing in the database dump or container logs, and "my password is X" is blocked.
    But "please remember X as my password" passes the regex, and X reached `chat_history`, the conversation title,
    checkpoints and the model. Checkpoints are binary, so a text search of a dump misses them: use `position(... in blob)`.
- [x] **T091** — Full manual browser run as customer, support and admin, with no console errors, on a database upgraded
      in place and on a clean rebuild · test: recorded here
  - **Result (2026-11-04):** In-place upgrade: done on the real database at T021, and the app ran on it through T066.
    Clean rebuild: `down -v`, then stack up in 16 s, setup embedded 20 chunks. 30 of 30 browser checks passed as 4 people.
    Every failed response was listed by URL, and each was a deliberate test or the signed-out `/auth/me` check.
- [x] **T092** — Update `specs/architecture.md` and `specs/testing-strategy.md`.
  - **Result (2026-11-04):** Added the isolation contracts, the integration test layer, and rules 10-13.
- [x] **T093** — Confirm `git status infra` is empty, `terraform validate` passes, and the image started with AWS
      settings needs no login, as today.
  - **Result (2026-11-04):** `infra/`, Dockerfile and CI unchanged; `terraform validate` and `fmt` pass. The same image
    with AWS settings: Bedrock and in-memory backends selected, accounts off, every local route 404, no gate on `/chat`
    or `/approve`, and psycopg, argon2, jwt and langchain_openai not loaded. `/chat` reached Bedrock's `Converse` call and
    failed only on the fake keys (`UnrecognizedClientException`). A real Bedrock call remains untested.
- [x] **T094** — Every Definition-of-Done gate green (`specs/constitution.md`); record the numbers.
  - **Result (2026-11-04):** `scripts/check.sh` passes (148 backend, 13 frontend). `scripts/evals_local.sh` 48 of 48: 27 of
    27 evals, 12 of 12 attacks, faithfulness 5.0 (Qwen judging itself), 21 integration tests, 90 s. Web build passes.
    Terraform validates. Browser run has no unexpected errors. 20 diagrams, 148 links.
- [x] **T095** — Tick ACs in `spec.md` (Status `Implemented`), update `roadmap.md`, `memory/progress.md`,
      `memory/MEMORY.md`.
  - **Result (2026-11-04):** 29 of 29 criteria ticked, status Implemented, roadmap updated.

## AC coverage

| AC    | Tasks            |
| ----- | ---------------- |
| AC-1  | T010, T012, T013 |
| AC-2  | T010, T012, T013, T061 |
| AC-3  | T011, T012, T013 |
| AC-4  | T011, T012       |
| AC-5  | T011, T012       |
| AC-6  | T011, T012, T090 |
| AC-7  | T010, T013       |
| AC-8  | T014             |
| AC-9  | T030, T031, T051 |
| AC-10 | T030, T032, T033 |
| AC-11 | T034             |
| AC-12 | T035             |
| AC-13 | T033             |
| AC-14 | T051             |
| AC-15 | T040, T042, T064 |
| AC-16 | T040, T041, T065 |
| AC-17 | T040, T042       |
| AC-18 | T042, T064       |
| AC-19 | T020, T021, T022 |
| AC-20 | T020, T022, T091 |
| AC-21 | T015, T066       |
| AC-22 | T061             |
| AC-23 | T043, T062       |
| AC-24 | T035, T063, T064 |
| AC-25 | T061             |
| AC-26 | T003, T093       |
| AC-27 | T050             |
| AC-28 | T070             |
| AC-29 | T071             |
