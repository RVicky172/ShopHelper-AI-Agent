---
title: Reasoning models
checked: 2026-11-06
---

## What you'll learn

- What a reasoning model does differently
- Why thinking before answering can help
- What it costs
- When to use it, and when not to

## The simple explanation

A model writes one token at a time, and each token gets about the same amount of work. So a hard question gets no more effort than an easy one, unless the model writes more.

That's the idea behind **reasoning models**. Before the final answer, the model writes out its working: trying an approach, checking it, and sometimes starting again. Each token of working is more thinking it gets to build on.

Think of a maths exam. Asked for an answer straight away, you might guess. Allowed scrap paper, you do far better, even though you're the same person.

It started as a prompting trick, asking a model to "think step by step". Now models are trained to do it. One well-known example is [DeepSeek-R1](https://arxiv.org/abs/2501.12948). Its paper reports that reasoning can be developed through reinforcement learning alone: reward correct final answers, and behaviours like checking its own work appear.

Some models can decide how much to think. Claude's **adaptive thinking** lets the model judge that for each request, guided by an **effort** setting.

## An example

Take this question: "A customer bought a $249 stand and a $12 cable, delivered 28 days ago. The stand arrived damaged, and they opened the cable and don't want it. What do they get back?"

A quick answer might say "$261". Working it through finds more:

1. The stand is defective, so there's no restocking fee, and the return label is free.
2. The cable is opened electronics and not defective, so there's a 10% fee: $1.20.
3. A non-defective return costs $5.99 for the label, deducted from the refund.
4. The order is within 30 days, so returns are allowed.
5. It's over $200, so a supervisor must review it.

Several rules interact, so working through them helps. Compare "How long do refunds take?". There's nothing to think through, so thinking just adds delay and cost.

## Not in ShopHelper

ShopHelper doesn't use a reasoning model. The local model is the *Instruct* version of Qwen3, and in this project's runs it answers directly, with no thinking text.

That suits the task. Most questions here are simple lookups, so speed matters more. And the hard parts are handled in code, not by reasoning:

```python file=src/shophelper/agent/graph.py
refund = _decide_refund(call["args"], _user_id(config))
```

Whether a refund is allowed is a rule, so code decides it. Asking a smarter model to reason about it wouldn't make it a guarantee.

That's a general point. If a step must be right every time, don't reach for more reasoning. Use code.

## In the market

Checked on 2026-11-06.

| Approach | Example | Control |
| --- | --- | --- |
| Model decides how much to think | [Claude's adaptive thinking](https://platform.claude.com/docs/en/about-claude/models/overview) | An effort setting |
| Fixed thinking budget | Older Claude models, in [extended thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) | A token budget. Deprecated, and rejected by Claude 4.7 and later |
| Open reasoning models | [DeepSeek-R1](https://arxiv.org/abs/2501.12948) | Varies |

Details change quickly, and they differ by provider.

**The cost is real.** Thinking tokens are output tokens, and output usually costs the most. With Claude they're billed, they count towards `max_tokens`, and they add to the wait. So measure on your task whether it earns its cost. Anthropic's docs also note that returns diminish as budgets grow.

**A good rule:** use reasoning for many-step problems, such as planning, coding and rules that interact. Skip it for lookups, classification and short answers.

## Interview questions

### What's a reasoning model, and when would you use one?

**Strong answer:** It writes out working before its final answer, which gives it more computation on hard problems. Newer models are trained to do this, and some choose how much to think. I'd use one where several steps or rules interact, like planning or coding. For simple lookups it only adds cost and delay. In my support agent most questions are lookups, so I don't use one.

**Follow-up:** How would you decide, with evidence?

### Could a reasoning model replace your refund rules?

**Strong answer:** No. Better reasoning makes mistakes less likely, but a rule that must always hold needs a guarantee, and that comes from code. Refund eligibility is decided in code in my project, and a human approves every refund. The model is good at understanding the request. It shouldn't be what decides whether money moves.

**Follow-up:** Where do you draw that line in general?

## Check yourself

### Why can writing out working improve an answer?

- [ ] The model looks facts up as it writes — it isn't searching anything.
- [x] It gets more computation to build on — right: each token of working helps the next.
- [ ] It makes the model more confident — confidence isn't the same as correctness.

### When is a reasoning model a poor choice?

- [x] A simple lookup where speed matters — right: thinking adds cost and delay, with nothing to think through.
- [ ] Several rules that interact — that's where it helps most.
- [ ] A hard planning problem — that's a good fit.

### A step must be correct every single time. What should you use?

- [ ] The strongest reasoning model — better odds aren't a guarantee.
- [ ] A higher effort setting — same problem.
- [x] Code — right: a rule in code runs the same way every time.
