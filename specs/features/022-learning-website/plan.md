# 022 — Learning Website · Implementation Plan

**Spec:** `./spec.md` · **Status:** Approved

## Approach

### §1 Plain Markdown, read straight from `docs/`

Lessons stay ordinary `.md` files, so they still read well on GitHub and adding one needs no code (spec NFR). There's no MDX: it would need a
compiler, and it would make lessons code. Each lesson has a short header and fixed section names:

```markdown
---
title: Chunking
checked: 2026-11-06
---

## What you'll learn
## The simple explanation
## An example
## How ShopHelper does it        (or: ## Not in ShopHelper)
## In the market                 (only where a choice exists)
## Try it                        (only where the app can show it)
## Interview questions
## Check yourself
```

- **Interview questions:** a `###` per question, then `**Strong answer:**` and `**Follow-up:**`.
- **Check yourself:** a Markdown task list. `- [x]` marks the right answer and text after ` — ` is the feedback. GitHub shows a checklist, and the site
  shows a question that responds.
- **Code from this project:** a fence naming its file, such as ` ```python file=src/shophelper/graph.py `. A test checks those lines still exist there.

### §2 Letting the website see `docs/`

The web container sees only `web/` (a known gotcha). `docker-compose.yml` mounts `./docs:/docs:ro`. The app is at `/app` in the container, so `../docs`
points at the same files there and on the host, with no path switching. Vite's `server.fs.allow` gains `..`. Neither the API images nor AWS change.

### §3 The course index

`docs/learn/course.json` holds stage and lesson order. A small Vite plugin, `web/learn-plugin.ts`, reads it plus each lesson's header and headings, and
exposes `virtual:course`: titles, reading times and headings, a few KB in all. The stepper and search use only this, so the browser doesn't download
81 lessons to draw a menu. Lesson bodies load one at a time through `import.meta.glob`. The question bank (AC-17) gets its own lazy module,
`virtual:course-questions`, extracted the same way, so it's one source and no copy.

### §4 The pages

`/learn` goes in the existing `Layout`, as a lazy route like `how-it-works`. So the navbar, theme and chat button come for free, and shop pages carry none
of its code (AC-20). The route needs no API change, and the existing signed-out gate doesn't apply to it (Q3).

- `/learn`: the stepper, stage cards and a Continue link.
- `/learn/:stage/:lesson`: stepper, lesson list, lesson, Previous and Next.
- The stepper is an ordered list with `aria-current="step"`. From 1024 px all 13 stages show. Below that it scrolls inside its own strip, with the
  current stage in view, so the page itself never scrolls sideways.
- Relative `.md` links become `/learn/...` routes when rendered, so a link works both on GitHub and on the site.
- Pages scroll in `#page` (D-013), so moving between lessons resets scroll there, not on `window`.

### §5 Progress

`web/src/features/learn/progress.ts` keeps finished lessons and the last lesson in `localStorage`, under one versioned key, with every read and write in
`try/catch`. It's not personal data, so it isn't cleared on logout. Pure functions, so they're unit tested.

### §6 Search

A small function over `virtual:course` titles and headings. At 81 lessons, a library isn't justified.

### §7 Folder move

Files move with `git mv`, once, in slice 1. The 11 chapters split like this:

| Chapter | Goes to |
| ------- | ------- |
| 01 Agents and the loop | Stage 3: chatbot or agent, the agent loop |
| 02 Tools | Stage 2 tool calling, stage 3 tools |
| 03 MCP | Stage 4 |
| 04 RAG | Stage 5 |
| 05 Memory and human approval | Stage 3: memory, human approval |
| 06 Streaming | Stage 6: streaming |
| 07 The React frontend | Stage 6: the frontend |
| 08 Guardrails | Stage 8 |
| 09 Evals | Stage 7 |
| 10 Local vs AWS | Stage 9 |
| 11 Accounts and isolation | Stage 6: authentication, authorization and isolation |

Chapters are carried over at their existing depth first, and restyled to the lesson format in the slice that owns their stage. A checklist tracks every
section, for AC-14. `architecture`, `local-setup`, `runbook`, `aws-services`, `deployment-comparison` and `next-steps` move to `docs/reference/`.
Live links in the README, `CLAUDE.md`, `specs/architecture.md`, `specs/roadmap.md`, `src/shophelper/auth.py` and `docs/` are updated. Finished feature
specs stay as written, because they're history.

### §8 Slices

Each slice ends in a working site, and can merge on its own. The spec stays In Progress until slice 4.

1. **Foundation:** spike, site, folder move, carried-over chapters, stage 0, and 2 finished lessons. **Stops for the owner's review of the style (Q7).**
2. **Core:** stages 1 to 5, 35 lessons.
3. **Production:** stages 6 to 10, 33 lessons.
4. **Interview:** stages 11 and 12, 10 lessons, the question bank, and final checks.

If an interview is close, slice 4 can follow slice 1.

### §9 How each lesson gets written

1. Close its gap from `research.md`, using primary sources.
2. Write in plain words, then check claims against the code.
3. Run its Try it on the live stack, and record that.

Tests here are level 1. Nothing in this feature touches the agent, so level 2 doesn't apply. Level 3 runs once, in the background, in slice 4.

## Dependencies (approved 2026-11-06, D-021)

All load only in the lazy `/learn` code, so the shop gets no bigger.

| Package | Why | Why not hand-roll it |
| ------- | --- | -------------------- |
| `remark-gfm` | Tables: the existing chapters use them, and `react-markdown` alone doesn't render them | The standard plugin for that renderer |
| `rehype-highlight` | Code colouring, with only the languages used | A tokenizer per language isn't worth writing |
| `mermaid` | The existing chapters have 13 diagrams, and more are coming | Large, so it loads only on a lesson that has a diagram |

T002 updates `specs/tech-stack.md`. `package.json` changes need `docker compose up --build -V web`.

## Files

| File | Change | Purpose |
| ---- | ------ | ------- |
| `docker-compose.yml` | modify | Read-only `docs` mount |
| `web/vite.config.ts`, `web/learn-plugin.ts` | modify, new | §2, §3 |
| `web/package.json` | modify | The dependencies above |
| `web/src/App.tsx`, `web/src/layout/Navbar.tsx` | modify | Lazy route and "Learn" link |
| `web/src/features/learn/*` | new | `LearnHome`, `LessonPage`, `Stepper`, `LessonList`, `LessonBody`, `CodeBlock`, `Diagram`, `CheckYourself`, `Search`, `QuestionBank`, `progress.ts`, `search.ts`, `links.ts`, with tests |
| `docs/learn/**`, `docs/reference/**`, `docs/README.md` | move, new | The course |
| `tests/test_course.py` | new | The content rules below |
| `README.md`, `CLAUDE.md`, `specs/architecture.md`, `specs/tech-stack.md`, `specs/roadmap.md` | modify | Paths, stack, status |

No change to `src/` beyond a comment path, `infra/`, the database or the API.

## Data Structures & Interfaces

```ts
// docs/learn/course.json
{ "stages": [{ "id": "05-rag", "title": "RAG", "lessons": ["01-why-rag", "02-embeddings"] }] }

// virtual:course
type Lesson = { stage: string; id: string; title: string; minutes: number; headings: string[]; checked: string }
type Stage = { id: string; title: string; lessons: Lesson[] }
export const course: Stage[]

// progress.ts
type Progress = { done: string[]; last: string | null }
loadProgress(): Progress
markDone(p: Progress, lessonKey: string): Progress
```

## Techniques

- Reading time: words outside code fences at 200 a minute. The limit in AC-8 is therefore 3,000 words.
- Diagrams: a Mermaid fence becomes a lazy component that holds its space, with the theme taken from light or dark. No script runs from lesson text,
  and Mermaid runs in strict mode.
- `tests/test_course.py` runs on the host, in `scripts/check.sh`, where it can read `src/` and `docs/` together.

## Test Approach

| AC | Test | Type |
| -- | ---- | ---- |
| AC-1, AC-2, AC-3, AC-5 | Browser run at 390 and 1280 px, with a sideways-scroll check | e2e |
| AC-4 | `progress.test.ts`, then a reload in the browser | unit + e2e |
| AC-6 | `search.test.ts`, then opening results in the browser | unit + e2e |
| AC-7, AC-11, AC-13, AC-17 | `tests/test_course.py`: parts in order, counts, stages | unit |
| AC-8 | `tests/test_course.py` for time; the owner reviews wording (Q7) | unit + manual |
| AC-9 | `tests/test_course.py`: each `file=` snippet's lines exist in that file | unit |
| AC-10 | Run per lesson, recorded in `tasks.md` | manual |
| AC-12 | `tests/test_course.py`: each "In the market" has a date and a link; sources read by hand | unit + manual |
| AC-14 | Section checklist in `tasks.md` | manual |
| AC-15, AC-16, AC-18 | Followed from the site alone, and read through | manual |
| AC-19, AC-20 | axe, keyboard, LCP and CLS, as in 021's T090, plus bundle size of shop pages before and after | measurement |
| AC-21 | Browser run listing every request's host, with LM Studio stopped | e2e |
| AC-22 | `tests/test_course.py`: every relative link resolves | unit |
| AC-23 | `scripts/check.sh`, level 3 once, and `git status infra` | unit |

Sabotage: for each content rule, break one lesson and confirm the test fails.

## Risks & Mitigations

- **Size.** 81 checked lessons is the biggest risk. Slices give value early, and Q7's review stops bad style from spreading.
- **The Vite plugin and Docker mount are new.** File changes may not reach Vite across the mount. **Spike first:** one lesson through the mount, plugin
  and lazy load, with a hot reload and a production build.
- **Mermaid's size and dark mode.** **Same spike:** measure its chunk, and confirm the shop's bundle doesn't change. Fallback: draw diagrams as SVG files.
- **Conflict with 030.** Its branch edits chapters 1, 6 and 9, the README and `local-setup.md`, which move here. Git can follow a move but not a split, so
  those edits will be redone by hand when 030 merges. About 40 lines.
- **Facts go stale.** The market changes fast, which is why lessons carry `checked` dates. A later job can list the oldest.
- **The whole app needs the API.** If the API is down, `App` shows an error, course included. AC-21 means the model being off, not the API. Changing
  that is out of scope.
- **A blank site after `git checkout`.** Vite can get stuck: restart `web` (see learnings). Moving 11 files will likely trigger it.

## Constitution Check

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Spec before code | ✅ | Spec updated first: `course.json`, not `course.yaml` |
| II. Test-gated delivery | ✅ | `tests/test_course.py` joins `scripts/check.sh`, with sabotage checks |
| III. Small dependencies | ✅ | 3 new packages, justified above, approved by the owner (D-021) |
| IV. Memory maintained | ✅ | Decisions and learnings recorded per slice |
| V. The model asks, code acts | ✅ | The agent isn't touched |
| VI. AWS stays the default | ✅ | No setting, API or infrastructure change |
| VII. Local first | ✅ | All served locally, with no runtime calls to other sites (AC-21) |
| VIII. Built to learn | ✅ | This feature is that principle. Claims are checked and numbers sourced |
| IX. Stream changes additive | ✅ | No stream changes |
