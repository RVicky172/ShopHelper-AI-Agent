# Spec-Driven Workflow

Every feature moves through five gated stages. Each stage produces a file in `specs/features/NNN-short-name/`.
Do not start a stage until the previous one is approved.

```
 1. SPECIFY  ──►  2. PLAN  ──►  3. TASKS  ──►  4. IMPLEMENT  ──►  5. VERIFY
   spec.md        plan.md       tasks.md        code + tests       Definition of Done, docs, memory
   (what/why)     (how)         (steps)
```

## Feature numbering

`000–009` foundation, `010–019` move to AWS, `020–029` users and understanding, `030+` agreed from the backlog.

Folder name: `NNN-kebab-name` (e.g. `012-user-login`).

## Stage 1 — Specify (`spec.md`)

Copy `templates/spec-template.md`. Describe **what** and **why**, never **how**:
user stories, acceptance criteria (testable, numbered `AC-1…`, each naming the test type that proves it),
out-of-scope, open questions. Set `Status: Draft`. A human reviews and changes it to `Status: Approved`.
**Gate:** no `[NEEDS CLARIFICATION]` markers remain; every AC is testable.

## Stage 2 — Plan (`plan.md`)

Copy `templates/plan-template.md`. Describe **how**: files touched, interfaces, techniques, risks, a test for every
AC, and a **Constitution check** (each principle: ✅ / ⚠️ with justification). A human approves it.
**Gate:** constitution check passes; no new dependency without a `tech-stack.md` update.

## Stage 3 — Tasks (`tasks.md`)

Copy `templates/tasks-template.md`. Break the plan into small ordered tasks (≤ ~1 hour each), each naming the files
it touches and the test that proves it. Tests are written **before or with** the code they cover. Mark tasks that
can run in parallel with `[P]`. Every AC is covered by at least one task (AC coverage table).

## Stage 4 — Implement

Work one task at a time. After each task:

1. Run level 1, `scripts/check.sh`, and level 2, the related eval cases, if the change affects the agent, its prompt, tools or RAG (`testing-strategy.md`). Fix until green.
2. Tick the task in `tasks.md` and add a short dated **Result** note under it: what was done, what was measured,
   anything surprising. These notes are the evidence Stage 5 checks.
3. Record decisions in `memory/decisions.md` and gotchas in `memory/learnings.md` as they happen.

For an important test, prove it can fail: break the code briefly, see the test fail, restore.

## Stage 5 — Verify

Run every gate in the Definition of Done (`constitution.md`): `scripts/check.sh`, `scripts/evals_local.sh`, `cd web && npm run build`, and the measurements the feature affects. Run the slow ones once, in the background, and carry on with docs and memory meanwhile. Then:

- Check each AC against its test or measurement; tick only the proven ones. Set `Status: Implemented`.
- Update `roadmap.md`, add a `memory/progress.md` entry, refresh "Current State" in `memory/MEMORY.md`.
- Report honestly anything that failed, was flaky, or was skipped.

## Changing a spec mid-flight

Stop. Edit `spec.md`, add a line to its **Changelog**, log the decision in `memory/decisions.md`, and re-check
`plan.md`/`tasks.md` for impact (add tasks if needed) — then write the code. Never silently diverge code from spec.

## Slash commands (Claude Code)

Shortcuts in `.claude/commands/`:

| Command                 | Does                                                            |
| ----------------------- | --------------------------------------------------------------- |
| `/spec-new <name>`      | Creates the next numbered feature folder with a draft `spec.md` |
| `/spec-plan <NNN>`      | Writes `plan.md` for an approved spec                           |
| `/spec-tasks <NNN>`     | Writes `tasks.md` from the plan                                 |
| `/spec-implement <NNN>` | Implements the next unchecked task(s), running tests            |
| `/spec-verify <NNN>`    | Runs the Definition-of-Done checklist and updates docs/memory   |
