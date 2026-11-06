# Testing Strategy

## Test Levels

Run the cheapest level that can catch the problem. The slow level runs once per feature, in the background, and nobody waits for it.

| Level | What runs | When | Time |
| ----- | --------- | ---- | ---- |
| 1. Fast | `scripts/check.sh` | Every task | About 1 min |
| 2. Targeted | `scripts/evals_local.sh -k <related cases>` | A task changes the agent, its prompt, tools or RAG | Under 1 min |
| 3. Full | `scripts/evals_local.sh`, plus the measurements below that apply | Once per feature, at Verify | 4 to 20 min |

`evals/measure_policy.py` runs at level 3 only when the feature touches what it measures:

| Measurement | Run it when these changed |
| ----------- | ------------------------- |
| `refunds` | The system prompt, the refund path, or the agent loop in `graph.py` |
| `starters` | The system prompt, the policies, or `web/src/chat/starters.ts` |
| `care` | The system prompt, `warranty.md`, or `POLICY_TOPIC` |

While level 3 runs, carry on with docs and memory. Stop only if it fails or needs the owner's decision. Run level 3 again only if a change
after it could affect the result. A task isn't ticked on level 3's behalf: a feature isn't Implemented until level 3 passes.

## Test Layers

`scripts/check.sh` runs the first two layers.

| Layer | Tool | Location | What it covers | Command |
| ----- | ---- | -------- | -------------- | ------- |
| Backend unit | pytest, scripted fake model | `tests/` | Graph, service, guardrails, API, MCP, chunking, AWS defaults | `uv run pytest` |
| Frontend unit | Vitest | `web/src/**/*.test.ts` | Stream handling, replayed through the reducer | `cd web && npm test` |
| Integration | pytest, real Postgres and MCP | `evals/test_integration.py` | Upgrades, Postgres backends, the MCP boundary, races. Uses a scratch database, except one test that needs the real model and removes its own rows | `scripts/evals_local.sh -k integration` |
| Evals | pytest, real model | `evals/test_golden.py` | Behaviour of the whole system, 33 cases, 12 of them attacks | `scripts/evals_local.sh` |
| Evals on AWS | pytest, Bedrock | `evals/` | The 20 cases that don't need accounts, on Claude | `RUN_EVALS=1 uv run pytest evals -v` |
| Browser | Manual, or a throwaway script kept out of the repo | none yet | UI flows as each level, client-side isolation | See the backlog |

## Rules

1. **Test-first for pure logic.** Write the failing test, then the code.
2. **Time and randomness are inputs.** Logic takes time/seeds as parameters so tests are deterministic.
3. **No flaky waits.** Wait on real signals (events, DOM attributes, readiness endpoints), not fixed sleeps. A
   flaky test is a bug: find the race, don't add retries.
4. **Prove important tests can fail** by briefly breaking the code they cover.

5. **Unit tests stay offline.** No Docker, LM Studio or AWS. `tests/conftest.py` clears the settings to keep it so.
6. **Evals check outcomes, not wording:** tools, status, key phrases, side effects.
7. **Read every eval failure.** The test may be the broken part. Never re-run until green.
8. **A local pass proves nothing about Claude.** Qwen judges itself locally, and regex guardrails match the
   suite's exact attacks, so report local scores with that caveat.
9. **Prompt changes need the full evals**, with `EVAL_RUNS=3` when the change matters, since results can vary between runs.
10. **Security tests need a sabotage check.** Remove the protection and confirm the test fails. A security test you've
    never seen fail proves nothing.
11. **"No leaks" needs a positive control.** Check that the right user still gets their data. A system that refuses
    everyone, or treats everyone as one user, also shows no leaks.
12. **Walking "all routes" must assert it saw them.** Check that known routes were in the list.
13. **Measure rates with interleaved prompts.** LM Studio's prompt cache makes repeated prompts repeat their outcome, so
    runs aren't independent. Put other questions between samples.
14. **Sabotage away from real data.** `scripts/evals_local.sh` resets the demo orders. Restart `mcp` before trusting a
    live result after changing `mcp_server.py`.

## Commands

```bash
scripts/check.sh                         # level 1: must pass before any task is ticked
scripts/evals_local.sh -k care_          # level 2: only the related eval cases
uv run pytest && (cd web && npm test)    # unit tests only
scripts/evals_local.sh                   # end-to-end; needs docker compose up + LM Studio; EVAL_RUNS=3 repeats it
cd web && npm run build                  # production build
uv run ruff check --fix src tests evals  # format
```
