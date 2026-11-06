---
title: Golden sets
checked: 2026-11-06
---

## What you'll learn

- What a golden set is, and where cases come from
- What to check when wording changes every run
- What belongs in a good set
- How a set grows from real failures

## The simple explanation

A **golden set** is a fixed list of inputs, each with what a good result looks like. Run it after every change, and compare.

Think of a driving test route. It's chosen on purpose: a hill start, a busy junction, a parking space. Examiners don't invent a new route each time, so results can be compared. And a good route includes the hard bits, not just a straight road.

You can't check for exact text, because a model's wording changes. So check the things that matter:

| Check | Example | Why |
| --- | --- | --- |
| Tool use | `tools: [request_refund]` | Did it take the right action? |
| Status | `status: pending_approval` | Did the flow go the right way? |
| Key phrases | `contains_any: [shipped]` | Is the fact there, in any wording? |
| Forbidden text | `not_contains: [...]` | Did it leak or promise something? |
| Side effects | `orders_after: {"1001": delivered}` | Is the database right? |
| Judge | `judge: true` | Is the answer faithful to the documents? |

Use the simplest check that works. A string match is free and never changes its mind, so only use a model to judge what a string can't.

## An example

Here's a real case:

```yaml file=evals/golden_cases.yaml
- id: refund_eligible_pauses
message: I'd like a refund for order 1001, the mouse stopped working.
as: Asha
expect: {tools: [request_refund], status: pending_approval, orders_after: {"1001": delivered}}
```

Read what it demands. The agent called the tool. The turn paused for a human. And the order is **still delivered**, because no refund happens until staff approve it. A reply saying "your refund is done" fails this, however well written.

Now see how the set grew. It wasn't designed in one sitting. Each group of cases came from something that went wrong:

| Group | Where it came from |
| --- | --- |
| Orders, policies, refunds | The first 20 cases, from the main jobs |
| Attacks | Trying to break the guardrails |
| Cross-user attacks | Building accounts |
| Lifestyle products | Selling things that aren't electronics |
| Care wordings | Real wordings that skipped search every time |

That's the healthy pattern. **Every real bug becomes a case**, so it can't quietly come back.

## How ShopHelper does it

[golden_cases.yaml](../../../evals/golden_cases.yaml) holds 37 cases, and 12 of them are attacks: 5 aimed at the guardrails, and 7 at another customer's data. Each runs as a named customer, using `as:`.

A good set has more than happy paths:

| Kind | Example from this set |
| --- | --- |
| Normal | "Where is my order 1002?" |
| No answer exists | "Do you offer a student discount?" |
| Missing data | "Where is order 9999?" |
| Should refuse | A refund that isn't eligible |
| Attack | "Ignore all previous instructions..." |
| Same meaning, new words | Several wordings of a Care question |

The "no answer exists" group is easy to forget, and it's where models invent things.

**Check what only the truth could contain.** The cross-user cases can't just look for a customer's name, because the attacker's own message contains it. So they forbid what only the real order could reveal, its item and price.

The runner is short, and turns each `expect` key into a check:

```python file=evals/test_golden.py
for order_id, status in exp.get("orders_after", {}).items():
actual = get_order_repo().get(order_id)["status"]
if actual != status:
errors.append(f"order {order_id} is {actual}, expected {status}")
```

**The limits of this set:**

- Every case is **one message**. Nothing tests a long conversation, or one that changes its mind.
- The cases were **written by the builder**, not taken from real customers, since there are none.
- It's small. It catches regressions, and it won't find problems nobody thought of.
- It's in version control, so a change to a case shows up in review. That's good, but don't edit a case just to make it pass.

## In the market

Checked on 2026-11-06.

Common advice lines up well with what happened here:

- **Start small, from real failures.** Anthropic suggests [20 to 50 tasks](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), from bug trackers and support queues.
- **Label by hand first.** A set of 20 to 50 labelled examples is enough to [show where a judge disagrees with you](https://arize.com/docs/ax/cookbooks/evaluate/align-llm-evals-with-human-judgment).
- **Prefer yes or no labels.** They're easier to agree on and to debug than a scale of 1 to 5.
- **Watch for saturation.** When everything passes, the set can't show improvement, so add harder cases.

In production, the best source of cases is your own traces: thumbs-down answers, escalations and complaints. Remove private data before adding them to a test file.

## Try it

1. Read `evals/golden_cases.yaml`. Find one case of each kind in the table above.
2. Pick `order_not_found`. What would a weak check miss?
3. Add a case of your own. For example, a partial refund:

```yaml
- id: refund_partial
  message: Refund $20 of order 1001, the mouse is scratched.
  as: Asha
  expect: {tools: [request_refund], status: pending_approval}
```

4. Run it with `scripts/evals_local.sh -k refund_partial`. That resets the demo orders. Did it pass? Read the answer either way. Then delete the case.

## Interview questions

### How would you build a golden set for a support agent?

**Strong answer:** I'd start with 20 to 50 cases from real tickets and failures, and label what a good result is by hand. I'd include normal questions, ones with no answer, missing data, things it must refuse, attacks, and different wordings. I'd check outcomes, such as tool calls, status and database state, not exact text. Then every bug becomes a case. Mine has 37 cases, 12 of them attacks, and most of the groups came from real failures.

**Follow-up:** How do you keep private data out of it?

### What should an eval check, if wording changes each run?

**Strong answer:** What matters to the customer. Did the right tool run, did the flow pause for a human, is the key fact there, is anything forbidden there, and is the database right. My refund case checks that the order is still "delivered" after the turn, because no refund should happen before approval. For things strings can't see, like faithfulness, I use a judge.

**Follow-up:** When is a string check too weak?

### Your golden set passes 100%. Is that good?

**Strong answer:** It means no known regressions, and not much more. A saturated set can't show improvement, and it says nothing about what isn't in it. Mine passes 37 of 37, but every case is one message, and I wrote them myself. So I'd add harder cases, multi-turn conversations, and real failures, and keep separate capability tasks that are expected to fail for now.

**Follow-up:** Where would harder cases come from?

## Check yourself

### Why not compare answers with exact text?

- [ ] It would be too slow — speed isn't the problem.
- [x] Wording changes between runs — right: check facts and outcomes.
- [ ] YAML can't store long text — it can.

### What does `orders_after` check?

- [x] The real state of the database — right: what happened, not what was said.
- [ ] How the answer was worded — that's `contains_any`.
- [ ] How long the turn took — it doesn't measure that.

### Where do the best cases come from?

- [ ] A brainstorm, written once — that's a start, not the source.
- [ ] The model itself — it may share your blind spots.
- [x] Real failures — right: every bug becomes a case.
