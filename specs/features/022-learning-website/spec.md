# 022 — Learning Website

**Status:** In Progress
**Roadmap phase:** 2 · **Created:** 2026-11-06 · **Owner:** RVicky172

## Summary

ShopHelper was built so its owner can learn AI engineering, but the learning lives in 11 Markdown chapters that are tiring to read and stop
short of what the job needs. This feature turns them into a step-by-step course on the website: one path from how an LLM works to passing an
AI engineer interview, with a stepper to show where you are, simple explanations, real code from this project, and a practice question at the
end of every lesson. It takes over the roadmap's "Learning views" item. Research behind the course is in `research.md`.

## User Stories

- **US-1:** As a learner, I want one ordered path with clear steps, so that I always know what to read next.
- **US-2:** As a learner, I want each idea explained simply, with an example, so that reading isn't tedious.
- **US-3:** As a learner, I want to see the real code and run it here, so that I understand it rather than memorise it.
- **US-4:** As a learner, I want to know what else the market offers and when to pick what, so that I'm not limited to this project's choices.
- **US-5:** As a job seeker, I want the questions I'm likely to be asked, with strong answers, so that I'm ready for interviews.
- **US-6:** As a job seeker, I want to explain how this project was built and run, locally and on AWS, so that I can present it as my work.
- **US-7:** As a candidate, I want to practise AI-assisted coding, so that I do well when a company tests how I use Claude Code.

## The Course

13 stages, 81 lessons. Stages are in learning order. "Built" means ShopHelper has it, and "Concept" means the lesson teaches it without this
project using it.

| # | Stage | Lessons | Mostly |
| - | ----- | ------- | ------ |
| 0 | **Start here:** the AI engineer role, the skills employers list, how this course works, a tour of ShopHelper | 3 | Built |
| 1 | **How LLMs work:** tokens, embeddings, attention and transformers, training, how a reply is generated (prefill, decode, KV cache), sampling, context windows and prompt caching, reasoning models, choosing a model | 9 | Concept |
| 2 | **Talking to models:** prompts, structured output, context engineering, tool calling, how data passes through the system from browser to model and back | 5 | Built |
| 3 | **Agents:** chatbot, workflow or agent; the agent loop; tools; memory; human approval; workflow patterns; multi-agent systems and when not to use them; frameworks in the market | 8 | Built |
| 4 | **MCP:** why a protocol, tools and resources, transports, authorization, the current spec, MCP risks | 4 | Built |
| 5 | **RAG:** why RAG, embeddings in depth, chunking, vector indexes, vector databases in the market, hybrid search and reranking, contextual retrieval, debugging a wrong answer, RAG or long context or fine-tuning | 9 | Part built |
| 6 | **Building the app:** project setup and folder structure, the API, streaming, the frontend, choosing a database, authentication, authorization and data isolation | 7 | Built |
| 7 | **Evals and testing:** why testing AI is different, test levels, golden sets, RAG evals, agent evals, LLM judges, eval tools in the market, evals in CI | 8 | Part built |
| 8 | **Security:** the OWASP lists, prompt injection, layered defences, guardrails and private data, securing tools and secrets | 5 | Part built |
| 9 | **Cloud deployment:** how we run it locally, planning it on AWS, compute options, infrastructure as code, CI/CD, ways to release, scaling and rate limits, cost, other clouds and hosting your own model | 9 | Part built |
| 10 | **Running in production:** monitoring and tracing, the metrics that matter, incidents and rollback, managing prompts and models after launch | 4 | Concept |
| 11 | **Building with AI:** how to work with Claude Code, its main features, spec-driven development, how this project was built | 4 | Built |
| 12 | **The interview:** how interviews run, system design practice, debugging scenarios, the AI-assisted round, telling the ShopHelper story, the question bank | 6 | Mix |

Topics the owner asked for, and where they land: agents and multi-agent (3), RAG and MCP (4, 5), market strategies and tools (every "in the
market" lesson), the AI engineer role (0), LLMs (1), data passing (2), project setup (6), testing (7), cloud deployment and options (9), RAG and
agent evals (7), prompt injection (8), cloud security and monitoring (8, 10), streaming (6), vector databases, embeddings and chunking (5),
golden sets (7), CI/CD (9), managing after deployment (10), choosing data stores (6), authentication and authorization (6), deploying and
scaling (9), Claude Code in interviews (11, 12), spec-driven development (11).

## Acceptance Criteria

### Finding your way

- [ ] **AC-1:** A "Learn" link in the navbar opens the course, from every page. _(e2e)_
- [ ] **AC-2:** A vertical stepper on the right shows all 13 stages in order, marks the current one and those finished, and opens the current
      stage's lessons. On a phone the same list opens from a menu above the page, with no sideways scroll at 390 px. _(e2e)_
- [ ] **AC-3:** Inside a stage, the learner sees its lessons in order, with the current one marked. Every lesson has a Previous and a Next
      link that continue across stages. _(e2e)_
- [ ] **AC-4:** A lesson can be marked done. Progress and the last lesson survive a reload and closing the browser, and a Continue link
      returns to the last lesson. _(e2e)_
- [ ] **AC-5:** Every lesson has its own URL, so the back button, reload and a shared link all work. An unknown lesson shows a helpful
      not-found page. _(e2e)_
- [ ] **AC-6:** A search box finds lessons by title and heading, and every result opens that lesson. _(e2e)_

### Every lesson

- [ ] **AC-7:** Every lesson shows its reading time and has these parts in this order: what you'll learn, the simple explanation, an example,
      how ShopHelper does it or a "Not in ShopHelper" note, what the market offers where a choice exists, interview questions, and check
      yourself. A test fails if a part is missing. _(unit)_
- [ ] **AC-8:** The simple explanation works without earlier jargon: a term is explained on first use or links to the lesson that does. Each
      lesson targets a 10 minute read, and none takes over 15 minutes. _(unit for time; manual review for wording)_
- [ ] **AC-9:** A code example taken from this project names its file, and a test fails if that code no longer exists there. _(unit)_
- [ ] **AC-10:** Every "Try it" step in a lesson was actually run, on the running app, and recorded. _(manual)_
- [ ] **AC-11:** Every lesson has at least 2 interview questions, each with a strong answer and a likely follow-up. Check yourself has at
      least 2 questions that give feedback on the answer, right or wrong. _(unit)_
- [ ] **AC-12:** Anything about the market, such as products, prices or versions, shows the date it was checked and links its source. A number
      from a vendor is labelled as the vendor's claim. A number measured in this project says so. _(unit for date and source; manual review)_

### Required content

- [ ] **AC-13:** All 13 stages and 81 lessons listed above exist. _(unit)_
- [ ] **AC-14:** The 11 existing chapters are all carried into the course, with nothing lost, and each fact has one home. _(manual checklist)_
- [ ] **AC-15:** The local run guide, the AWS plan and the deployment steps can each be followed from the site alone. The AWS lessons state
      their costs, and no step deploys anything by accident. _(manual)_
- [ ] **AC-16:** A learner can trace one message from browser to model and back in a single diagram, with the real function at every step.
      _(manual)_
- [ ] **AC-17:** The interview stage has at least 60 questions across all stages, 3 system design walkthroughs and 5 debugging scenarios. _(unit)_
- [ ] **AC-18:** The AI-assisted round lesson says plainly that company rules differ, and to ask the recruiter what's allowed. _(manual)_

### Keeping what exists

- [ ] **AC-19:** Light and dark, keyboard use, and the contrast and target sizes from 021 hold on every course page. _(measurement)_
- [ ] **AC-20:** On the phone profile from 021, Largest Contentful Paint stays under 2.5 s and layout shift under 0.1. The shop's own pages get
      no slower: course pages load only when opened. _(measurement)_
- [ ] **AC-21:** Everything is served from this project, with no runtime calls to other sites, and the course works with the agent switched off.
      _(e2e)_
- [ ] **AC-22:** Every internal link works, and a test fails on a broken one. _(unit)_
- [ ] **AC-23:** No API, agent or AWS behaviour changes, and `scripts/check.sh` passes. _(unit)_

## Non-Functional Requirements

- Writing: short sentences and plain words. Say what a thing does before naming it.
- Honesty: don't present a vendor's ranking as fact. Say what this project hasn't built, and that local eval results come from Qwen.
- Upkeep: a lesson is a text file, and adding one needs no code change.
- Performance and accessibility: as in AC-19 and AC-20.

## Out of Scope

- Video, a certificate, comments or a shared leaderboard.
- Hosting the site publicly, or on AWS.
- Building features the course only describes, such as hybrid search, tracing or a multi-agent mode (Q6).
- Courses for ML research topics, such as training a model from scratch. Stage 1 explains the ideas only.
- Guarantees about any company's interview. Questions are typical ones, from public sources.

## Open Questions

All answered by the owner on 2026-11-06, who accepted the proposals as a starting point.

- **Q1** Where does the course live? _Answer:_ inside the existing website at `/learn`. It shares the design, needs no
  second server, and already has a Markdown renderer. A separate site built with Starlight or Docusaurus gets search and navigation for free,
  but means a second app, a second design and a second thing to run. A stepper would still need custom work.
- **Q2** How should the folders change? _Answer:_ keep Markdown in `docs/`, the one home for learner content, grouped by
  stage, and let the website read it. Each file moves once, and no copy exists. Nothing outside `docs/` and `web/` changes:

  ```
  docs/
    README.md                     index, points to the course
    learn/
      course.json                 stage and lesson order: the one source for the stepper
      00-start-here/
      01-how-llms-work/
        01-tokens.md
        02-embeddings.md
      ...
      12-the-interview/
    reference/                    moved here: architecture, local-setup, runbook, aws-services,
                                  deployment-comparison, next-steps
  web/src/features/learn/                  new: the course's pages and components
  ```

  The 11 chapters split across the new stages, and every link to them is updated. `specs/` and `memory/` stay as they are.
- **Q3** Do you need to sign in to read it? _Answer:_ no. The course is public, like the shop, and only the Try it steps
  need the demo accounts.
- **Q4** Where is progress saved? _Answer:_ in this browser. It needs no server change, and there's one learner. Saving
  to the account would follow you across devices, but adds tables and routes.
- **Q5** What gets built first? _Answer:_ in 4 slices, each usable when it lands. **Slice 1:** the site, the stepper, the
  folder move, the 11 chapters carried over, and stage 0. **Slice 2:** stages 1 to 5, the core. **Slice 3:** stages 6 to 10, production.
  **Slice 4:** stages 11 and 12, the interview. If an interview is close, slice 4 can come straight after slice 1.
- **Q6** Should the project gain what it lacks, so lessons are hands-on? _Answer:_ not in this feature. Lessons on hybrid
  search, tracing and multi-agent say "Not in ShopHelper", and each is listed as a possible lab afterwards. Interviewers value production
  experience, so tracing is the first one to build.
- **Q7** Who checks the writing is simple enough? _Answer:_ you. Slice 1 stops for your review of 2 finished lessons, and
  the style is fixed before the other 79 are written.

## Changelog

- 2026-11-06 — Created, from the owner's request and `research.md`. Replaces the roadmap's "Learning views" item.
- 2026-11-06 — Questions answered and spec Approved.
- 2026-11-06 — The site moves to `web/src/features/learn/`, and docs paths follow 031's layout.
- 2026-11-06 — Owner approved the lesson style, and moved the stepper to the right of the page (AC-2).
- 2026-11-06 — Plan approved. `course.json` replaces `course.yaml` (D-021). Stage 6 now names folder structure, at the owner's request.
