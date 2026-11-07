# Project Memory — Index

> Read this first every session. Keep ≤ 40 lines. Rules: `specs/memory-management.md`.

## Current State (2026-11-07)

- **Phase:** 2. Features 020 (accounts) and 021 (storefront) Implemented. Local stack works: `docker compose up` plus LM Studio. Evals 37/37.
- **Git:** PR #23 (022 stages 11 and 12, sign-in fix) is pushed and CI passed, waiting for the owner to merge. The merge was blocked as unreviewed, so don't retry it. `feat/032-slice-1` is stacked on it, with slice 1 uncommitted.
- **AWS:** torn down on 2026-11-01. Don't deploy unless asked.
- **Active feature:** 022 learning website, In Progress: 48 of 53 tasks, T390 in the backlog (D-026), all 13 stages and 81 lessons written, question bank built (D-021). Stages 11 and 12 and the bank aren't committed yet. Containers are running.
- **Next step:** `/spec-implement 022`, from T391: request hosts with LM Studio stopped. Known bugs: warranty refunds (D-023), MCP one version behind (backlog).
- **Next feature:** 032 fluid glass redesign, In Progress: slice 1 built, stopped at T007 for the owner's review of the look.
- **Blockers:** none locally. Phase 1 needs the Anthropic form.

## Files

- [decisions.md](decisions.md) — append-only decision log (why we chose X)
- [progress.md](progress.md) — session log, newest first
- [learnings.md](learnings.md) — gotchas and non-obvious fixes
