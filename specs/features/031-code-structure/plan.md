# 031 — Code Structure and Standards · Implementation Plan

**Spec:** `./spec.md` · **Status:** Approved

## Approach

### §1 Safety net first

Checks land before anything moves, so every later change is proved by them: the import rule test, the path test, and the frontend CI job. Today the frontend's
82 tests run only on this machine, so CI must cover them before frontend files move.

### §2 Layers

Measured from the real imports. Each folder may import only those to its left in this order, and a test enforces it, including imports inside functions:

```
core  <-  shop  <-  accounts  <-  rag*  <-  agent  <-  mcp  <-  api
```

`rag` depends only on `core`. Its place in the line is for reading, and the test uses this table:

| Folder | May import |
| ------ | ---------- |
| `core` | nothing |
| `shop` | `core` |
| `accounts` | `core`, `shop` |
| `rag` | `core` |
| `agent` | `core`, `shop`, `accounts`, `rag` |
| `mcp` | `core`, `shop`, `accounts`, `agent` |
| `api` | all of them |

The first layout created 2 cycles, and each has a small fix (D-024):

- **`shop` and `accounts`:** `auth.py` creates sample orders at sign-up, and `refunds.py` needs `Principal`. `Principal` is a plain dataclass, so it moves to `core/identity.py`.
- **`agent` and `api`:** `service.py` returns `ChatResponse`. It moves to `agent/schemas.py`, and the request models go to `api/schemas.py`.

`setup_local.py` imports `accounts`, `shop` and `rag`, so it joins `api/`, the layer for entry points.

### §3 Backend moves

| Today | Moves to |
| ----- | -------- |
| `config`, `db`, `observability`, `identity`, `schema.sql` | `core/` |
| `catalog`, `cart`, `orders`, `refunds` | `shop/` |
| `auth`, `conversations` | `accounts/` |
| `rag` | `rag/pipeline.py` |
| `graph`, `service`, `tools`, `memory`, `guardrails`, `raw_agent` | `agent/` |
| `mcp_client`, `mcp_server` | `mcp/client.py`, `mcp/server.py` |
| `api`, `auth_api`, `shop_api`, `local_api`, `setup_local` | `api/app.py`, `auth_routes.py`, `shop_routes.py`, `local_routes.py`, `setup_local.py` |
| `data/` | stays, because `infra/dynamodb.tf` reads it |

- Done by a one-off script: `git mv`, then import rewrites, then `ruff --fix` for import order. The commit contains only that.
- `__init__.py` files stay empty. Re-exports would load local-only packages on AWS, which breaks Constitution VI.
- `shophelper/mcp/` beside the `mcp` library is safe, because every import is absolute. The spike confirms it.
- Paths built from `__file__` change: `parents[2]` becomes `parents[3]` for `knowledge/`, and `data/` becomes one level up. A wrong path fails at start, so unit tests and `setup` catch it.
- Entry points to update: the `Dockerfile`, `docker-compose.yml` (`api`, `mcp`, `setup`) and `scripts/evals_local.sh`. Nothing in `infra/` names a module, so it needs no edit.

### §4 Tests

`tests/` mirrors the 7 folders. Names stay unique, so pytest needs no new settings. `test_shop.py` (645 lines) splits along its own section headers, into catalogue, cart, checkout,
delivery and policy files. `evals/test_integration.py` (589 lines) splits the same way. The test count is compared before and after, so none can vanish in the move.

### §5 Frontend moves

| Today | Moves to |
| ----- | -------- |
| `api/`, `layout/` | `shared/` |
| `chat/`, `ConversationList`, `MessageBubble` | `features/chat/` |
| `cart/` | `features/cart/` |
| `auth/` | `features/auth/` |
| `shop/`, `OrdersView` | `features/shop/` |
| `QueueView`, `UsersView` | `features/staff/` |
| `HowItWorks`, `ChatView`, `RagView`, `ToolsView`, `TracePanel` | `features/how-it-works/` |

`App.tsx`, `main.tsx` and `index.css` stay. `tests/` also reads `returns-policy.md`, so that path updates too. Restart `web` after the move (learnings).

### §6 Pull requests

Each one is small, passes `scripts/check.sh`, and merges by itself:

1. **Safety net:** import and path tests, frontend CI job, spike results.
2. **Backend moves:** paths and imports, plus the 2 cycle fixes as a separate commit first.
3. **Test layout.**
4. **Frontend moves.**
5. **Frontend lint and format:** config in one commit, the mechanical reformat in another.
6. **Pre-commit hooks.**
7. **Type check, part 1:** `core`, `shop`, `accounts`, `rag`.
8. **Type check, part 2:** `agent`, `mcp`, `api`, then turn it on in `scripts/check.sh` and CI.
9. **Guide and close-out:** `CONTRIBUTING.md`, architecture doc, paths, full evals once.

### §7 Type errors

124 today. Each gets one of 3 outcomes: a type-only fix; an ignore with a written reason, for wrong library types; or, if the fix would change what the code does, a line in
`tasks.md` for the owner. Any that turn out to be real bugs are listed, not silently fixed.

### §8 Testing level

Level 1 on every step. Backend moves touch the agent's imports, so PR 2 also runs level 2: `scripts/evals_local.sh -k "care_ or refund"`, and a live `docker compose up`. Level 3 runs once, in PR 9.
The refund and starter measurements aren't needed: the prompt, policies and logic don't change.

## Dependencies (approved 2026-11-06, D-024)

All development only. Nothing reaches the app or AWS.

| Package | Why |
| ------- | --- |
| `pyright` | Type checks, Q3 |
| `pre-commit` | Hooks, Q5 |
| `@biomejs/biome` | Lint and format, see below |

### Why Biome

Q4 first chose ESLint and Prettier, but **`typescript-eslint` 8.72.1 supports TypeScript below 6.1, and this project uses TypeScript 7**. It's the piece that lets ESLint read TypeScript, so that choice is unsupported here.

- **Biome (chosen):** one tool for lint and format, with its own parser, so it doesn't depend on TypeScript's version. Also 1 package, not 4.
- **Downgrade TypeScript to under 6.1:** keeps ESLint, but moves the project backwards for a linter.
- **ESLint anyway:** relies on an unsupported pairing, and could break at any update.

## Files

| File | Change | Purpose |
| ---- | ------ | ------- |
| `src/shophelper/**` | move | §2, §3 |
| `tests/**`, `evals/test_integration*.py` | move, split | §4 |
| `tests/test_architecture.py` | new | Import rule, loose modules, frontend folders, `src/` paths in docs |
| `web/src/**` | move | §5 |
| `Dockerfile`, `docker-compose.yml`, `scripts/evals_local.sh`, `scripts/check.sh` | modify | Entry points and new checks |
| `.github/workflows/ci.yml` | modify | Frontend job |
| `.pre-commit-config.yaml`, `CONTRIBUTING.md`, lint config | new | Standards and the guide |
| `pyproject.toml`, `uv.lock`, `requirements.txt`, `web/package.json` | modify | Dev tools |
| `README.md`, `CLAUDE.md`, `docs/**`, `specs/architecture.md`, `specs/tech-stack.md`, `specs/testing-strategy.md` | modify | Paths and tools |

## Data Structures & Interfaces

```python
# tests/test_architecture.py
ALLOWED = {"core": set(), "shop": {"core"}, "accounts": {"core", "shop"}, "rag": {"core"}, ...}
def imports_of(path: Path) -> set[str]: ...   # ast walk, includes imports inside functions
```

New entry points: `shophelper.api.app:app`, `python -m shophelper.mcp.server --http`, `python -m shophelper.api.setup_local`.

## Techniques

- `git mv` in a commit with no content changes beyond paths keeps `git log --follow` working.
- A count of tests collected, before and after each move.
- The AWS image is checked with a local `docker build` only. Nothing is pushed or deployed.

## Test Approach

| AC | Test | Type |
| -- | ---- | ---- |
| AC-1, AC-2 | `tests/test_architecture.py`, with a sabotaged import that must fail | unit |
| AC-3 | `tests/test_architecture.py`: old folders are gone; review of the tree | unit + manual |
| AC-4 | Line count check, and collected test count before and after | unit |
| AC-5 | `CONTRIBUTING.md` read through | manual |
| AC-6 | Type check in `scripts/check.sh` and CI | unit |
| AC-7 | Lint and format in `scripts/check.sh` and CI | unit |
| AC-8 | Throwaway branch with a failing frontend test, then deleted | e2e |
| AC-9 | Timed commit of a small change | measurement |
| AC-10 | `scripts/check.sh` on every PR, level 3 once | unit + e2e |
| AC-11 | Clean rebuild, then a browser run: sign in, buy, chat | e2e |
| AC-12 | `git status infra`, `terraform validate`, `test_defaults_are_the_aws_path`, local `docker build` | unit |
| AC-13 | `tests/test_architecture.py`: every `src/` path in live docs exists | unit |
| AC-14 | PR list recorded in `tasks.md` | manual |

## Risks & Mitigations

- **The move breaks AWS in a way local tests miss.** Lazy imports and the `Dockerfile` entry point are the danger. `test_defaults_are_the_aws_path`, a local `docker build` and starting that image's app cover it. Real proof
  still needs a deploy, which waits for Phase 1.
- **`shophelper.mcp` shadowing the `mcp` library.** **Spike first**, in a throwaway branch: one module moved, with the MCP server started.
- **Type fixes could change behaviour.** §7 keeps those for the owner.
- **The stash for 022 goes stale.** Its plan says `web/src/learn/`, and its paths change. Updated when it's restored, before any of it is built.
- **A blank site after moves.** Restart `web` (learnings).
- **Size.** 9 PRs is a lot of ceremony for one person, but reviewable history is what this feature is for.

## Constitution Check

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Spec before code | ✅ | Refactors may skip a spec, but this has one anyway, updated first for Q1 and Q4 |
| II. Test-gated delivery | ✅ | Checks land first, and every PR passes them |
| III. Small dependencies | ✅ | Development tools only, approved by the owner (D-024) |
| IV. Memory maintained | ✅ | Decisions and learnings recorded |
| V. The model asks, code acts | ✅ | No logic changes |
| VI. AWS stays the default | ✅ | No setting changes, `__init__.py` files stay empty so imports stay lazy |
| VII. Local first | ✅ | Unchanged |
| VIII. Built to learn | ✅ | Becomes the Stage 6 lesson, with the real before and after |
| IX. Stream changes additive | ✅ | No stream changes |
