---
title: Sampling and temperature
checked: 2026-11-06
---

## What you'll learn

- How a model picks its next word
- What temperature does, and what it doesn't
- Why the same question can get different answers
- What setting to use, and why

## The simple explanation

After reading everything, the model gives every token it knows a probability. It doesn't produce one answer. It produces odds.

Choosing from those odds is called **sampling**. Think of a weighted raffle: likely tokens get many tickets, unlikely ones get few.

**Temperature** changes how the tickets are shared out:

| Temperature | Effect | Feels like |
| --- | --- | --- |
| 0 | Always take the most likely token | Careful, repeatable |
| Around 0.7 | Mostly likely tokens, some variety | Natural |
| High | Unlikely tokens get a real chance | Creative, then chaotic |

Two other common settings cut off the long tail of unlikely tokens before the draw. **Top-k** keeps the k most likely. **Top-p** keeps the most likely ones until their odds add up to p.

One small choice changes everything after it, because each token becomes part of the text the next is predicted from. That's why two answers can start alike and end up very different.

Temperature 0 isn't a promise of identical output. It removes the random draw, but tiny differences in how a server batches and calculates can still flip a close call. So tests should allow for variation.

## An example

We asked this project's local model for "one short, friendly sentence telling a customer their refund was approved", 4 times at each temperature:

| Temperature | Different answers out of 4 |
| --- | --- |
| 0 | 1 |
| 0.7 | 2 |
| 1.5 | 2 |

The only difference was a dash: "Great news — your" against "Great news—your". Every answer was otherwise the same.

That's not what tutorials usually show, and it's worth understanding. Temperature only reshapes the odds. For a simple, well-defined request, this model was very sure of its answer, so even at 1.5 the same words won. Instruction tuning tends to make models confident like this. A wide-open prompt, such as a story, leaves more room for variety.

So treat temperature as a small dial, not a creativity switch. Changing the prompt usually does far more.

## How ShopHelper does it

The agent runs at temperature 0, on AWS and locally:

```python file=src/shophelper/agent/graph.py
model=s.agent_model_id, region_name=s.aws_region, temperature=0, max_tokens=s.max_tokens
```

Support answers need to be accurate and repeatable, so there's no reason to add randomness. Tests also get more stable.

But stable isn't the same as safe. The evals still saw a failure that appeared once and not again on 10 more tries, at temperature 0, when the model invented an order number. That's why testing here repeats questions with others in between. See [Evals](../07-evals-and-testing/01-why-testing-ai-differs.md).

## In the market

Checked on 2026-11-06.

Settings differ by provider, and some newer reasoning models limit or ignore sampling settings. Check the docs for the model you use. For Claude, see the [models overview](https://platform.claude.com/docs/en/about-claude/models/overview).

A rough guide to starting points:

| Task | Temperature |
| --- | --- |
| Support, extraction, classification, tool use | 0 or low |
| General chat | Provider's default |
| Brainstorming, creative writing | Higher |

Treat these as a place to start, and measure on your own task.

## Interview questions

### What does temperature do?

**Strong answer:** The model outputs a probability for every possible next token, and temperature reshapes that before one is picked. Low makes the top choice dominate, high flattens the odds so unlikely tokens get a chance. For support and tool use I use 0, because I want accuracy and repeatability. It isn't a creativity switch, though: when I measured it, a simple prompt barely changed even at 1.5, because the model was already very confident.

**Follow-up:** What's the difference between top-p and top-k?

### You set temperature to 0, but outputs still differ between runs. Why?

**Strong answer:** Temperature 0 removes the random draw, but it doesn't guarantee identical results. Differences in how a server batches requests and tiny floating-point effects can flip a close decision, and one changed token changes everything after it. So I design tests that check outcomes, not exact text, and I don't rely on identical output.

**Follow-up:** How do you test something that isn't deterministic?

## Check yourself

### What does temperature 0 do?

- [x] Always picks the most likely token — right: there's no random draw.
- [ ] Guarantees identical answers every time — server effects can still change the result.
- [ ] Turns off the model's knowledge — it only affects choosing between tokens.

### Why does ShopHelper use temperature 0?

- [ ] It's cheaper — temperature doesn't change the price.
- [x] Support answers should be accurate and repeatable — right: nothing is gained from randomness here.
- [ ] Higher values aren't allowed — they are, but they'd add risk here.

### When we raised the temperature for a simple request, what happened?

- [ ] The answers became wildly different — only a dash changed.
- [x] Almost nothing changed — right: the model was already very sure, so the same words won.
- [ ] The model refused to answer — it answered every time.
