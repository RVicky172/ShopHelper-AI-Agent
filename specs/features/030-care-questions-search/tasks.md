# 030 — Care Questions Always Search the Policy · Tasks

**Plan:** `./plan.md`
Legend: `[P]` = can run in parallel with the previous task. Each task lists files and the proving test.
Test-first: each "tests" task must fail before its paired implementation makes it pass.
When a task is done, tick it and add an indented **Result (YYYY-MM-DD):** note: what was done, numbers measured,
anything surprising or deferred.

## Setup

- [x] **T001** — Write the measurement script, with the 8 D-016 wordings and at least 8 new ones, fixed before any fix exists (AC-2) ·
      files: `evals/measure_policy.py` · test: `care` mode on today's code gives about 12 of 24 on the 8 D-016 wordings, and records a
      baseline for the new ones
      **Result (2026-11-06):** 16 wordings fixed before any fix. Baseline on the old code, 3 rounds: D-016 wordings searched 12 of 24, exactly
      as in D-016, and new wordings 18 of 24, so the problem wasn't limited to the known ones. 6 wordings skipped every time. One answer told
      the customer to "call search_policy".
- [x] **T002** — Add `refunds` and `starters` modes, from the 021 scratch scripts, with at least 12 of the 60 refund attempts mentioning a
      warranty · files: `evals/measure_policy.py` · test: both run end to end, and the temporary order is gone afterwards
      **Result (2026-11-06):** Both ran end to end in the T033 and T034 measurements, and the temporary order was removed.
- [x] **T003** — Spike, thrown away afterwards: patch the search in, run `care` on the 8 D-016 wordings, and read every answer · files:
      `src/shophelper/graph.py` (temporary) · test: `warranty.md` comes back and answers are correct. **If they stay poor, stop and report.**
      **Result (2026-11-06):** Searched 16 of 16, but 2 answers were wrong and the keyword check passed both: a laptop stand "not an electronic
      product", and a desk mat called lifestyle. Cause: retrieval. The Care chunk comes back without the chunk defining electronics, so the
      model guessed. Fixed by naming the categories in the Care line (D-019). Then all 16 correct on reading. Spike code removed.

## Tests First

- [x] **T010** — Failing tests: protected questions search before the model runs, with 0 extra model calls, and again on a repeated
      question (AC-1 logic, AC-4, AC-8) · files: `tests/test_graph.py`
      **Result (2026-11-06):** Written with T011 and T012. 12 failed on the old behaviour, for the right reason.
- [x] **T011** [P] — Failing tests: at least 10 near misses get no forced search, and Q1's terms match in any letter case (AC-7) · files:
      `tests/test_graph.py`
      **Result (2026-11-06):** 10 near misses and 7 protected wordings. Near misses passed before and after, as they should.
- [x] **T012** [P] — Failing tests: a failed search gives the fixed reply with no model call, and the stream has no `token` before
      `tool_end` (AC-5, AC-6) · files: `tests/test_graph.py`
      **Result (2026-11-06):** Also covers a failed search on another topic staying with the model, and a refund that mentions a warranty.

## Core

- [x] **T020** — Pattern, `_current_turn`, `_needs_policy_search`, and the first branch in `agent()`; the refund check reuses `_current_turn` ·
      files: `src/shophelper/graph.py` · test: T010, T011
      **Result (2026-11-06):** `POLICY_TOPIC`, `_current_turn`, `_needs_policy_search`, `_search_first`. Refund check reuses `_current_turn`.
- [x] **T021** — `_search_failed`, `NO_POLICY_ANSWER`, and the second branch in `agent()` · files: `src/shophelper/graph.py` · test: T012
      **Result (2026-11-06):** `_policy_search_failed` matches by `tool_call_id`, because `run_tool`'s error message has no tool name.
      `scripts/check.sh`: 354 backend, 82 frontend.
- [x] **T022** — Update the script of the MCP warranty test, which now searches through code · files: `tests/test_mcp.py` · test:
      `scripts/check.sh`
      **Result (2026-11-06):** Script drops the model's search call. Also added a test pinning the Care line's wording.

## Integration

- [x] **T030** — Add the 4 wordings that failed in D-016 to the golden evals, making 37 cases · files: `evals/golden_cases.yaml` · test:
      `scripts/evals_local.sh`, all pass
      **Progress (2026-11-06):** 37 cases. First full run: 36 of 37, 93 of 94 with integration. `lifestyle_not_off_topic` failed: the model invented
      order 12345 and called `request_refund` on a general question. The message has no protected term, so the new check didn't run. 0 of 10
      on repeat, interleaved. A rare model error, and code refused the unknown order. One clean full run is still needed.
      **Result (2026-11-06):** Clean full run: 37 of 37, 94 of 94 with integration, faithfulness 5.0.
- [x] **T031** — Sabotage: remove the check and confirm at least 3 of the 4 new cases fail, then restore and restart `api` and `mcp` · files:
      `src/shophelper/graph.py` (temporary) · test: recorded result (AC-11)
      **Result (2026-11-06):** Check removed: 4 of 4 new cases failed, 2 of 6 Care cases passed. Restored, and `cmp` confirmed the file.
- [x] **T032** — Measure Care questions: 24 of 24 on the 8 D-016 wordings, 24 of 24 on the new ones, all 48 answers read (AC-1, AC-2, AC-3) ·
      test: `evals/measure_policy.py care`
      **Result (2026-11-06):** Searched 24 of 24 and 24 of 24, up from 12 and 18. All 48 answers read: facts correct. The 3 rounds repeat almost
      word for word, so that's about 18 distinct answers, not 48. One nit: the portable charger answer says Care "adds 2 years" where the
      policy says it extends coverage to 2 years.
- [x] **T033** — Measure refunds at 60 of 60, with at least 12 mentioning a warranty (AC-9) · test: `evals/measure_policy.py refunds`
      **Progress (2026-11-06):** 59 of 60, so AC-9 isn't met. The miss: "It's under warranty, please refund order 1006", where the agent asked for a
      reason. Diagnosed on that wording, 12 attempts each, interleaved: 6 of 12 submit with the check, 0 of 12 without. So the wording was already
      hard, and the check helps. Without it the agent also gave a laptop stand a 90-day warranty. Needs the owner's call.
      **Progress (2026-11-06):** After D-022, re-measured with a wording that states a problem: 52 of 60, so AC-9 still isn't met. 45 of 45 attempts with no
      warranty mention submitted, and 7 of 7 on "This is still under warranty and it stopped working". "It's under warranty and it stopped working,
      please refund" got 0 of 8: the agent says refunds aren't issued for items under warranty, which contradicts `refunds.md`. Checked with the 030 check
      on and off, 8 attempts per wording: 0 and 8 of 8 on, 0 and 4 of 8 off. So it's an older bug, not caused by the check. Needs the owner's call.
      **Result (2026-11-06):** Closed on the owner's decision (D-023): 45 of 45 with no warranty mention. A further 60-attempt run was stopped unfinished, so it counts for nothing.
- [x] **T034** [P] — Measure starters at 57 of 57, reading any flagged by the strict check (AC-10) · test:
      `evals/measure_policy.py starters`
      **Result (2026-11-06):** 57 of 57 on reading. The strict check said 51: all 6 are complete answers ending in an offer to look up an order,
      5 on the cancellation policy and 1 on Yoga Mat returns.
- [x] **T035** — Browser check in the chat widget: a Care question streams with no answer withdrawn, with failed responses listed by URL
      (AC-6) · test: recorded here
      **Result (2026-11-06):** Asked in the chat widget and on the trace page. Correct answer in both, with the search listed before the answer.
      No page errors, and the only failed response was the expected signed-out `401 GET /api/auth/me`. The test conversation was removed.
      Also found the web app blank since the 09:57 `git checkout`: see learnings.

## Docs

- [x] **T040** — Explain why a prompt wasn't enough, with the real numbers and a Try it step that was run; note the 0-token `model_step` ·
      files: `docs/learn/01-agents-and-the-loop.md`, `docs/learn/06-streaming.md` · test: Try it step run (AC-12)
      **Result (2026-11-06):** Chapter 1 has the real numbers and code, chapter 6 the note. Try it step 5 was run in the browser. The trace labels the
      code's step "Model call 1", which isn't accurate, so the step says so.
- [x] **T041** [P] — Case count 33 to 37 · files: `README.md`, `docs/learn/09-evals.md`, `docs/local-setup.md`, `specs/testing-strategy.md`
      **Result (2026-11-06):** Case counts updated to 37, and the backend test count to 354.
- [x] **T042** — Close the gap on record: update D-016, 021's AC-39 note and the roadmap (AC-13) · files: `memory/decisions.md`,
      `specs/features/021-storefront/spec.md`, `specs/roadmap.md`
      **Result (2026-11-06):** D-016 marked closed and 021's AC-39 note updated. The roadmap entry had already moved from the backlog to 030.

## Verify

- [x] **T090** — Update `specs/architecture.md` with what this feature established.
      **Result (2026-11-06):** `graph.py`'s row records that code can write a tool call.
- [x] **T091** — Every Definition-of-Done gate green (`specs/constitution.md`); record the numbers.
      **Result (2026-11-06):** `scripts/check.sh` passed (354 backend, 82 frontend), build passed, evals 37 of 37 and 94 of 94, faithfulness 5.0. `infra/` unchanged.
- [x] **T092** — Tick ACs in `spec.md` (Status `Implemented`), update `roadmap.md`, `memory/progress.md`,
      `memory/MEMORY.md`.
      **Result (2026-11-06):** 13 of 13 criteria ticked, Status `Implemented`, roadmap and memory updated.

## AC coverage

| AC    | Tasks            |
| ----- | ---------------- |
| AC-1  | T001, T010, T020, T032 |
| AC-2  | T001, T032       |
| AC-3  | T003, T032       |
| AC-4  | T010, T020       |
| AC-5  | T012, T021       |
| AC-6  | T012, T021, T035 |
| AC-7  | T011, T020       |
| AC-8  | T010, T020       |
| AC-9  | T002, T033       |
| AC-10 | T002, T034       |
| AC-11 | T030, T031       |
| AC-12 | T040             |
| AC-13 | T042             |
