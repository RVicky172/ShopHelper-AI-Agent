---
title: Test levels
checked: 2026-11-06
---

## What you'll learn

- The layers of testing in an AI project
- How to run the cheapest test that can catch a problem
- Why slow tests shouldn't block you
- How to prove a test can fail

## The simple explanation

A car goes through different checks. A quick look at the tyres before every drive. A proper service once a year. A crash test once per model. You'd never crash-test before the school run, and a tyre check can't replace the crash test.

Software is the same. Fast checks run all the time, and slow ones run rarely.

The rule: **run the cheapest level that can catch the problem.**

| Layer | Tests | Needs | Speed |
| --- | --- | --- | --- |
| Lint and types | Typos and wrong shapes | Nothing | Seconds |
| Unit | Your logic, with fakes | Nothing | Seconds |
| Integration | Parts working together | Database, services | Under a minute |
| Evals | Whole-system behaviour | Real model | Minutes |
| Measurements | Rates over many runs | Real model | Longer |

## An example

This lesson came from a real complaint. Early on, every small task re-ran the full evals, three times over. The owner of this project said it plainly: most of the time they were sitting doing nothing.

The tests weren't wrong. They were running at the wrong moment. A docs edit can't break refunds, so why run the refund evals?

The fix was three levels, decided by what changed:

| Level | What runs | When | Time |
| --- | --- | --- | --- |
| 1. Fast | `scripts/check.sh` | Every task | About 1 minute |
| 2. Targeted | `scripts/evals_local.sh -k <cases>` | A task changes the agent, prompt, tools or RAG | Under 1 minute |
| 3. Full | All evals, plus measurements that apply | Once per feature | 4 to 20 minutes |

Level 3 runs in the background while you carry on, and you stop only if it fails. Evals now run once by default, and `EVAL_RUNS=3` repeats them when a change really matters. Nothing was lost, because every level still runs. They just run when they can tell you something.

## How ShopHelper does it

**Level 1** is one script, with no Docker or model needed, so it also works in CI:

```bash file=scripts/check.sh
uv run ruff check src tests evals
uv run pyright
uv run pytest -q
```

It runs 387 backend and 95 frontend tests, plus lint and types.

**Level 2** picks related cases by name. Six cases match `care_`, so a change to Care questions tests only those:

```bash
scripts/evals_local.sh -k care_
```

**Integration tests** run against real Postgres and MCP, using a scratch database. There are 44 of them. They cover what fakes can't, such as 8 reviewers racing for one refund.

**Measurements** answer questions a single case can't. `evals/measure_policy.py` asks each question many times, with an unrelated question between each, because of the caching problem in the [last lesson](01-why-testing-ai-differs.md). They run only when what they measure has changed:

| Measurement | Run it when these changed |
| --- | --- |
| `refunds` | The system prompt, the refund path, the agent loop |
| `starters` | The system prompt, the policies, the starter questions |
| `care` | The system prompt, `warranty.md`, the topic pattern |

**Proving a test can fail.** A passing test might be passing for the wrong reason. So for security tests, this project breaks the code on purpose. The 7 cross-user attacks were checked two ways:

1. **Did they reach the code under test?** All 7 called the order tool, so no guardrail was doing the work.
2. **Do they fail without the protection?** With the owner check removed, all 7 failed.

A security test you've never seen fail hasn't proved anything.

This is sometimes called sabotage testing, and it found real problems. A test that walked every route once skipped half of them without saying so.

## In the market

Checked on 2026-11-06.

The classic picture is the **test pyramid**: many fast tests at the bottom, fewer slow ones at the top. AI adds a layer above it, and that layer costs money each run, so the pressure to be selective is greater.

[Anthropic's guide](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) suggests starting with 20 to 50 tasks drawn from real failures, because early changes tend to have big effects, so small samples can show them.

Teams often split by trigger:

| Trigger | Runs |
| --- | --- |
| Every commit | Lint, types, unit tests |
| Every pull request | Plus integration, and a small eval set |
| Every night, or before release | The full evals |
| In production | Sampled scoring of real traffic |

ShopHelper's local version is simpler, and [evals in CI](08-evals-in-ci.md) shows what's automated and what isn't.

## Try it

1. Run `scripts/check.sh`, and time it.
2. See which cases a name selects, without running any:

```bash
uv run pytest evals --collect-only -q -k care_
```

3. **Prove a test can fail.** In `src/shophelper/shop/refunds.py`, change `request.owner_id == reviewer.user_id` to use `!=`. Run `uv run pytest tests/shop -q`, and watch the refund tests fail. Undo the change.

## Interview questions

### How do you decide what to test at each level?

**Strong answer:** I run the cheapest test that can catch the problem. Logic is unit tested with a fake model, in seconds. Database and race conditions need integration tests on real Postgres. Behaviour needs evals with the real model, and rates need repeated runs. In my project every task runs the fast gate, agent changes run related evals by name, and the full suite runs once per feature, in the background.

**Follow-up:** What stops the slow level being skipped?

### Evals are slowing your team down. What do you change?

**Strong answer:** I'd check when they run before cutting any. I hit this: every small task re-ran the full suite three times. I split it into three levels based on what changed, selected related cases by name, and moved the full run to once per feature, in the background. Coverage stayed the same, and people stopped waiting. Repeats became opt-in, for changes that matter.

**Follow-up:** How do you know you haven't lost coverage?

### How do you know a security test works?

**Strong answer:** I break the protection and see it fail. For my cross-user tests I checked two things: each attack reached the tool, so nothing else was stopping it, and all seven failed once I removed the owner check. A test that has never failed might be testing nothing. I do it away from real data, and restore it afterwards.

**Follow-up:** Could you automate that?

## Check yourself

### You fix a typo in a lesson. What should run?

- [x] The fast gate — right: a docs change can't affect refunds.
- [ ] The full evals, three times — that's the waste this lesson removes.
- [ ] Nothing at all — the fast gate still checks docs.

### Why do integration tests exist, if unit tests pass?

- [ ] They're faster — they're slower.
- [x] Some things need the real parts, like races in a database — right: fakes can't show those.
- [ ] They replace evals — they don't use the model.

### What does a test you've never seen fail prove?

- [ ] That the code is right — it may be testing nothing.
- [x] Not much, until you've seen it fail — right: break the code once to check.
- [ ] That it's fast — that's unrelated.
