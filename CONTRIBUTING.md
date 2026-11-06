# Contributing

How this project is organised, and how a change gets in.

## Where things live

| Folder | What it's for |
| ------ | ------------- |
| `src/shophelper/` | The backend, grouped by feature |
| `web/src/` | The React app, grouped by feature |
| `tests/` | Offline tests, mirroring `src/shophelper/` |
| `evals/` | Tests against the real model and database |
| `knowledge/policies/` | The documents the agent searches |
| `infra/` | Terraform for AWS |
| `scripts/` | Checks, evals and AWS deployment |
| `docs/` | Written for people learning from this project |
| `specs/`, `memory/` | How work is planned, and what's been decided |

## Where new code goes

### Backend

| Folder | Put here | May import |
| ------ | -------- | ---------- |
| `core/` | Settings, database access, logging, identity | Nothing else |
| `shop/` | Catalogue, cart, orders, refunds | `core` |
| `accounts/` | Users, sessions, conversations | `core`, `shop` |
| `rag/` | Chunking, embedding, search | `core` |
| `agent/` | The agent loop, tools, memory, guardrails | `core`, `shop`, `accounts`, `rag` |
| `mcp/` | The MCP server and client | `core`, `shop`, `accounts`, `agent` |
| `api/` | HTTP routes, request models, entry points | Everything |

Imports point one way, so a change low down can't be broken by something above it. `tests/test_architecture.py` enforces this.

Ask what a piece of code is about, not what kind of code it is. A new shop rule goes in `shop/`, even if a route calls it. If two folders need the same thing, it probably
belongs lower down.

`data/` holds seed files, and stays there because Terraform reads `orders.json`.

Local-only packages such as `psycopg` are imported inside functions, so AWS never loads them. Keep `__init__.py` files empty for the same reason.

### Frontend

- `web/src/features/<feature>/`: everything for one feature, tests included.
- `web/src/shared/`: what several features use: the API client and the page layout.

### Tests

A test goes in the `tests/` folder that matches the code. Keep test files under 400 lines.

## Standards

| Check | Tool | Runs |
| ----- | ---- | ---- |
| Python lint | ruff | Before each commit, `scripts/check.sh`, CI |
| Python types | Pyright | `scripts/check.sh`, CI |
| Frontend lint and format | Biome | Before each commit, `scripts/check.sh`, CI |
| Frontend types, tests and build | TypeScript, Vitest, Vite | `scripts/check.sh` (build separately), CI |
| Folder rules, doc paths | `tests/test_architecture.py` | `scripts/check.sh`, CI |

Run `uv run pre-commit install` once per clone.

A type ignore needs a reason on the line above. A test fails without one.

## Making a change

1. **Spec first.** New behaviour needs an approved spec. See `specs/workflow.md`.
2. **Test first** where you can, and see the test fail.
3. **Run the cheapest check that can catch the problem.** `specs/testing-strategy.md` has the 3 levels.
4. **Keep pull requests small.** One idea each.
5. **Never mix a move with a change.** A commit that moves files changes only paths and imports, so a reviewer can trust it and `git log --follow` keeps working.

Commit messages name the feature: `feat(012): add login form`.
