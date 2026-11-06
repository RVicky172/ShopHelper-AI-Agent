---
title: Agent evals
checked: 2026-11-06
---

## What you'll learn

- Why agents are graded on outcomes, not fixed steps
- The difference between pass@k and pass^k
- How to measure a rate properly
- What this project's rates showed

## The simple explanation

An agent takes several steps, and more than one route can be right. So what do you grade?

Think of a taxi. You care that you arrived, on time, and were charged the right fare. You don't mark the driver down for taking a different road. But you'd still want to know if they drove through a red light.

So grade two things:

- **The outcome.** What's true in the world afterwards? Does the refund request exist? Is the order unchanged?
- **Rules on the path.** A few things must never happen, whatever the route: no refund without approval, no reading another person's order.

Don't check for an exact sequence of tool calls. It's brittle, and it fails good solutions you didn't think of.

Agents also vary, so one run tells you little. Two numbers describe repeated attempts:

| Metric | Means | Goes | Use when |
| --- | --- | --- | --- |
| **pass@k** | At least 1 of k tries worked | Up with k | One success is enough, like generating code you'll test |
| **pass^k** | All k tries worked | Down with k | People rely on it every time |

A support agent needs the second. Customers don't get to retry until it works.

## An example

Here's what that means for a real number from this project. Before a fix, Care questions ran the policy search in 30 of 48 runs, which is 62.5%.

| Trials in a row | pass^k, at 62.5% | At 95% | At 100% |
| --- | --- | --- | --- |
| 1 | 62.5% | 95% | 100% |
| 3 | 24% | 86% | 100% |
| 10 | 0.9% | 60% | 100% |

So at 62.5%, almost nobody gets ten good runs in a row. Even at 95%, 4 in 10 sets of ten questions contain a failure.

The fix was in code: search first, with no choice for the model. That made it 48 of 48. **When something must happen every time, take it away from the model.** [The agent loop](../03-agents/02-the-agent-loop.md) shows how.

A sample of 48 doesn't prove 100%, though. With no failures in 48 tries, the true failure rate could still plausibly be around 6%. That comes from the "rule of three": zero failures in n tries suggests the true rate is under about 3/n.

## How ShopHelper does it

**Outcomes.** The golden set reads the database after the turn:

```yaml file=evals/golden_cases.yaml
expect: {tools: [request_refund], status: pending_approval, orders_after: {"1001": delivered}}
```

**Tools, loosely.** The check says each listed tool must have been called. It doesn't care about order, or about extra calls:

```python file=evals/test_golden.py
for tool in exp.get("tools", []):
if tool not in resp.tools_used:
errors.append(f"tool {tool} not called (called {resp.tools_used})")
```

**Rates.** `evals/measure_policy.py` repeats questions, and it's careful about independence:

```python file=evals/measure_policy.py
Every question is followed by an unrelated one, because LM Studio's prompt cache makes repeated
```

| Measurement | Result |
| --- | --- |
| Refund requests submitted | 60 of 60 |
| Starter questions answered | 57 of 57 |
| Care questions, after the fix | 48 of 48 |

**Read them, too.** The script's own note says a count is only a first pass. At one point Care wordings "searched 16 of 16", but 2 answers were wrong, and the keyword check passed both. One said a laptop stand wasn't an electronic product. That led to the fix for the policy line. Counting alone would have called it done.

**What this doesn't measure:** multi-turn conversations, how a person feels about the answers, or how the agent recovers when a tool is down over many runs. Latency and tokens are recorded for each case, in `evals/report.json`: the last run had a median of about 2.3 seconds a turn, and used 46,493 input tokens across 37 cases.

## In the market

Checked on 2026-11-06.

From [Anthropic's guide](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents):

- A **task** can have several graders, and partial credit helps show progress on multi-part jobs.
- The **outcome** isn't what the agent says: a flight agent's outcome is whether the reservation exists.
- Its example is a 75% success rate giving about 42% for three in a row, which is 0.75 cubed.
- **Read the transcripts** before trusting a score, to confirm the grading was fair.

**Public benchmarks** are a place to start when choosing a model, and they can't replace your own tests. Tool use in your domain, with your tools and rules, is what you ship. Scores also rise over time, until a benchmark **saturates**, and stops separating models.

**Simulated users.** Some teams use a second model to play the customer, which lets you test multi-turn conversations at scale. It's useful, but the simulator has its own habits, so check it against real transcripts. This isn't built here.

## Try it

1. Work out pass^3 and pass^10 for a success rate you'd consider "pretty good", such as 90%.
2. Read `evals/measure_policy.py`, and find where the unrelated question is added.
3. Sign in, and on **How it works** ask "Refund my order 1001, the mouse stopped working" as Asha. In the trace, which tools ran? What's the order's status now? Then reject it as Support, so the demo data stays clean.

## Interview questions

### How do you evaluate an agent, as opposed to a single prompt?

**Strong answer:** I grade outcomes, because valid paths vary: what's in the database after the turn, not an exact tool sequence. Then I add path rules for things that must never happen, like a refund without approval. Since runs vary, I measure rates over repeated, independent trials. For a support agent I care about pass^k, since every customer needs it to work. And I read transcripts, because a count can pass wrong answers.

**Follow-up:** Why not just check the tool sequence?

### What's the difference between pass@k and pass^k?

**Strong answer:** pass@k is the chance at least one of k tries works, so it rises with k. pass^k is the chance all k work, so it falls. Use the first when one success is enough and you can verify it. Use the second when people depend on it. At 62.5%, which is how often my Care questions searched before a fix, three in a row is only 24%.

**Follow-up:** What did you do about it?

### An agent passes 48 of 48. Is it reliable?

**Strong answer:** It's a good sign, but not proof. With no failures in 48, the rule of three says the true failure rate could still be around 6%. So I ask whether the samples were independent, whether the wordings were varied, and whether I read the answers. In my case the behaviour was forced in code, which is stronger evidence than the count, since the model no longer chooses.

**Follow-up:** How many runs would you need to show 99.9%?

## Check yourself

### Why not grade the exact order of tool calls?

- [x] Valid agents can take different routes — right: grade the outcome.
- [ ] Tools run in random order — the point is that good paths vary.
- [ ] It's impossible to record them — traces record them.

### Which suits a customer-facing agent?

- [ ] pass@k — customers can't retry until it works.
- [x] pass^k — right: it has to work every time.
- [ ] Neither — reliability matters here.

### A behaviour must happen every time. What's the strongest fix?

- [ ] A stronger prompt — that's still a request.
- [ ] More eval cases — they measure, and don't fix.
- [x] Do it in code — right: the model no longer chooses.
