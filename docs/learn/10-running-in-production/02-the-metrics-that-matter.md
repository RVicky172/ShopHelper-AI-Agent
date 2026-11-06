---
title: The metrics that matter
checked: 2026-11-06
---

## What you'll learn

- The four golden signals
- Why averages hide problems
- Which metrics are special to agents
- How to tell when quality drifts

## The simple explanation

You can measure hundreds of things. Most won't help at 2 am.

Think of a car's dashboard. It doesn't show every sensor. It shows speed, fuel, temperature, and a warning light. Each one tells you something you'd act on.

Start with Google's [four golden signals](https://sre.google/sre-book/monitoring-distributed-systems/):

| Signal | Means | For an agent |
| --- | --- | --- |
| **Latency** | How long it takes | Time to first token, and to finish |
| **Traffic** | How much demand | Turns per minute |
| **Errors** | How many fail | Failed turns, failed tools |
| **Saturation** | How full you are | Model quota, GPU, connections |

Then add what's special to AI:

| Group | Metric | Tells you |
| --- | --- | --- |
| **Cost** | Tokens and dollars per turn | Whether the bill is safe |
| **Agent** | Steps per turn, tool error rate | Whether it's struggling |
| **Quality** | Sampled faithfulness | Whether answers are right |
| **Outcome** | Resolved, escalated, thumbs down | Whether it helped |
| **Safety** | Guardrail blocks, refunds pending | Whether something's wrong |

Outcome is what the business cares about, and it's the hardest to measure.

## An example

We summarised this project's real log lines, 66 turns from a working session. It's a mix, including a load test, so don't read much into the values. Read how they're shown:

| Measure | Value |
| --- | --- |
| Turns | 66 |
| Median latency | 2.95 s |
| 95th percentile | 9.69 s |
| Slowest | 10.83 s |
| Answered | 62 |
| Pending approval | 3 |
| Blocked | 1 |
| Input tokens, average | 1,469 |
| Output tokens, average | 79 |

**The median and the 95th percentile tell different stories.** A typical person waited 3 seconds. One in twenty waited about 10. An average blends those into a number nobody felt.

That's why teams quote percentiles. **p95** means 95% of turns were faster than this. If you have thousands of users, your p95 isn't rare. It happens all day.

The tools tell a story too:

| Tool | Calls |
| --- | --- |
| `search_policy` | 35 |
| `get_order_status` | 11 |
| `request_refund` | 3 |
| No tool at all | 19 turns |

Is 19 turns with no tool good? It might be greetings, or it might be the model skipping a search it should've done, which is the [Care bug](../05-rag/08-debugging-a-wrong-answer.md). The number can't tell you. It tells you where to look.

## How ShopHelper does it

The fields come straight from the log line, so a new metric is one filter on AWS:

```hcl file=infra/observability.tf
LatencyMs       = { pattern = "{ $.event = \"chat_completed\" }", value = "$.latency_ms" }
```

The dashboard shows latency at p50 and p90, not an average.

| Group | Have it? |
| --- | --- |
| Golden signals | Traffic, latency, errors. Saturation only through AWS's own graphs |
| Cost | Tokens, and estimated cost |
| Agent | Tools are logged, with no metric for tool errors or steps |
| Quality | Only in evals, not on real traffic |
| Outcome | **None.** No feedback button, and no resolved flag |
| Safety | Guardrail blocks and pending refunds |

**Time to first token** matters for a streaming UI, because it's the wait people feel. `scripts/compare_deployments.sh` measures it, and the logs don't record it. We measured it by hand in [streaming](../06-building-the-app/03-streaming.md): 2.33 seconds of 4.86.

**A watch-out with blocked turns.** A sudden rise in guardrail blocks might be an attack. It might also be a new rule catching normal customers. Both show the same number.

## In the market

Checked on 2026-11-06.

**SLOs, service level objectives**, turn metrics into promises. For example: 95% of turns finish in under 8 seconds, and 99.5% don't error. An **error budget** is what's left: if you've used it up, stop shipping risky changes and fix reliability. Quality can have one too: 98% of sampled answers are faithful.

**Drift** means behaviour changing over time, without a code change:

| Kind | Example | Sign |
| --- | --- | --- |
| **Input drift** | Customers start asking about a new product | More "I don't know" answers |
| **Model drift** | A provider updates a model | Scores shift overnight |
| **Knowledge drift** | Policies change, and documents don't | Faithful but wrong answers |
| **Cost drift** | Conversations grow longer | Tokens per turn rise |

To spot these, build a baseline from a stable period, then compare. Tools call this **online evaluation**: score a sample of real traffic. It catches what [offline evals](../07-evals-and-testing/03-golden-sets.md) can't, because real questions aren't in your golden set. Scoring every request can be costly, so sample.

**Alert on symptoms, not causes.** The [Google SRE book](https://sre.google/sre-book/monitoring-distributed-systems/) makes this point: page someone for "users are getting errors", not for every internal wobble. Too many alerts teach people to ignore them.

**User feedback** is cheap and useful: a thumbs up or down, whether they asked for a human, or whether they came back with the same question. Few people click, and those who do lean negative, so treat it as a signal, not a score.

## Try it

1. Run this, and find your own median:

```bash
docker compose logs api --no-log-prefix | grep chat_completed | grep -o '"latency_ms": [0-9]*' | sort -t: -k2 -n
```

2. Find the turn at 95% of the way down the list. How far is it from the median?
3. Pick three metrics you'd put on a phone screen for this shop. Say what you'd do when each one moves.
4. Write one SLO for the chat. How would you measure it with the data here?

## Interview questions

### What metrics would you track for an AI agent?

**Strong answer:** The golden signals first: latency as percentiles, including time to first token, plus traffic, errors and saturation, which usually means model quota. Then cost per turn, steps and tool errors, sampled quality like faithfulness, and outcomes such as resolution and escalation. Outcome matters most, and it's hardest. My project logs tokens, tools, status and latency for each turn, and it has no outcome data yet, which is what I'd add next.

**Follow-up:** How would you define "resolved"?

### Why use percentiles and not averages?

**Strong answer:** An average hides the people having a bad time. In my logs the median was about 3 seconds, and p95 was about 10. The average would be somewhere in between, describing nobody. With many users, the slow tail happens constantly. So I alert on p95 or p99, and track median to see typical experience.

**Follow-up:** Why might p99 be misleading on low traffic?

### How would you detect that quality is slowly getting worse?

**Strong answer:** Score a sample of real traffic against a baseline from a stable period, and watch the trend. I'd also watch proxies: more escalations, more "I don't know", more repeated questions, and changes in tool use. Regular runs of the golden set catch provider-side changes. A slow change won't trip a threshold, so I'd compare week on week. And someone reads a sample by hand.

**Follow-up:** How big a sample do you need?

## Check yourself

### What does p95 latency of 10 seconds mean?

- [ ] The average is 10 seconds — it isn't an average.
- [x] 95% of turns were faster than that — right: the slow tail is one in twenty.
- [ ] 95 turns took 10 seconds — that's not it.

### Guardrail blocks suddenly rise. What does it show?

- [ ] An attack — it might be.
- [ ] A bug — it might be.
- [x] Something to look at — right: the number alone can't tell you which.

### Which is the hardest to measure, and matters most?

- [ ] Latency — that's easy.
- [x] Outcomes, such as resolved conversations — right: it's what the business cares about.
- [ ] Token count — that's logged on each turn.
