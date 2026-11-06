# Progress Log

Newest first. One entry per working session.

```
## YYYY-MM-DD — <feature id or "chore">
**Done:** …
**Next:** …
**Blockers:** …
```

---

## 2026-11-06 — 022: stage 6, building the app

**Done:** 7 lessons, replacing the 3 carried chapters. One timed turn: first event 2.07 s, first token 2.33 s, search 0.04 s, total 4.86 s.
Gaps stated in the lessons: no `Secure` cookie flag locally, no migrations tool, no rate limits, one layer of isolation.
**Next:** `/spec-implement 022`, from T203: stage 7, evals.
**Blockers:** none

## 2026-11-06 — 022: stage 5, RAG

**Done:** 9 lessons, replacing the carried RAG chapter. Measured on this project: reranking the top 8 took right-first from
17 to 20 of 20; hybrid search and query prefixes showed no gain on 24 chunks; HNSW index unused at 24 rows; on 50,000 random
vectors, exact 85 ms, HNSW 2.2 to 4.5 ms, recall@10 0.28 to 0.60. Try it steps run live, including the Care price change.
**Next:** `/spec-implement 022`, from T200: slice 3, production.
**Blockers:** none

## 2026-11-06 — 022 slice 1 done

**Done:** The course at `/learn`: right-hand stepper, lessons, quizzes, search, progress. Docs reorganised into stages. 15 lessons so far, 5 at final quality. Owner approved the style.
**Next:** Slice 2, stages 1 to 5.
**Blockers:** none

## 2026-11-06 — 031 Implemented

**Done:** Backend and frontend organised by feature, tests mirror the code, imports enforced one way. Pyright 124 errors to 0, Biome, pre-commit, frontend CI. 8 PRs (4 to 11, without
the throwaway PR 3). Evals 37 of 37, 366 backend, 82 frontend. No behaviour changed, and no real bugs found.
**Next:** 022. Restore its planning from `git stash` on `feat/022-learning-website`, rebase on `main`, and move its site to `web/src/features/learn/`.
**Blockers:** none

## 2026-11-06 — 030 Implemented

**Done:** Code searches first on Care and warranty questions: 48 of 48, up from 30 of 48. Evals 37 of 37, 354 backend, 82 frontend. 13 of 13 criteria.
**Known bug:** The agent can wrongly refuse a refund when the customer mentions a warranty (D-023), now in the backlog.
**Next:** Owner merges 030. Then 031 code structure, then 022, whose planning is in `git stash` on `feat/022-learning-website`.
**Blockers:** none

## 2026-11-06 — 030 paused for the learning website

**Done:** Code searches first on Care and warranty questions: 48 of 48 searched, up from 30 of 48, all answers correct. Three test levels
adopted (D-020, Constitution 1.1.0). 14 of 21 tasks done.
**Open:** AC-9 at 59 of 60 needs the owner's call (T033). One clean full eval run (T030): the last was stopped, the one before had one rare
failure. Then T041, T042, T090 to T092.
**Blockers:** Owner put the learning website first. Nothing is lost: the work sits uncommitted on the branch.

## 2026-11-06 — 021 Implemented

**Done:** Owner accepted the Care gap (D-016) and cut evals to 1 run, with `EVAL_RUNS` to repeat them (D-017). All gates pass: 331 backend,
82 frontend, build, evals 90 of 90, refunds 60 of 60, starters 57 of 57. 42 of 42 criteria ticked. Everything merged through PR 1.
**Next:** Merged to `main` through PR 1. Owner chooses 022 or the Care fix from the backlog.
**Blockers:** none locally. Phase 1 needs the Anthropic form.

## 2026-11-06 — 021 Care decision: T094 reopened

**Done:** Owner chose Care for electronics only and kept the trace page's chat (D-015). Spec, policy, both prompts and 2 eval cases
changed, policy re-embedded. `scripts/check.sh` passes, evals 90 of 90 in 1 run.
**Found:** Only 12 of 24 Care questions searched the policy, so the agent still makes up or dodges the answer on 4 of 8 wordings.
**Next:** Owner chooses how to fix that. Then 3 eval runs, refunds 60 of 60, T095.
**Blockers:** Owner's choice on the fix.

## 2026-11-06 — 021 T094 done

**Done:** `scripts/check.sh` (331 backend, 82 frontend) and the build pass. Evals 3 runs, each 88 of 88 (31 golden, 57 integration),
faithfulness 5.0. Demo data clean afterwards.
**Next:** T095, once the owner has answered.
**Blockers:** Owner's two answers: does ShopHelper Care cover lifestyle products, and does the trace page keep its chat.

## 2026-11-04 — 021 T091 to T093 done, T094 started

**Done:** Clean rebuild, the whole story in a browser 17 of 17, AWS mode returns 404, architecture contracts updated.
**Stopped:** The owner stopped the evals during run 1 of 3, and the containers, with `docker compose stop`. Data is kept.
**Next:** `lms server start`, `docker compose up -d`, then T094's 3 eval runs.
**Blockers:** Owner's two answers, for T095 only: ShopHelper Care for lifestyle products, and whether the trace page keeps its chat.

## 2026-11-04 — 021 T090: measurements done

**Done:** LCP at most 1.87 s on a slow phone profile, CLS at most 0.074. axe clean bar one artefact, after 8 real fixes. A purchase by
keyboard alone works.
**Next:** T091, the full browser run on an upgraded database and a clean rebuild.
**Blockers:** Owner's two answers, for T095 only.

## 2026-11-04 — 021 T081: critique done

**Done:** All pages reviewed in both themes. Old colour names gone, staff pages aligned, shopper wording cleaned up.
**Next:** T090, performance and accessibility numbers on a production build.
**Blockers:** none

## 2026-11-04 — 021 T080: docs done

**Done:** Learner docs and README describe the shop. 157 links, 22 diagrams and 16 Try it steps checked.
**Next:** T081, the design critique.
**Blockers:** none

## 2026-11-04 — 021 chat widget: T070 to T074 done

**Done:** Chat button, panel, starters, nudge, trace link. AC-25 measured, 0 overlaps. The page now scrolls in `#page` (D-013). The policies
define electronics (D-014). Evals 31 of 31 in 3 runs, refunds 60 of 60, starters 57 of 57. All browser checks rerun and passing.
**Next:** T080, the docs.
**Blockers:** none

## 2026-11-04 — 021 T062: all 42 illustrations drawn

**Done:** The other 34 drawings, checked against the tokens and reviewed in both themes.
**Next:** T070, the chat button.
**Blockers:** none

## 2026-11-04 — 021 cart pages: T060, T061, T063 to T065 done

**Done:** Cart logic, guest and signed-in carts, merge, cart and checkout pages, Mark delivered. Browser run 39 of 39, twice, with 2 of 2
sabotage checks caught. Demo data restored to 7 orders and empty carts.
**Next:** T062, the other 34 illustrations.
**Blockers:** none

## 2026-11-04 — 021 shop pages: T050 to T053 done

**Done:** Product grid, landing, category and product pages, return policy page. Browser run 40 of 40. CLS at most 0.057.
**Next:** T060, `cartLogic.ts`. T062 can run at any time and would fill the blank tiles.
**Blockers:** none

## 2026-11-04 — 021 frontend shell: T040 to T044 done

**Done:** `ChatProvider`, routes, navbar, account menu, footer, public landing stub, safe `next`, How it works. Browser run 55 of 55.
A stream survives moving between URLs, proven with a sabotage check.
**Next:** T050, the product grid.
**Blockers:** none

## 2026-11-04 — 021 agent and policies: T030 to T032 done

**Done:** General store wording, lifestyle terms, 3 new eval cases. Evals 30 of 30 in 3 full runs. Refunds 60 of 60 interleaved.
**Next:** T040, the frontend shell. Owner to say whether ShopHelper Care covers lifestyle products.
**Blockers:** none

## 2026-11-04 — 021 cart and orders backend: T020 to T025 done

**Done:** Carts, merge, checkout and Mark delivered, in memory and Postgres. 15 of 15 sabotage checks caught. A bought order went
through the real agent from lookup to refund, 4 of 4 runs. Evals 27 of 27, integration 56 of 56, unit 263.
**Next:** T030, the general store wording and policies.
**Blockers:** none

## 2026-11-04 — 021 catalogue backend: T010 to T014 done

**Done:** 42 products, `ProductRepo` in memory and Postgres, public read routes, `is_public` for GET only. 4 of 4 sabotage checks
caught. Postgres matches the in-memory repo, and the real database upgraded in place.
**Next:** T020, the cart.
**Blockers:** none

## 2026-11-04 — 021 setup: T001 to T003 done

**Done:** 8 illustrations in `web/public/products/`, in both themes, with contrast measured. `scripts/check.sh` passes.
**Also:** Owner approved the style, so T001 is ticked and T062 is unblocked. Solid shapes still invert in dark mode.
**Also:** T002 packages added, and T003 design tokens in both themes, with all contrast pairs passing. The app works on the new
palette and font. `package.json` changes need `docker compose up --build -V web`.
**Next:** T010, the catalogue backend.
**Blockers:** none

## 2026-11-04 — 020 Implemented

**Done:** AC-6 narrowed (D-010), AC-29 proven by the owner, 29 of 29 criteria ticked, all gates pass.
**Also:** A failing eval exposed false refund promises (0 of 20 on one wording). Fixed in `graph.py`, now 60 of 60.
**Next:** 021 storefront.
**Blockers:** none

## 2026-11-04 — 020 verify: not yet Implemented

**Done:** All gates pass. 27 of 29 acceptance criteria proven and ticked. AC-8 wording aligned with the approved plan.
**Next:** Owner decides AC-6, and tries the Inspector steps for AC-29. Then rerun `/spec-verify 020`.
**Blockers:** AC-6 needs the owner's decision.

## 2026-11-04 — 020 accounts: backend started

**Done:** Spike, settings, sign-up, login, sessions, lockout, login gate, admin routes; in-memory backends only.
90 backend tests pass, and four sabotage checks were caught.
**Also done:** Tables, Postgres accounts, demo seeding, integration tests. Real database upgraded in place.
**Also done:** Isolation: orders, MCP identity, refunds and conversations, with 10 of 10 sabotage checks caught.
**Also done:** Staff refund queue and role rules, with 16 of 16 sabotage checks caught. A real refund ran end to end.
**Also done:** 7 cross-user evals, 27 of 27. With the owner checks removed, all 7 attacks succeeded.
**Also done:** Frontend: login, sign-up, tabs by level, conversations, refund queue, users. 4-person browser run passed.
**Also done:** Chapter 11, and older docs updated with their exercises re-run, except the Inspector steps.
**Also done:** Clean rebuild, AWS checks and all gates pass.
**Next:** AC-6 decision, then `/spec-verify 020`.
**Blockers:** none. T002 closed: the slow build was the ISP's IPv4 route to PyPI, not Docker.

## 2026-11-04 — 000 baseline: local stack, React UI, docs

**Done:** Docker stack (Postgres + pgvector, pgAdmin, MCP, API, web), LM Studio models, streaming UI, local
guardrails, learning docs. Evals 20/20 after a clean rebuild. Terraform unchanged and valid.
**Next:** The user reviews and commits. AWS retest is listed in `docs/next-steps.md`.
**Blockers:** Anthropic use-case form, for AWS only.

## 2026-11-04 — chore: spec-driven development set up

**Done:** `specs/` (constitution, workflow, roadmap, tech stack, architecture, testing strategy, templates),
`memory/`, `/spec-*` commands, CLAUDE.md, and `scripts/check.sh` as the single fast gate (D-001).
**Next:** see `MEMORY.md` → Next step.
**Blockers:** none
