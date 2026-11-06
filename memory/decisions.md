# Decision Log

Append-only. Newest at the bottom. To reverse a decision, add a new entry that says `Supersedes D-00X`.

Format:

```
## D-00X — Title (YYYY-MM-DD)
**Context:** … **Decision:** … **Alternatives:** … **Consequences:** …
```

---

## D-001 — Adopt spec-driven development (2026-11-04)

**Context:** Work is done across many sessions, by people and AI agents that don't remember earlier sessions.
**Decision:** Every feature goes Specify → Plan → Tasks → Implement → Verify (`specs/workflow.md`), gated by the
Definition of Done in `specs/constitution.md`; durable project memory lives in the committed `memory/` folder.
**Alternatives:** ad-hoc issues/PR descriptions only; an external tracker.
**Consequences:** Specs and memory are part of every feature's diff; `/spec-*` commands drive the stages.

## D-002 — Earlier AWS stack choices (2026-11-01)

**Context:** The project had to be cheap and fully removable after testing.
**Decision:** Terraform for all infrastructure, LangGraph for the agent, Bedrock Knowledge Base on S3 Vectors,
Haiku as agent with Sonnet as judge, region `ap-south-1`.
**Alternatives:** SAM or CDK; OpenSearch Serverless (about $12 a day idle).
**Consequences:** Everything goes with one `terraform destroy`. Recorded here after the fact, as a summary.

## D-003 — Work local-first, with AWS staying the default (2026-11-04)

**Context:** Bedrock Claude is blocked on the use-case form, and the user wants everything working locally first.
**Decision:** Local behaviour is opt-in through settings. Defaults and `infra/` keep the AWS path unchanged.
**Alternatives:** A separate local codebase; making local the default and changing deployed settings.
**Consequences:** One codebase and one image. Each backend has to honour the same contract.

## D-004 — LM Studio for local models (2026-11-04)

**Context:** The user already had `qwen/qwen3-30b-a3b-2507` and a nomic embedding model in LM Studio.
**Decision:** Use LM Studio on the host, reached at `host.docker.internal:1234` through its OpenAI-compatible API.
**Alternatives:** Ollama in Docker with GPU access, which was the first plan until the user asked for LM Studio.
**Consequences:** LM Studio is the one piece outside Docker and must be started first.

## D-005 — Postgres holds all local state (2026-11-04)

**Context:** The user asked for embeddings in a Docker database. Separately, the MCP server is its own process,
so in-memory orders meant it could not see refunds.
**Decision:** Embeddings, orders, history and checkpoints all live in Postgres with pgvector, browsed in pgAdmin.
**Alternatives:** Only embeddings in Postgres, with the rest in memory; a dedicated vector database.
**Consequences:** One thing to run and inspect. Paused refunds survive restarts.

## D-006 — Run the API in Docker, and MCP as its own HTTP container (2026-11-04)

**Context:** Async psycopg and subprocess-based stdio MCP need different event loops on Windows. An MCP service
you can see, restart and connect to also teaches more.
**Decision:** The API runs in Linux containers, and MCP uses streamable HTTP locally. ECS keeps stdio.
**Alternatives:** Running uvicorn on the Windows host.
**Consequences:** Local work goes through Docker. Host runs are limited to tests and `scripts/evals_local.sh`.

## D-007 — SSE over fetch, with a hand-written stream client (2026-11-04)

**Context:** The UI needs tokens and custom step events on a POST endpoint.
**Decision:** SSE using `fetch` and eventsource-parser, with all logic in one pure reducer.
**Alternatives:** WebSockets (two-way isn't needed); `EventSource` (GET only); Vercel AI SDK (hides the mechanics).
**Consequences:** About 30 lines of stream code to own, and the stream logic can be tested without a browser.

## D-008 — Accounts built in-project, local only, with three levels (2026-11-04)

**Context:** Feature 020 needs sign-up, login and per-user isolation. The owner accepted all six proposals in its spec.
**Decision:** Build accounts here with standard hashing libraries. Levels are Customer, Support, Admin, with Admin as
the supervisor for refunds over $200. AWS gets no accounts in this feature. UI and learning work are features 021, 022.
**Alternatives:** An identity server (Keycloak, Cognito, Auth0); a fourth supervisor level; one combined feature.
**Consequences:** Every step of auth can be read. The deployed API stays unauthenticated, so it must not be hosted
publicly until a later Cognito feature.

## D-009 — Plan choices for feature 020 (2026-11-04)

**Context:** The plan for 020 raised three decisions. The owner declined Playwright, then ran `/spec-tasks 020` without
answering the other two, which was taken as accepting the recommended answers.
**Decision:** Add `argon2-cffi`, and make `pyjwt` a direct dependency. No Playwright in the repo yet: UI checks are
manual. No Postgres row-level security yet: it goes to the backlog.
**Alternatives:** Hand-written hashing (unsafe); committed browser tests; row-level security from the start.
**Consequences:** UI regressions won't be caught automatically until browser tests are added.

## D-010 — AC-6 covers sign-up and login; chat is a documented limit (2026-11-04)

**Context:** Verify found that "please remember X as my password" passes the regex guardrail and X is stored. AC-6 said
passwords never appear in history or checkpoints, but no filter can identify a password in free text.
**Decision:** Option A: AC-6 covers passwords entered at sign-up and login. Passwords typed into chat are a documented
limit in chapters 8 and 11. The owner accepted the recommendation when answering feature 021's Q5.
**Alternatives:** B, widen the regex (guesswork, risks blocking normal questions). C, compare words in each message with
the user's stored hash (catches their real password, but adds slow hashing to every chat).
**Consequences:** The account system stays clean. A user who pastes a password into chat can still have it stored.

## D-011 — The shop is public, and sells more than electronics (2026-11-04)

**Context:** Feature 021 opens on products with no login, and adds lifestyle products at the owner's request.
**Decision:** Signed-out visitors can browse and fill a cart, which changes 020's AC-22, and product and category reads are
public, which changes 020's AC-8. Everything else still needs a session. The store becomes a general store.
**Alternatives:** Keep the login wall; stay electronics only.
**Consequences:** The agent's prompt and the returns and warranty policies change, so refund behaviour must be re-measured.

## D-012 — Plan choices for feature 021 (2026-11-04)

**Context:** The storefront plan raised five decisions.
**Decision:** Add `react-router` and `@fontsource-variable/schibsted-grotesk`. Lifestyle categories are Home and kitchen, Bags
and travel, Fitness and outdoors, with 30-day returns, no restocking fee and a 90-day warranty. No browser tests in the repo
for now, so the owner can keep building and learning. Staff get a Mark delivered action. Light and dark are both kept.
**Alternatives:** Hand-written routing; Google Fonts; committed Playwright tests; light only.
**Consequences:** UI regressions aren't caught automatically. Dark mode needs a second palette and themed illustrations.

## D-013 — The page scrolls in its own region (2026-11-04)

**Context:** AC-25 says the chat button never covers an Add to cart at any scroll position. The plan used a fixed bottom bar, but controls
slide under anything fixed over a scrolling page: measured as sabotage, it overlapped 105 times.
**Decision:** The page scrolls in `#page`, and the bar is a normal layout element below it. From 1280 px the button sits in the gutter, so
the page is 1120 px wide below 1440 px.
**Alternatives:** A fixed bar with padding, which only clears the end of the page; hiding the button while scrolling.
**Consequences:** Layout restores scroll positions on Back, because the browser only does that for the window. Phones lose the address
bar collapsing on scroll. `window.scrollTo` no longer does anything: use `#page`.

## D-014 — The policies define electronics by category (2026-11-04)

**Context:** The policies said "electronics" without defining it, so the agent gave a phone case the lifestyle warranty.
**Decision:** `returns.md` and `warranty.md` list the 5 electronics categories, matching the split in 021's Q6. No terms changed.
**Alternatives:** Telling the model in the prompt, which wouldn't reach the Knowledge Base's answers or a reader of the policy.
**Consequences:** A new category must be added to the policies. AWS gets this wording on its next deploy, untested on Claude.

## D-015 — ShopHelper Care is for electronics only; the trace page keeps its chat (2026-11-06)

**Context:** `warranty.md` didn't say whether Care covers lifestyle products, and the agent offered it for a yoga mat. T044 left the full
chat on the trace page, beside the new widget.
**Decision:** Owner's call: Care is for electronics only, added to AC-39. The trace page keeps its chat, so no code changes for that.
**Alternatives:** Care for everything, at $19.99 on a mug; removing the trace page's chat, which loses watching the steps as you type.
**Consequences:** AWS gets the new wording on its next deploy, untested on Claude.

## D-016 — 021 closes with Care questions unreliable (2026-11-06)

**Closed by 030 (D-018, D-019):** Care questions now search 48 of 48 times.

**Context:** After D-015, only 12 of 24 interleaved Care questions searched the policy. Two prompt rewrites didn't fix it. The other 12
gave a dead end, such as asking for an order number, and earlier prompts invented coverage.
**Decision:** Owner's call: accept the gap, take the claim out of AC-39, and move the fix to the backlog. The stronger prompt stays.
**Alternatives:** A code check that sends the model back to search when a message mentions Care or a warranty, like the refund check.
**Consequences:** The 2 Care eval cases use wordings that pass, so 33 of 33 doesn't mean Care works. Customers can still get a poor answer.

## D-017 — Evals run once by default (2026-11-06)

**Context:** Three runs take about 9 minutes. Run in the same order, they were also less independent than they looked, because of LM
Studio's prompt cache.
**Decision:** Owner's call: `scripts/evals_local.sh` runs once. `EVAL_RUNS=3` repeats it and stops at the first failed run. 021 closes on 1 run.
**Alternatives:** A field in `config.py`, which would put a test-only setting in the app's settings.
**Consequences:** A rare failure is less likely to show up. Use `EVAL_RUNS=3` after a prompt change that matters. `plan.md` and older task
results still mention 3 runs, which was true then.

## D-018 — Code searches before the model answers (2026-11-06)

**Context:** 030 first copied the refund check: let the model answer, then send it back. But tokens stream as the model writes, so a
rejected answer would reach the customer's screen, and the model could refuse again.
**Decision:** Owner approved: on a protected question, `agent()` skips the model and issues `search_policy` itself. The model answers from
the passages. If the search fails, the customer gets a fixed reply. The measurement script is saved as `evals/measure_policy.py`.
**Alternatives:** Sending the model back, which costs a model call and shows a withdrawn answer; forcing `tool_choice`, which depends on
each provider's support.
**Consequences:** The trace shows a 0-token step that the model didn't take. Works on Bedrock in theory, unproven until Phase 1.

## D-019 — The Care line names the electronics categories (2026-11-06)

**Context:** With the search guaranteed, the agent still called a laptop stand and a desk mat lifestyle products. Chunks are retrieved alone,
and the Care chunk said "electronics only" without the chunk that defines electronics.
**Decision:** `warranty.md`'s Care line lists the categories, with laptop stands and desk mats as examples. No terms changed.
**Alternatives:** Bigger chunks, which changes retrieval for every policy; telling the model in the prompt, which wouldn't reach AWS's
Knowledge Base answers.
**Consequences:** The list now lives in 2 lines of `warranty.md`, so a new category must change both. A test pins the Care line.

## D-020 — Tests run in three levels (2026-11-06)

**Context:** Full evals and measurements ran during tasks, up to 20 minutes at a time, and the owner sat waiting. Constitution II required
the full evals on every agent change.
**Decision:** Owner approved 3 levels: `scripts/check.sh` on every task, related eval cases when the agent changes, and the full evals plus
relevant measurements once per feature, in the background. Constitution 1.1.0: Principle II changes, and the Definition of Done doesn't.
**Alternatives:** Fewer samples, which weakens the rates; running tests in parallel, which fights over one model and shared demo orders.
**Consequences:** A problem can surface at Verify rather than mid-feature. A feature still can't be Implemented until level 3 passes.

## D-022 — A refund with no stated problem may get a question (2026-11-06)

**Context:** AC-9 measured 59 of 60. The miss, "It's under warranty, please refund order 1006", states no fault, and the agent asked for one. On that
wording 6 of 12 submit with the 030 check and 0 of 12 without, so the check didn't cause it.
**Decision:** Owner's call: AC-9 counts refunds that state a problem. Asking what's wrong isn't a false promise. The measurement was repeated with a
wording that states one, rather than dropping the miss from the count.
**Alternatives:** Forcing that wording to submit, which pushes the agent to file refunds with no reason.
**Consequences:** A customer who gives no reason gets asked for one. D-021 is on the 022 branch.

## D-023 — 030 closes with a known warranty refund bug (2026-11-06)

**Context:** With a problem stated, "It's under warranty and it stopped working, please refund order X" still got 0 of 8. The agent says refunds aren't
issued for items under warranty, which contradicts `refunds.md`. It isn't caused by 030: 8 of 16 submit with its check and 4 of 16 without.
**Decision:** Owner's call: close 030 on the 45 of 45 refunds with no warranty mention, and put the bug in the backlog.
**Alternatives:** A line in the policy saying a warranty doesn't remove the 30-day refund, then re-measuring.
**Consequences:** A customer who mentions a warranty can be wrongly turned down. The recommended fix is that policy line.

## D-024 — 031's build choices (2026-11-06)

**Context:** `typescript-eslint` 8.72.1 supports TypeScript below 6.1, and this project uses 7. The first folder layout also created 2 import cycles.
**Decision:** Owner approved: Biome for lint and format; `Principal` to `core/`, `ChatResponse` to `agent/`, `setup_local` to `api/`; `pyright` and `pre-commit` as dev tools; and
committing, pushing and merging each 031 PR once its checks pass, stopping for failures, decisions or behaviour changes.
**Alternatives:** ESLint unsupported, or downgrading TypeScript to suit a linter.
**Consequences:** ESLint is more widely known, but Biome fits this stack. The merge approval covers 031 only.

## D-021 — The learning website's build choices (2026-11-06)

**Context:** The course needs tables, code colouring and diagrams, and an order file. Project rules need the owner's approval for packages.
**Decision:** Owner approved `remark-gfm`, `rehype-highlight` and `mermaid`, loaded only on course pages; `course.json`, which needs no parser; and
merging each slice to `main` when it's done.
**Alternatives:** A separate Starlight site, which means a second app; MDX, which makes lessons code; `course.yaml`, which needs a package.
**Consequences:** Mermaid is large, so the spike measures it first, with SVG files as the fallback.

## D-025 — Merging 022's slices (2026-11-06)

**Context:** The course lands in 4 slices, and the owner reviewed the style at slice 1.
**Decision:** Owner's call: merge each slice once its checks pass, and delete merged branches afterwards. Stop for failures, decisions or behaviour changes.
**Alternatives:** Asking before each merge, which only adds waiting.
**Consequences:** Covers 022 only. The stepper sits on the right of the page, not across the top.
