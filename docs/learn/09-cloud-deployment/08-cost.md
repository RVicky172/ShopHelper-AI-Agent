---
title: Cost
checked: 2026-11-06
---

## What you'll learn

- How to estimate what an agent costs
- Why the model usually dominates
- The main ways to reduce the bill
- How to stop a surprise

## The simple explanation

Normal web apps cost roughly the same however much each user does. AI apps charge per word, on every call. So cost follows usage closely, and one heavy feature can change the bill.

Think of a phone plan compared with a taxi meter. Servers are the plan: a fixed amount. Model calls are the meter: running whenever someone's talking.

The basic sum:

```text
cost per turn = input tokens × input price + output tokens × output price
monthly cost  = cost per turn × turns per month + fixed costs
```

Two things surprise people. **Agents make several model calls per turn**, each re-sending the conversation. And **input usually outweighs output**, because the system prompt, tools, history and passages go in every time.

## An example

Let's price 1,000 turns a day, or 30,000 a month. A real turn here uses about 1,750 input and 100 output tokens. Prices are [Anthropic's list prices](https://platform.claude.com/docs/en/about-claude/models/overview). Bedrock [sets its own](https://aws.amazon.com/bedrock/pricing/), so check there too.

| Item | Working | Per month |
| --- | --- | --- |
| Sonnet 5.5, $2 in and $10 out per million | $0.0045 a turn | **$135** |
| Or Haiku 5.5, $0.10 and $0.50 | $0.000225 a turn | **$6.75** |
| Lambda, 2 GB for 5 s | 300,000 GB-seconds | $5, or free in the free tier |
| API Gateway | 30,000 requests | $0.03 |
| Or Fargate and load balancer | Always on | $47 |

Three lessons:

**Model choice beats everything.** That's a 20-fold difference, far more than any compute decision. It's only worth it if the cheaper model still does the job, so [evals](../07-evals-and-testing/03-golden-sets.md) decide that, not the price list.

**Compute is the small part** on a good model, and it's still worth getting right, because at low traffic a fixed cost of $47 is the whole bill.

**It grows with tokens.** Double the history, and input cost doubles. Three model calls means three times the cost, or more.

These are estimates, from one real turn. A long conversation or a busy agent costs more, so measure your real average.

## How ShopHelper does it

**It records tokens on every turn:**

```python file=src/shophelper/api/app.py
tools=resp.tools_used, input_tokens=resp.input_tokens, output_tokens=resp.output_tokens,
```

On AWS, those log lines become metrics, and a dashboard shows estimated cost. You can't manage what you can't see.

**A budget is created first**, before anything that costs money. It emails at 50% of actual spending, and at 100% of forecast:

```hcl file=infra/budget.tf
limit_amount = tostring(var.monthly_budget_usd)
```

Note that a budget warns you. It doesn't stop anything.

**Cheap design choices:**

| Choice | Saved |
| --- | --- |
| S3 Vectors, not OpenSearch Serverless | About $12 a day idle |
| No NAT gateway | An hourly charge |
| On-demand DynamoDB | Nothing when idle |
| 7-day log retention | Storage |
| `enable_ecs = false` | About $1.56 a day |
| Teardown after testing | Everything |

**Fewer tokens.** Retrieval sends about 300 tokens of passages, not every policy. A guardrail block costs 0 tokens, because the model never runs. Code answers some cases with no model call.

**Local costs nothing per call**, which is why this project's evals can run freely. Your electricity and GPU are real costs, and that's a topic for [the next lesson](09-other-clouds-and-self-hosting.md).

## In the market

Checked on 2026-11-06.

The main ways to cut model costs, roughly in the order to try them:

| Technique | Saves | Catch |
| --- | --- | --- |
| Measure first | Finds the real cost | None |
| Trim prompts and history | Directly | May lose context |
| [Prompt caching](../01-how-llms-work/07-context-windows-and-prompt-caching.md) | About 90% on repeated input, on reads | Needs a stable prefix, and writes cost more |
| Smaller model for easy work | Up to 20 times, in the table above | Needs evals |
| Limit output length | Output is the dearer rate | May cut answers |
| [Batch API](https://platform.claude.com/docs/en/build-with-claude/batch-processing) | 50%, for work that can wait | Not for live chat |
| Cache whole answers | Whole calls | Stale or wrong matches |
| Fewer agent steps | Whole calls | Needs design |

**Routing.** A small model handles easy questions, and a bigger one takes hard ones. It can save a lot, but it adds a classifier, more evals, and a new way to fail. Try a single cheaper model first.

**Unit economics.** Work out cost per resolved conversation, not per call. A cheap model that needs three tries, or hands more to humans, may cost more overall. Compare it with what a human agent costs, too.

**Tags and cost allocation** show which feature spends what. Bigger teams set budgets per team.

**Hard stops.** Budgets alert, and they don't cut anything off. If a bill could hurt you, use your own limit that really stops calls.

## Try it

1. Sign in, and on **How it works** ask a question. Note the tokens in the trace.
2. Ask three follow-ups in the same conversation. How do input tokens grow?
3. Work out your own monthly cost: turns a day, tokens a turn, and a model's price.
4. Find what would change if every turn took two model calls.

## Interview questions

### What would this agent cost at 1,000 conversations a day?

**Strong answer:** I'd measure tokens first. A turn here is about 1,750 in and 100 out. So at 1,000 turns a day, Sonnet at $2 and $10 per million is about $135 a month, and Haiku at $0.10 and $0.50 is about $7. Conversations have several turns, and history grows, so I'd multiply by the real average. Compute is small: about $5 on Lambda, or $47 a month for always-on containers. So the model decision matters most.

**Follow-up:** What assumptions could be wrong?

### How do you reduce LLM costs without hurting quality?

**Strong answer:** Measure first, then the free wins: trim prompts and history, and use prompt caching. Then try a smaller model, with evals deciding if it's good enough. Then fewer steps, batching for offline work, and caching answers where that's safe. I judge by cost per resolved conversation, since a cheap model that fails more isn't cheap.

**Follow-up:** When wouldn't you use the cheapest model?

### How do you stop a runaway bill?

**Strong answer:** Layers. Step limits per turn, input limits, and per-user limits stop one source. Budgets and alarms tell me early, but note they don't stop anything. For real protection I'd have a hard limit in code that blocks calls past a spending level. In my project the budget is created first, turns are capped at 6 steps, and I tear down when I'm done. I don't have per-user limits yet.

**Follow-up:** How quickly would you find out?

## Check yourself

### What usually dominates an agent's running cost?

- [x] Model tokens — right: compute is often the small part.
- [ ] The load balancer — that's a fixed amount.
- [ ] Logs — usually small.

### What does an AWS budget do at its limit?

- [ ] Shuts everything down — it doesn't.
- [x] Sends an alert — right: it warns, and doesn't stop.
- [ ] Lowers your prices — sadly not.

### Why compare cost per resolved conversation?

- [ ] It's a smaller number — that's not why.
- [ ] Providers bill that way — they bill tokens.
- [x] A cheap model that fails can cost more overall — right: count the outcome.
