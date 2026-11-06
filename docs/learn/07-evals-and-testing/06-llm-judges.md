---
title: LLM judges
checked: 2026-11-06
---

## What you'll learn

- When a model should grade another model
- How to write a rubric
- The known biases of judges
- How to check a judge, with a real test

## The simple explanation

Is an answer actually supported by the passages? A string match can't tell you. A person can, but not 1,000 times a day. So you ask a model to grade it, using a written rubric. That's an **LLM judge**.

Think of exam markers. A marking scheme lets many people mark consistently. But before a school trusts a new marker, a senior teacher re-marks a sample, to see if they agree. A judge is a new marker. You check it before you trust it.

| Grader | Good at | Weak at |
| --- | --- | --- |
| **Code** | Facts, tools, status. Fast and free | Meaning |
| **LLM judge** | Meaning, at scale | It varies, it costs, and it has biases |
| **Human** | The final word | Slow and expensive |

So use code when you can, a judge when you must, and humans to check the judge.

## An example

We tested this project's judge. We wrote 14 answers by hand, and labelled each: is it faithful or not? Then we ran the judge, which is the local Qwen model, with a pass mark of 4 out of 5.

| Kind of answer | Label | Scores |
| --- | --- | --- |
| Plain and right, 4 cases | Faithful | 5, 5, 5, 5 |
| Honest "I couldn't find that" | Faithful | 5 |
| Long and right | Faithful | 5 |
| Wrong number ("3-5 days") | Not faithful | 3 |
| Contradicts the passage | Not faithful | 1 |
| Invented gift wrapping | Not faithful | 2 |
| Rule quietly changed | Not faithful | 3 |
| Short and wrong | Not faithful | 2 |
| Long, friendly and wrong | Not faithful | 2 |
| Added "covers accidental damage" | Not faithful | 3 |
| **Added "orders before noon ship the same day"** | Not faithful | **4: passed** |

It agreed with us on **13 of 14**. That's better than expected, and the miss is interesting. The answer repeated two true facts, then added an invented promise. The judge said it was accurate "though" it added detail, and let it through. **An invented promise tacked onto true facts is the kind of thing a customer acts on.**

It's a small set of cases we wrote ourselves, so it's a first check, not a proof. But now we know one thing to watch for, which we didn't before.

## How ShopHelper does it

The rubric is in [judge.py](../../../evals/judge.py). Here's the key part:

```text
An answer is faithful if every factual claim about store policy in it is supported by the
retrieved passages. Saying that the information is not available, when the passages don't
contain it, is faithful. Friendly filler and offers to help further are fine.
```

Notice what it does:

- It asks one question, not "is this good?".
- It defines the term.
- It says what isn't a failure, so saying "I don't know" isn't punished.
- It asks for JSON with a reason, so a failure can be read:

```text
{"score": <1-5, 5 = fully supported>, "faithful": <true|false>, "reason": "<one sentence>"}
```

The temperature is 0, to keep scores stable:

```python file=evals/judge.py
inferenceConfig={"maxTokens": 300, "temperature": 0},
```

**Which model judges?** On AWS, a stronger, different model grades the agent: Sonnet judges Haiku. Locally, Qwen judges itself, because it's what's available:

```python file=evals/judge.py
"""Local runs: the agent's own model is the judge, so the bias noted above applies."""
```

**A warning sign.** In the last full eval run, all 16 judged cases scored 5, for a mean of 5.0. That might mean every answer was perfect, or that a model marking its own work goes easy. The calibration above suggests the judge can give low scores, on answers it didn't write. It doesn't tell us how it scores its own, so treat local scores as a rough signal only.

**An improvement to make.** The pass mark is 4, and the one miss scored 4. The rubric's own `faithful` field could be used instead, or a stricter rule: list each claim, and mark it supported or not. We haven't tested either.

## In the market

Checked on 2026-11-06.

[Judging LLM-as-a-Judge](https://arxiv.org/abs/2306.05685), by Zheng and colleagues, is the paper to know. It found strong judges agreed with human preferences over 80% of the time, about the same as humans agree with each other. It also named the biases:

| Bias | What happens | Defence |
| --- | --- | --- |
| **Position** | Prefers the first or second of two answers | Run both orders |
| **Verbosity** | Prefers longer answers | State in the rubric that length earns nothing |
| **Self-enhancement** | Prefers its own style of output | Use a different model |

Our test had a long wrong answer and a short wrong one, and both scored 2, so verbosity didn't show up there. That's one pair of cases, and not a real test of it.

**How to run one well:**

1. Label 20 to 50 examples by hand, as [Arize suggests](https://arize.com/docs/ax/cookbooks/evaluate/align-llm-evals-with-human-judgment).
2. Run the judge, and read where it disagrees.
3. Fix the rubric, and run it again.
4. Prefer yes or no to a scale of 1 to 5.
5. Check again when the judge model changes, because scores move.
6. Re-check a sample by hand from time to time.

Don't use a judge for what code can check. A model isn't needed to see if a string contains "$19.99".

## Try it

1. Read the rubric in `evals/judge.py`, and say which words you'd change.
2. Open `evals/report.json`, if you've run the evals. Find a `judge` entry, and read its `reason`.
3. Write three answers to "How long do refunds take?": one right, one wrong, one right with an invented extra. Which would you trust a model to catch?

## Interview questions

### How do you know you can trust an LLM judge?

**Strong answer:** I check it against human labels before relying on it. In my project I hand-labelled 14 answers, and the judge agreed on 13. The miss was useful: true facts with an invented promise added, which scored a passing 4. So I know what to watch. I'd grow the set, read disagreements, and re-check when the judge model changes. The score means little until it's been calibrated.

**Follow-up:** What agreement level is good enough?

### What biases do LLM judges have?

**Strong answer:** Position bias when comparing two answers, verbosity bias towards longer ones, and self-enhancement towards their own style, from the MT-Bench paper. Defences are to swap the order, state that length earns nothing, and use a different, stronger model. Locally my judge is the same model as the agent, and it gave every case a 5, so I treat that as a rough signal. On AWS the plan is a stronger model judging.

**Follow-up:** Does a judge need to be stronger than the agent?

### When would you not use an LLM judge?

**Strong answer:** Whenever code can decide. Whether a tool ran, whether a fact appears, and what's in the database are all deterministic and free. A judge adds cost and variation. I use one for meaning, like whether each claim is supported. Sixteen of my 37 cases use it, and every case also has code checks. For high-stakes decisions, a person reviews a sample.

**Follow-up:** How do you keep judge costs down?

## Check yourself

### What should you do before trusting a judge?

- [ ] Use the biggest model — that isn't calibration.
- [x] Compare it with hand labels — right: read where it disagrees.
- [ ] Run it at a high temperature — that adds variation.

### What did our judge miss?

- [ ] A wrong number — it scored that 3.
- [x] An invented promise added to true facts — right: it scored 4, and passed.
- [ ] An honest "I don't know" — that was right to pass.

### A check needs to see if a price appears. What do you use?

- [x] A string check — right: it's free, and it never changes its mind.
- [ ] An LLM judge — that's more cost, for less certainty.
- [ ] A human — that's far too slow.
