# 022 — Learning Website · Tasks

**Plan:** `./plan.md`
Legend: `[P]` = can run in parallel with the previous task. Each task lists files and the proving test.
Test-first: each "tests" task must fail before its paired implementation makes it pass.
When a task is done, tick it and add an indented **Result (YYYY-MM-DD):** note: what was done, numbers measured,
anything surprising or deferred.

Every lesson task follows plan §9: close the gap with primary sources, write in plain words, check claims against the code, run its Try it. Each
ends with `scripts/check.sh`. Lesson tasks may finish 2 or 3 lessons at a time.

# Slice 1 — Foundation

## Setup

- [x] **T001** — Spike, thrown away afterwards: one lesson through the docs mount, plugin and lazy load, with hot reload and a production build. Measure
      Mermaid's chunk and the shop's bundle size · files: `docker-compose.yml`, `web/vite.config.ts` · test: recorded numbers; if Mermaid is too heavy,
      switch to SVG files and stop to report
      **Result (2026-11-06):** Worked through the Docker mount: tables, code colouring and Mermaid, with no page errors. Shop landing page unchanged at 170 KB. A lesson with a diagram downloads about 900 KB of compressed JavaScript, half of it Mermaid's elk layout engine. It loads after the text and is cached, so Mermaid stays, and T390 confirms it on the phone profile. Spike removed.
- [x] **T002** — Add `remark-gfm`, `rehype-highlight` and `mermaid`; update the stack doc · files: `web/package.json`, `specs/tech-stack.md` · test:
      `docker compose up --build -V web`, then `scripts/check.sh`
      **Result (2026-11-06):** `remark-gfm` 4.0.1, `rehype-highlight` 7.0.2 and `mermaid` 12.3.0. Web container rebuilt.
- [x] **T003** — Read-only docs mount and `server.fs.allow` · files: `docker-compose.yml`, `web/vite.config.ts` · test: a lesson edit reaches the running site
      **Result (2026-11-06):** `./docs:/docs:ro`, and `server.fs.allow`. A lesson edit shows after a browser refresh, not instantly, which is enough for writing.

## Tests First

- [x] **T010** — Failing content tests: parts in order, counts, reading time, links, `file=` snippets, market dates and sources, interview questions, check
      yourself. Each rule proved by breaking a sample lesson · files: `tests/test_course.py`
      **Result (2026-11-06):** 20 tests in `tests/test_course.py`, including 11 that each break a sample lesson and confirm the rule fires.
- [x] **T011** [P] — Failing tests for progress, search and link conversion · files: `web/src/features/learn/*.test.ts`
      **Result (2026-11-06):** 13 tests for parsing, links, progress and search.

## Core

- [x] **T020** — `course.json` format and `learn-plugin.ts`: `virtual:course` and `virtual:course-questions` · files: `web/learn-plugin.ts`,
      `docs/learn/course.json` · test: T010, and an index of a few KB
      **Result (2026-11-06):** `course.json` and `learn-plugin.ts`. The question bank module waits for T303, its only user.
- [x] **T021** — `progress.ts`, `search.ts`, `links.ts` · files: `web/src/features/learn/` · test: T011
      **Result (2026-11-06):** All pure and tested. `search.ts` became `lessonSearch.ts`, because it clashed with `Search.tsx` on Windows.
- [x] **T022** — Route, navbar link, course home with Continue · files: `web/src/App.tsx`, `web/src/layout/Navbar.tsx`, `web/src/features/learn/LearnHome.tsx` · test:
      browser run; shop bundle unchanged
      **Result (2026-11-06):** Route and "Learn" link. Shop's main chunk 343.06 kB, up 0.47 kB, for the link and route.
- [x] **T023** — Stepper and lesson list, at 390 and 1280 px · files: `web/src/features/learn/CourseNav.tsx` · test: browser run, no sideways scroll
      **Result (2026-11-06):** 13 stages, current one marked, finished ones ticked. Moved to a right-hand rail at the owner's request, with the current stage's lessons opened, and a menu above the page on phones. No sideways scroll at 390 px, checked on 4 pages.
- [x] **T024** — Lesson page: body, code, diagrams, Previous and Next, not found · files: `web/src/features/learn/LessonPage.tsx`, `LessonBody.tsx`, `CodeBlock.tsx`,
      `Diagram.tsx` · test: browser run, both themes
      **Result (2026-11-06):** Lessons, code with file captions, tables, diagrams, Previous and Next, not found. Both themes reviewed from screenshots. Mermaid follows light and dark.
- [x] **T025** — Check yourself, interview answers and search box · files: `web/src/features/learn/CheckYourself.tsx`, `Search.tsx` · test: browser run
      **Result (2026-11-06):** Answers reveal on demand, each check gives feedback, search opens results. Screenshot review found no arrow on disclosure rows, now fixed.

## Folder move

- [x] **T030** — Move reference docs to `docs/reference/` and fix live links · files: `docs/`, `README.md`, `CLAUDE.md`, `specs/architecture.md`,
      `specs/roadmap.md`, `src/shophelper/auth.py` · test: link check, 0 broken
      **Result (2026-11-06):** 6 docs moved to `docs/reference/`, with live links updated.
- [x] **T031** — Split the 11 chapters into stage folders, with a section checklist · files: `docs/learn/**` · test: link check, checklist complete (AC-14).
      Restart `web` afterwards
      **Result (2026-11-06):** All 11 chapters moved, each whole into its stage, with a `carried` header: they split when their stage is written, so nothing is lost meanwhile. Checklist: 9 moved as they were; agents rewritten as the agent loop lesson with every section kept; the RAG chapter's chunking section moved to the new Chunking lesson. The link check also found 2 links broken by 031, now fixed. The old "20 chunks" was stale: it's 24.
- [x] **T032** — Rewrite `docs/README.md` as the course index · files: `docs/README.md` · test: link check
      **Result (2026-11-06):** `docs/README.md` and the README point to the course.

## Style review

- [x] **T040** — Stage 0: the role, how the course works, tour of ShopHelper · files: `docs/learn/00-start-here/` · test: T010
      **Result (2026-11-06):** 3 lessons, all passing the format rules. Sources checked: one claim about interviews had no source that supported it, so it was reworded.
- [x] **T041** — 2 full sample lessons at final quality: the agent loop and chunking · files: `docs/learn/` · test: T010
      **Result (2026-11-06):** The agent loop and Chunking, at final quality. Every Try it step run on the live stack, which caught one wrong instruction, now fixed. Test conversations removed.
- [x] **T042** — **Stop for the owner's review of the style (Q7).** Record changes to the format before more is written · test: owner's approval
      **Result (2026-11-06):** Owner approved the style, and asked for the stepper on the right, as a normal docs site has it.
- [x] **T043** — Slice 1 gates and merge, once the owner asks · test: `scripts/check.sh`, build, browser run
      **Result (2026-11-06):** Gates pass, merged, and merged branches deleted.

# Slice 2 — Core

- [x] **T100** — Stage 1: tokens, embeddings, attention and transformers · files: `docs/learn/01-how-llms-work/`
      **Result (2026-11-06):** 3 lessons with real measurements from this project: digits take a token each, Hindi cost 18 tokens against English 5, and a paraphrase scored below a shipping sentence. Sizes from each provider's docs. Snippet test caught a misquoted schema comment.
- [x] **T101** — Stage 1: training, generating a reply, sampling
      **Result (2026-11-06):** 3 lessons. Measured: about 1 second of prefill per 1,000 tokens, decode falling from 63 to 26 tokens a second as prompts grew, and temperature barely changing a simple answer, which tutorials don't usually show.
- [x] **T102** — Stage 1: context windows and prompt caching, reasoning models, choosing a model
      **Result (2026-11-06):** 3 lessons. Measured a repeated prompt falling from 4.05 s to 0.07 s. Running the Try it showed a repeated chat question doesn't speed up, because the conversation grows, so the exercise now teaches that. Costs worked out from Anthropic's published prices. Stage 1 is complete: 9 lessons.
- [x] **T103** — Stage 2: prompts, structured output, context engineering · files: `docs/learn/02-talking-to-models/`
      **Result (2026-11-06):** 3 lessons. Measured: valid JSON 10 of 10 with a prompt alone and with a schema, so the lesson explains a schema is a guarantee for the rare case, not better odds. A real turn split into about 14, 300 and 1,440 tokens. Guidance from Anthropic's docs.
- [x] **T104** — Stage 2: tool calling, how data passes through the system, with the one diagram (AC-16)
      **Result (2026-11-06):** 2 lessons, with a real tool call captured from the local model, which also invented tracking information: kept in as a teaching point. AC-16's diagram names the real function at all 13 steps and renders correctly. Every Try it step run. Stage 2 is complete: 5 lessons.
- [x] **T105** — Stage 3: chatbot, workflow or agent; the loop; tools · files: `docs/learn/03-agents/`
      **Result (2026-11-06):** Chatbot, workflow or agent is new, and Designing tools replaces the carried chapter with every fact kept. Tools exercises run: 9999 returns an error object, and Arjun's order is refused by the rule.
- [x] **T106** — Stage 3: memory, human approval, workflow patterns
      **Result (2026-11-06):** The carried chapter split into Memory and Human approval, plus Workflow patterns. The full approval demo was run with two users: paused, API restarted, approved afterwards, order refunded. Neha's order never reached the queue, and Kabir's $249 request needs an admin.
- [x] **T107** — Stage 3: multi-agent, frameworks in the market
      **Result (2026-11-06):** Multi-agent systems and Agent frameworks, from each project's own docs. That corrected 2 blog claims: the OpenAI Agents SDK isn't limited to OpenAI models, and Microsoft Agent Framework is the direct successor to AutoGen. OWASP's wording taken from its own cheat sheet. Stage 3 is complete: 8 lessons.
- [x] **T108** — Stage 4: all 4 MCP lessons. First check what `mcp` 1.30.0 here does against spec 2026-07-28 · files: `docs/learn/04-mcp/`
      **Result (2026-11-06):** 4 lessons replace the carried chapter. Checked against the running server: `mcp` 1.30.0 tops out at 2025-11-25, answers that when asked for 2026-07-28, and still needs a session, so it's a legacy server. It works because this project owns both ends. Upgrade added to the backlog, and the lessons say so. Fixed a Try it broken by 031. Ran the token and curl exercises, and added and removed a tool. The Inspector's own screen wasn't run, as it's interactive: the same calls were made directly. Stage 4 is complete.
- [ ] **T109** — Stage 5: why RAG, embeddings in depth, chunking · files: `docs/learn/05-rag/`
- [ ] **T110** — Stage 5: vector indexes, vector databases in the market, hybrid search and reranking
- [ ] **T111** — Stage 5: contextual retrieval, debugging a wrong answer, RAG or long context or fine-tuning
- [ ] **T112** — Slice 2 gates and merge, once the owner asks

# Slice 3 — Production

- [ ] **T200** — Stage 6: project setup and folder structure, the API, streaming · files: `docs/learn/06-building-the-app/`
- [ ] **T201** — Stage 6: the frontend, choosing a database
- [ ] **T202** — Stage 6: authentication, authorization and isolation
- [ ] **T203** — Stage 7: why testing AI differs, test levels, golden sets · files: `docs/learn/07-evals-and-testing/`
- [ ] **T204** — Stage 7: RAG evals, agent evals, LLM judges
- [ ] **T205** — Stage 7: eval tools in the market, evals in CI
- [ ] **T206** — Stage 8: the OWASP lists, prompt injection, layered defences · files: `docs/learn/08-security/`
- [ ] **T207** — Stage 8: guardrails and private data, securing tools and secrets
- [ ] **T208** — Stage 9: running locally, planning it on AWS with costs, compute options (AC-15) · files: `docs/learn/09-cloud-deployment/`
- [ ] **T209** — Stage 9: infrastructure as code, CI/CD, ways to release
- [ ] **T210** — Stage 9: scaling and rate limits, cost, other clouds and hosting your own model
- [ ] **T211** — Stage 10: all 4 lessons on running in production · files: `docs/learn/10-running-in-production/`
- [ ] **T212** — Slice 3 gates and merge, once the owner asks

# Slice 4 — Interview

- [ ] **T300** — Stage 11: all 4 lessons · files: `docs/learn/11-building-with-ai/`
- [ ] **T301** — Stage 12: how interviews run, system design practice with 3 walkthroughs · files: `docs/learn/12-the-interview/`
- [ ] **T302** — Stage 12: 5 debugging scenarios, the AI-assisted round (AC-18)
- [ ] **T303** — Stage 12: telling the ShopHelper story, and the question bank page · files: `web/src/features/learn/QuestionBank.tsx` · test: 60 or more questions

## Verify

- [ ] **T390** — Accessibility and performance on a production build, as in 021's T090 · test: recorded numbers (AC-19, AC-20)
- [ ] **T391** — Request hosts listed with LM Studio stopped · test: only this site's host (AC-21)
- [ ] **T392** — Update `specs/architecture.md` with what this feature established.
- [ ] **T393** — Every Definition-of-Done gate green (`specs/constitution.md`), level 3 in the background; record the numbers.
- [ ] **T394** — Tick ACs in `spec.md` (Status `Implemented`), update `roadmap.md`, `memory/progress.md`, `memory/MEMORY.md`.

## AC coverage

| AC    | Tasks            |
| ----- | ---------------- |
| AC-1  | T022             |
| AC-2  | T023             |
| AC-3  | T023, T024       |
| AC-4  | T011, T021, T022 |
| AC-5  | T022, T024       |
| AC-6  | T011, T021, T025 |
| AC-7  | T010, T041       |
| AC-8  | T010, T042       |
| AC-9  | T010             |
| AC-10 | every lesson task |
| AC-11 | T010, T025       |
| AC-12 | T010             |
| AC-13 | T010, T394       |
| AC-14 | T031             |
| AC-15 | T208             |
| AC-16 | T104             |
| AC-17 | T301, T302, T303 |
| AC-18 | T302             |
| AC-19 | T390             |
| AC-20 | T001, T022, T390 |
| AC-21 | T391             |
| AC-22 | T010, T030, T031 |
| AC-23 | T393             |
