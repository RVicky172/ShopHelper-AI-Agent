# ShopHelper — Constitution

> The non-negotiable principles of this project. Every spec, plan, task, and line of code must comply.
> If a change needs to break a principle, amend this document first (see "Governance & Amendments").

**Version:** 1.1.0 · **Ratified:** 2026-11-04 · **Amended:** 2026-11-06

---

## Mission

ShopHelper is a customer-support AI agent for a fictional electronics store, built so its owner can learn how agents, RAG, MCP and tools really work. Success means every part
runs and can be inspected on one machine, and the same code can still deploy to AWS.

## Core Principles

### I. Spec Before Code

No feature code is written without an approved spec in `specs/features/NNN-name/`.
The flow is always **Specify → Plan → Tasks → Implement → Verify** (see `workflow.md`).
Bug fixes and refactors that do not change behavior may skip the spec but must still be logged in `memory/progress.md`.

### II. Test-Gated Delivery

- No task is "done" until its tests pass: `scripts/check.sh`, plus the related eval cases if the change affects the agent, its prompt, tools or RAG. The full `scripts/evals_local.sh` runs once per feature, at Verify (see the levels in `testing-strategy.md`).
- Pure logic is unit-tested, test-first: write the failing test, then the code.
- Tests wait on real signals, never fixed sleeps; anything time-dependent takes time as an input so tests are
  deterministic.

### III. Simplicity and Small Dependencies

- Prefer the platform and small in-house helpers over new libraries.
- Adding a runtime dependency requires a justification in `specs/tech-stack.md` (size, license, why not
  hand-rolled) and a `memory/decisions.md` entry.
- YAGNI: build what the current roadmap phase needs, nothing more.

### IV. Memory Is Maintained

- Agents and humans keep `memory/` current: decisions, progress, and learnings (see `memory-management.md`).
- A session that changes direction or discovers a pitfall records it before ending.

### V. The Model Asks, Code Acts

- The model never performs an action itself. Anything that changes data or moves money is decided in
  deterministic code, not in a prompt.
- A refund always passes `refund_eligibility` and then a human approval through `interrupt()`.
- Tools that change state are never exposed on the MCP server, which any client can reach.
- Side effects go after `interrupt()`, because LangGraph re-runs the node from the top on resume.

### VI. AWS Stays the Default

- Every new setting defaults to the existing AWS behaviour. `test_defaults_are_the_aws_path` pins this.
- Local-only packages are imported inside functions, so AWS runtimes never load them.
- Local-only routes return 404 unless `DATABASE_URL` is set.
- Nothing is deployed to AWS, and no paid resource is created, unless the user asks in that session.
- Infrastructure stays destroyable with `scripts/teardown.sh`, and is tagged `Project=ShopHelper`.

### VII. Local First

- Every feature works with `docker compose up` and LM Studio, with no cloud account and no paid service.
- Its data can be inspected, in pgAdmin or the UI. Ports stay bound to `127.0.0.1`.

### VIII. Built to Learn

- A new concept gets an explanation in `docs/learn/`: why it exists, the real code, and a Try it exercise.
- Doc claims are checked against the running app. Numbers are measured, never estimated.
- The readable, explicit version beats the clever one, including over a library that hides the mechanics.

### IX. Stream Changes Are Additive

- `/chat/stream` may gain event types, but existing events keep their names and shapes, so a client that
  reads only `token` and `final` keeps working.
- New events are handled in `web/src/chat/chatReducer.ts`, with a test, and listed in
  `docs/learn/06-streaming.md`.

## Quality Gates (Definition of Done)

A feature is **Done** when all are true:

1. Spec status is `Implemented` and every acceptance criterion is checked — each one proven by a test or a
   recorded measurement.
2. `scripts/check.sh` passes (the fast gate: lint, unit tests, Terraform format, typecheck).
3. `scripts/evals_local.sh` passes every case (needs `docker compose up` and LM Studio). A failure is read
   and explained, never just re-run until green.
4. `cd web && npm run build` succeeds.
5. `memory/progress.md`, `memory/MEMORY.md` and `specs/roadmap.md` are updated.

6. If `infra/` changed: `terraform -chdir=infra validate` passes.
7. If the UI changed: the flow was run in a real browser with no console errors.
8. If behaviour changed: `docs/` is updated, and its Try it steps were actually run.

## Governance & Amendments

- This constitution supersedes all other docs. Conflicts are resolved in its favor.
- Amend by editing this file in a dedicated change: bump the version (MAJOR = principle removed/redefined,
  MINOR = principle added, PATCH = wording), and record the reason in `memory/decisions.md`.
