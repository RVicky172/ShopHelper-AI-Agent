---
title: Choosing a model
checked: 2026-11-06
---

## What you'll learn

- What really matters when choosing a model
- How to work out what a model will cost
- Hosted models against running your own
- Why you should plan to switch

## The simple explanation

There's no best model, only the best model for a job. Think of hiring. You wouldn't pay a senior surgeon to take blood pressure, and you wouldn't ask a trainee to do heart surgery.

Here's what to compare:

| Question | Why it matters |
| --- | --- |
| Is it good enough at *my* task? | Public scores may not match your work |
| How fast does it need to be? | A live chat and an overnight job differ |
| What does it cost at my volume? | Small per-call costs add up |
| Can my data go to it? | Some data can't leave your control |
| Does it have what I need? | Tool use, context size, languages |

Start with a capable model to prove the task can be done, then try cheaper ones and see what still passes. Your evals decide, not a leaderboard.

You don't need one model for everything either. A common pattern is a small, fast model for simple steps, and a stronger one for hard steps.

## An example

Here's a real turn from this project, 1,757 tokens in and 98 out, priced using [Claude's published rates](https://platform.claude.com/docs/en/about-claude/models/overview):

| Model | Price per million tokens, in / out | One turn | 1,000 turns |
| --- | --- | --- | --- |
| Haiku 5.5 | From $0.10 / $0.50 | $0.0002 | About $0.22 |
| Sonnet 5.5 | $2 / $10 | $0.0045 | About $4.50 |
| Opus 5.5 | $4 / $20 | $0.0090 | About $9 |
| Fable 5.1 | $10 / $50 | $0.0225 | About $22 |

The sum is simple:

```text
cost = (input tokens × input price + output tokens × output price) ÷ 1,000,000
```

That's a 100 times range for the same turn. So at scale, this choice matters a lot. These are list prices, for one turn, and don't include caching or batch discounts. An agent also makes several calls per question, so measure a real conversation.

## How ShopHelper does it

Here the model is a setting, so the same code can run different ones:

```python file=src/shophelper/agent/graph.py
if s.llm_provider == "openai_compatible":
```

| Where | Agent | Judge in evals |
| --- | --- | --- |
| Local | Qwen3 30B, through LM Studio | The same Qwen model |
| AWS | Claude Haiku 4.5 | Claude Sonnet 4.6 |

Why these?

- **Local Qwen** is free to run, private, and works with no cloud account. That suits a learning project.
- **A small agent model on AWS**, because most questions are simple lookups, and the hard rules live in code.
- **A stronger, different model as judge on AWS**, because a model marking its own work is biased. Locally there's no second model, so scores there are only a rough signal.

The AWS choices are from when that was built. Newer models exist now, and changing them is a setting plus a run of the evals.

## In the market

Checked on 2026-11-06.

| Option | Good | Watch out for |
| --- | --- | --- |
| Provider API, such as [Anthropic](https://platform.claude.com/docs/en/about-claude/models/overview) | Best models, nothing to run | Data leaves you, prices can change |
| Through your cloud, such as [Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html) | Fits your cloud's security and billing | New models can arrive later |
| Open model you host, such as [Qwen3](https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507) | Full control and privacy | You run the hardware and handle scaling |

Anthropic's own advice is to start with Opus 5.5 for most work if you're unsure. Haiku 5.5 is aimed at high-volume, speed-sensitive tasks such as classification and routing.

**Hosting your own isn't automatically cheaper.** You pay for GPUs whether they're busy or not. It tends to pay off at steady high volume, or when data can't leave.

**Plan to switch.** Models change every few months, and older ones are retired. Keep the model behind a setting, keep your tests, and a change becomes an afternoon's work.

## Try it

1. Sign in, open **How it works**, and click the **Tool call** example.
2. Add up the input and output tokens across the turn.
3. Work out what that turn would cost on two models from the table.
4. Multiply by a guess of daily questions. Does the choice matter at that volume?

## Interview questions

### How do you choose a model for a new feature?

**Strong answer:** I start from requirements: quality on my task, latency, cost at expected volume, and data rules. I build a small eval set from real examples. Then I start with a strong model to prove it's possible, and try cheaper ones until quality drops below what I need. I'd often use different models for different steps. Public benchmarks are only a first filter.

**Follow-up:** What if the cheap model passes 95% of cases?

### What would a support bot with 10,000 conversations a day cost each month?

**Strong answer:** I'd measure a real conversation first. Say 3 turns, each 2 model calls of about 1,750 tokens in and 100 out. That's about 10,500 in and 600 out per conversation. Monthly, that's about 3.2 billion input and 180 million output tokens. At $2 and $10 per million that's about $6,300 and $1,800, so roughly $8,000 a month. Then I'd look for savings: caching the system prompt, a smaller model, or shorter prompts.

**Follow-up:** Which of those would you try first?

### Why not self-host an open model and avoid API costs?

**Strong answer:** It can be right, but it isn't free. You pay for GPUs around the clock, handle scaling and failures, and open models may trail the best hosted ones. It makes sense with strict data rules or steady high volume. I run Qwen locally for development, which shows how much is involved even at small scale.

**Follow-up:** What would make you switch to self-hosting?

## Check yourself

### What should decide your choice of model?

- [ ] The top of a public leaderboard — it may not match your task.
- [x] How models do on your own task, within your limits — right: test with your evals.
- [ ] The newest release — newer isn't always better for your job.

### Why does ShopHelper's AWS setup use a different model as the judge?

- [x] A model marking its own work is biased — right: a stronger, separate judge is more trustworthy.
- [ ] It's cheaper — the stronger model costs more.
- [ ] AWS requires it — it was a design choice.

### How do you make switching models easy later?

- [ ] Choose a model that never changes — models are retired.
- [x] Keep it behind a setting, with tests — right: switching becomes a change plus a test run.
- [ ] Copy the prompt into every file — that makes changes harder.
