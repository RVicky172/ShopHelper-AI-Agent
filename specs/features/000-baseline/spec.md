# 000 — Baseline

**Status:** Implemented
**Roadmap phase:** 0 · **Created:** 2026-11-04 · **Owner:** RVicky172

## Summary

Records what existed when spec-driven development was adopted, so later specs have a known starting point. This
was built before the workflow existed, so it has no `plan.md` or `tasks.md`, and each criterion below records what
was actually run on 2026-11-04.

## User Stories

- **US-1:** As a learner, I want to run the whole agent on my machine, so that I can see how it works at no cost.
- **US-2:** As a learner, I want to watch each step of a turn, so that the agent isn't a black box.
- **US-3:** As the owner, I want the AWS code kept intact, so that I can deploy when I'm ready.

## Acceptance Criteria

- [x] **AC-1:** `docker compose up --build` from an empty state starts every service, and setup embeds 9 documents
      into 20 chunks. _(manual: run after `docker compose down -v`)_
- [x] **AC-2:** All 20 golden evals pass on the local stack. _(e2e: `scripts/evals_local.sh`; four clean runs)_
- [x] **AC-3:** A refund pauses, survives an API restart, and on approval the order becomes `refunded` in Postgres.
      _(manual: scripted against the running stack)_
- [x] **AC-4:** The UI streams answers, shows each step, and completes an approval with no console errors, including
      at 390 px wide. _(manual: Playwright script, not committed)_
- [x] **AC-5:** pgAdmin opens the database with no login or password prompt. _(manual: browser)_
- [x] **AC-6:** Default settings select Bedrock and DynamoDB, and hide local routes. _(unit: `test_local_stack.py`;
      manual: production image started with AWS settings)_
- [x] **AC-7:** `infra/` has no changes and `terraform validate` passes. _(manual)_

## Non-Functional Requirements

- Measured on an RTX 5080: about 45 tokens per second, and a first token in about 2-5 seconds.

## Out of Scope

- Anything needing real AWS. Claude has never run in this project, so the eval results apply to Qwen only.
- Hosting the UI on AWS.

## Open Questions

None.

## Changelog

- 2026-11-04 — Created to record the existing system.
