# 031 — Code Structure and Standards · Tasks

**Plan:** `./plan.md`
Legend: `[P]` = can run in parallel with the previous task. Each task lists files and the proving test.
Test-first: each "tests" task must fail before its paired implementation makes it pass.
When a task is done, tick it and add an indented **Result (YYYY-MM-DD):** note: what was done, numbers measured,
anything surprising or deferred.

Every PR passes `scripts/check.sh`. The owner approved committing, pushing and merging each PR once its checks pass (D-024). Stop for anything that fails,
needs a decision, or would change behaviour.

## PR 1 — Safety net

- [x] **T001** — Spike, thrown away afterwards: move `mcp_client` into `shophelper/mcp/`, start the MCP server, and confirm the `mcp` library still imports · test: server
      starts, `tests/test_mcp.py` passes
      **Result (2026-11-06):** `shophelper.mcp` beside the `mcp` library works: both import correctly and the server starts. The copy was removed.
- [x] **T002** — Record the baseline: tests collected, lines per test file, Pyright errors · test: numbers recorded here
      **Result (2026-11-06):** 354 unit tests, 94 eval tests. Largest test files: `test_shop.py` 653 lines, `evals/test_integration.py` 589. Pyright: 124 errors.
- [x] **T003** — Add `pyright`, `pre-commit` and Biome, with `requirements.txt` re-exported if needed and the stack doc updated · files: `pyproject.toml`, `uv.lock`, `web/package.json`,
      `specs/tech-stack.md` · test: `scripts/check.sh`
      **Result (2026-11-06):** Added `pyright` 1.1.414, `pre-commit` 4.7.0 and `@biomejs/biome` 2.6.4, all development only. `requirements.txt` unchanged.
- [x] **T004** — `tests/test_architecture.py`: import rule, `src/` paths in docs. Rule table inactive until the folders exist. Sabotage each check · files: `tests/test_architecture.py` · test:
      each check fails when broken
      **Result (2026-11-06):** 8 tests. Each check has its own test proving it fails. Live docs currently have no broken paths.
- [ ] **T005** — Frontend CI job: tests, types and build. Prove it with a failing test on a throwaway branch, then delete the branch · files: `.github/workflows/ci.yml` · test: the job fails, then passes
- [ ] **T006** — Merge PR 1

## PR 2 — Backend moves

- [ ] **T010** — Cycle fixes, in their own commit: `Principal` to `identity.py`, split `ChatResponse` from the request models · files: `src/shophelper/` · test: `scripts/check.sh`
- [ ] **T011** — Move script: `git mv`, import rewrites, `ruff --fix`, one commit of paths only · files: `src/shophelper/**`, `tests/**`, `evals/**` · test: same test count, `scripts/check.sh`
- [ ] **T012** — Fix `__file__` paths and entry points · files: `Dockerfile`, `docker-compose.yml`, `scripts/evals_local.sh`, moved modules · test: `docker compose up --build`, `/health`
- [ ] **T013** — Turn on the import rule and "no loose modules". Sabotage: add a forbidden import · files: `tests/test_architecture.py` · test: it fails, then passes
- [ ] **T014** — Level 2 and AWS check: `scripts/evals_local.sh -k "care_ or refund"`, `test_defaults_are_the_aws_path`, `terraform validate`, local `docker build`. Nothing pushed or deployed · test: all pass
- [ ] **T015** — Update `src/` paths in live docs · files: `README.md`, `CLAUDE.md`, `docs/**`, `specs/architecture.md`, `specs/*.md` · test: path check
- [ ] **T016** — Merge PR 2

## PR 3 — Test layout

- [ ] **T020** — Move tests into folders that mirror the code · files: `tests/**` · test: same test count
- [ ] **T021** — Split `test_shop.py` along its sections, and `evals/test_integration.py` the same way, all under 400 lines · files: `tests/shop/`, `evals/` · test: same test count, line check
- [ ] **T022** — Merge PR 3

## PR 4 — Frontend moves

- [ ] **T030** — Move to `features/` and `shared/`, one commit of paths only, then restart `web` · files: `web/src/**`, `tests/` · test: 82 frontend tests, typecheck, build
- [ ] **T031** — Add the old-folders check · files: `tests/test_architecture.py` · test: fails on a recreated `views/`
- [ ] **T032** — Browser run: sign in, buy, chat, staff pages, How it works, with failed responses listed by URL · test: recorded here
- [ ] **T033** — Merge PR 4

## PR 5 — Lint and format

- [ ] **T040** — Biome config, and fix what the lint rules find, listing anything that would change behaviour · files: `web/biome.json`, `web/src/**` · test: lint passes
- [ ] **T041** — The mechanical reformat, as its own commit · files: `web/src/**` · test: 82 frontend tests, build
- [ ] **T042** — Add to `scripts/check.sh` and CI · files: `scripts/check.sh`, `.github/workflows/ci.yml` · test: a formatting slip fails
- [ ] **T043** — Merge PR 5

## PR 6 — Pre-commit

- [ ] **T050** — Hooks for ruff and Biome, with install steps in the docs · files: `.pre-commit-config.yaml`, `docs/` · test: a bad commit is refused; a small commit takes under 10 s (AC-9)
- [ ] **T051** — Merge PR 6

## PR 7 — Type checks, part 1

- [ ] **T060** — Pyright config, then fix `core` and `rag` · files: `pyproject.toml`, `src/shophelper/core/`, `rag/` · test: 0 errors there
- [ ] **T061** — Fix `shop` · files: `src/shophelper/shop/` · test: 0 errors there
- [ ] **T062** — Fix `accounts` · files: `src/shophelper/accounts/` · test: 0 errors there
- [ ] **T063** — Merge PR 7

## PR 8 — Type checks, part 2

- [ ] **T070** — Fix `agent` · files: `src/shophelper/agent/` · test: 0 errors there
- [ ] **T071** — Fix `mcp` and `api` · files: `src/shophelper/mcp/`, `api/` · test: 0 errors in `src/`
- [ ] **T072** — Add to `scripts/check.sh` and CI, and list any real bugs found · files: `scripts/check.sh`, `.github/workflows/ci.yml` · test: a type error fails
- [ ] **T073** — Merge PR 8

## PR 9 — Guide and close-out

- [ ] **T090** — `CONTRIBUTING.md`: what each folder is for, where new code goes, the layers, how PRs work · files: `CONTRIBUTING.md` · test: read through
- [ ] **T091** — Update `specs/architecture.md` with what this feature established.
- [ ] **T092** — Clean rebuild and browser run, in the background where possible · test: recorded here (AC-11)
- [ ] **T093** — Every Definition-of-Done gate green (`specs/constitution.md`), level 3 once; record the numbers.
- [ ] **T094** — Tick ACs in `spec.md` (Status `Implemented`), list the PRs, update `roadmap.md`, `memory/progress.md`, `memory/MEMORY.md`. Merge PR 9.

## AC coverage

| AC    | Tasks            |
| ----- | ---------------- |
| AC-1  | T011, T013       |
| AC-2  | T004, T013       |
| AC-3  | T030, T031       |
| AC-4  | T020, T021       |
| AC-5  | T090             |
| AC-6  | T060 to T072     |
| AC-7  | T040, T041, T042 |
| AC-8  | T005             |
| AC-9  | T050             |
| AC-10 | every PR, T093   |
| AC-11 | T012, T032, T092 |
| AC-12 | T014             |
| AC-13 | T004, T015       |
| AC-14 | T094             |
