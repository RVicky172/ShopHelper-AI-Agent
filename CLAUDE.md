# CLAUDE.md

Guidance for Claude Code (and any AI agent) working in this repository.

## Project

**ShopHelper** — a customer-support AI agent inside a small fictional shop, built so its owner can learn how agents, RAG, MCP and tools really work.

## Start Every Session

1. Read `memory/MEMORY.md` (current state + active feature).
2. Read the newest entry in `memory/progress.md`.
3. Open the active feature in `specs/features/NNN-*/` and find the next unchecked task.
4. If the task touches principles, re-read `specs/constitution.md`.

## Spec-Driven Workflow (mandatory)

**Specify → Plan → Tasks → Implement → Verify.** Full rules: `specs/workflow.md`.

- Never write feature code without an **Approved** `spec.md`. If none exists, draft one and stop for review.
- Never plan from a spec that still has `[NEEDS CLARIFICATION]` markers — ask the user.
- Work one task from `tasks.md` at a time; tick it only after its tests pass.
- If code must diverge from the spec, update the spec (and its Changelog) first.
- Slash commands: `/spec-new`, `/spec-plan`, `/spec-tasks`, `/spec-implement`, `/spec-verify`.

## Key Docs

| Doc                         | Read when                                               |
| --------------------------- | ------------------------------------------------------- |
| `specs/constitution.md`     | Before any design decision; contains Definition of Done |
| `specs/architecture.md`     | Before touching shared code or adding a module          |
| `specs/tech-stack.md`       | Before adding any dependency                            |
| `specs/testing-strategy.md` | Before writing tests                                    |
| `memory/MEMORY.md`          | First, in every session                                 |
| `memory/learnings.md`       | Before debugging, or working on Docker, RAG or evals    |
| `memory/decisions.md`       | Before reversing or revisiting an earlier choice        |
| `specs/roadmap.md`          | Choosing what's next                                    |

## Hard Rules

- **Don't deploy to AWS or create paid resources** unless the user asks in that session.
- **AWS stays the default.** New settings must not change deployed behaviour (Constitution VI).
- **The model asks, code acts.** Never put a state-changing tool on the MCP server (Constitution V).
- After changing Python dependencies, re-export `requirements.txt` (see `specs/tech-stack.md`).

## Run It

`lms server start`, then `docker compose up --build`. App: http://localhost:5173, pgAdmin: http://localhost:5050.
Full guide: `docs/reference/local-setup.md`. `docs/` is written for learners; `specs/` and `memory/` are for this workflow.

## Commands

```bash
scripts/check.sh                         # fast gate — must pass before any task is ticked
uv run pytest && (cd web && npm test)    # unit tests only
scripts/evals_local.sh                   # end-to-end; needs docker compose up + LM Studio; EVAL_RUNS=3 repeats it
cd web && npm run build                  # production build
uv run ruff check --fix src tests evals  # format
```

`scripts/check.sh` must pass before any task is marked done.

## Memory Management (project memory in `memory/`)

Full rules: `specs/memory-management.md`.

- **Decision made** (library, pattern, spec change) → append to `memory/decisions.md` right away.
- **Gotcha found** (lost >10 min, non-obvious fix) → add to `memory/learnings.md`.
- **End of session** → add an entry to `memory/progress.md` and update "Current State" in `memory/MEMORY.md`.
- Shared project knowledge goes in `memory/` (committed). Personal agent memory is only for one user's
  preferences — never the only place a project fact lives.
- Use absolute dates. Fix or delete memory that becomes wrong.

## Git

- Commit and push only when asked. Conventional-style messages referencing the feature: `feat(012): add login form`.
- Run `scripts/check.sh` before committing.
