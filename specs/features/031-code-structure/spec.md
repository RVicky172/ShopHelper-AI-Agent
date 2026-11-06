# 031 — Code Structure and Standards

**Status:** In Progress
**Roadmap phase:** Backlog · **Created:** 2026-11-06 · **Owner:** RVicky172

## Summary

The code is small and well tested, but its structure hasn't kept up. All 25 Python modules sit in one folder, the frontend mixes two ways of organising
files, and several standards rely on people remembering them. This feature organises both sides by feature, so anyone can tell where something lives,
and makes the standards automatic. Nothing the app does changes. It comes before 022, because the course quotes real file paths.

## User Stories

- **US-1:** As a developer, I want the folders to show what the system does, so that I can find any feature quickly.
- **US-2:** As a developer, I want checks to run by themselves, so that standards don't depend on memory.
- **US-3:** As a reviewer, I want small changes, so that each one can really be reviewed.
- **US-4:** As a job seeker, I want to explain how and why this project was restructured, so that I can answer an interviewer with real experience.

## Acceptance Criteria

### Structure

- [ ] **AC-1:** Backend code is grouped by feature, with no module left loose in the package except the package marker. Each folder's purpose is stated in
      one line. _(unit)_
- [ ] **AC-2:** Dependencies point one way: shared code imports no feature, and a test fails if a forbidden import appears. _(unit)_
- [ ] **AC-3:** Frontend code is grouped by feature, with one shared area, and the separate `views/`, `shop/` and `components/` split is gone. _(manual review + unit)_
- [ ] **AC-4:** The backend tests mirror the code's folders, and no test file is over 400 lines. The test count doesn't fall. _(unit)_
- [ ] **AC-5:** A short document says where new code goes, and what each top-level folder is for. _(manual)_

### Standards that run by themselves

- [ ] **AC-6:** A Python type checker passes on all of `src/`, and runs in `scripts/check.sh` and CI. Any ignored error has a written reason. _(unit)_
- [ ] **AC-7:** Frontend linting and formatting pass, and run in `scripts/check.sh` and CI. _(unit)_
- [ ] **AC-8:** CI runs the frontend's tests, type check and production build on every pull request. A failing frontend test fails the pipeline. _(e2e, proved with a
      deliberate failure on a throwaway branch)_
- [ ] **AC-9:** Lint and format checks run before each commit, and take under 10 seconds on a small change. _(measurement)_

### Nothing changes

- [ ] **AC-10:** All existing tests pass after every step, with the same behaviour: 354 backend and 82 frontend, plus any added. Evals pass 37 of 37 once, at the end.
      _(unit + e2e)_
- [ ] **AC-11:** `docker compose up` works after a clean rebuild, and `/health`, sign-in, a purchase and a chat all work in a browser. _(e2e)_
- [ ] **AC-12:** The AWS path is intact: `infra/` needs no edits beyond entry point or path updates, `terraform validate` passes, and
      `test_defaults_are_the_aws_path` passes. Nothing is deployed. _(unit)_
- [ ] **AC-13:** Every path in live docs, specs and scripts is correct, and a test fails on a `src/` path that doesn't exist. Finished feature specs stay as written. _(unit)_
- [ ] **AC-14:** The work merges as at least 5 pull requests, none over about 40 files of real change. A pure file move can be larger if nothing else changes in it.
      _(manual)_

## Non-Functional Requirements

- Moves and behaviour never mix: a commit that moves files changes only paths and imports.
- No new runtime dependency. New tools are development only, and need a `specs/tech-stack.md` entry.
- History stays traceable: `git log --follow` works on a moved file.

## Out of Scope

- Rewriting logic, or splitting large functions.
- Fixing the warranty refund bug (D-023), or any other behaviour.
- Moving `docs/`: 022 does that.
- A browser test suite such as Playwright, which stays in the backlog.
- A monorepo tool, or splitting into separate repositories.

## Open Questions

All answered by the owner on 2026-11-06, who accepted the proposals.

- **Q1** Is this the right backend layout? _Answer:_

  ```
  src/shophelper/
    core/       config, db, observability, schema.sql, identity and Principal
    agent/      graph, service, tools, memory, guardrails, raw_agent, ChatResponse
    rag/        ingest and search
    mcp/        client, server
    accounts/   auth, conversations
    shop/       catalog, cart, orders, refunds
    api/        the app, routes for auth, shop and local, request models, setup_local
    data/       stays put, because Terraform reads orders.json from here
  ```

  The package name stays `shophelper`, and the root stays `src/`.
- **Q2** Is this the right frontend layout? _Answer:_

  ```
  web/src/
    features/   chat, cart, auth, shop, staff, how-it-works
    shared/     api client, layout, common components
  ```

  022 then adds `features/learn/`, not `web/src/learn/`.
- **Q3** How strict should type checking be? _Answer:_ Pyright at its default level, with `strict` only for new code later. Today it reports 124 errors, led
  by `graph.py` (26) and `auth.py` (18): many are values that may be `None`, and some come from library types. Each is fixed, or ignored with a written reason, in its own
  pull requests, after the moves. A fix that would change behaviour is listed for the owner, not slipped in.
- **Q4** Which frontend tools? _Answer:_ Biome, one tool for lint and format. ESLint was first choice, but `typescript-eslint` doesn't support TypeScript 7 (D-024).
- **Q5** Which pre-commit tool? _Answer:_ the `pre-commit` framework, for ruff and frontend format, with slow checks left to `scripts/check.sh`. It's
  the usual choice in Python projects, and handles both languages.
- **Q6** Does `raw_agent.py` stay? _Answer:_ yes, in `agent/`. It's the comparison that shows what a framework does for you, and it costs little.
- **Q7** What about loose root files? _Answer:_ leave them. `Dockerfile`, `docker-compose.yml`, `pyproject.toml` and `README.md` belong at the root, and
  `build/` and the `.docx` are ignored by git, so they aren't in the repo. Delete them from your disk only if you no longer want them.

## Changelog

- 2026-11-06 — Created, from the owner's concern about structure. Comes before 022.
- 2026-11-06 — Questions answered and spec Approved.
- 2026-11-06 — Plan approved. Biome replaces ESLint and Prettier, and Q1 changes to avoid 2 import cycles (D-024).
