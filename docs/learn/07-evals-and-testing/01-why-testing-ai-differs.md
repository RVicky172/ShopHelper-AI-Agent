---
title: Why testing AI is different
checked: 2026-11-06
---

## What you'll learn

- What unit tests can't tell you about an AI system
- What an eval is
- Why one passing run proves little
- Why you should read failures, not only count them

## The simple explanation

A normal function gives the same answer every time, so a test can state the exact result. A language model doesn't work like that. Ask twice, and the wording can differ. Change one line of a prompt, and something unrelated can break, with no error anywhere.

Think of a calculator and a new employee. You test a calculator once: 2 + 2 is 4. You can't test an employee that way. You give them realistic situations, see how they handle them, and check on them again after anything changes. You're judging behaviour, and you're looking at a rate, not a single result.

So AI systems need two kinds of test:

| | Unit tests | Evals |
| --- | --- | --- |
| Model | Fake and scripted | Real |
| Checks | Your logic | The system's behaviour |
| Speed | Seconds | Minutes |
| Result | The same every time | Can vary between runs |
| Cost | Nothing | Model calls |

Unit tests use a fake model that returns a scripted reply, so they're fast and repeatable. But they can't tell you whether the real model calls the right tool.

An **eval** runs realistic inputs through the whole system, with the real model, and checks the outcome. Think of evals as tests for behaviour.

## An example

The first time this project's evals met a real model, 18 of 20 passed. The most useful part was working through the failures, because each had a different cause:

| Failure | Real cause | Fix |
| --- | --- | --- |
| Asked for an order number it had been given | **Bug in the test.** An unquoted `#1005` in YAML starts a comment, so the model received "Can you check order" | Quote the string |
| Answer said "don't", and the check failed | **Bug in the check.** The model wrote a curly apostrophe | Normalise before comparing |
| Wrote "I'll process the refund", and stopped | **Real model weakness** | Prompt rule: call the tool now |
| Asked the customer to confirm first | **Real model weakness** | Prompt rule: don't ask, a human reviews it |
| 8 of 20 failed with `Event loop is closed` | **Test setup.** The client caches connections across pytest's loops | Run all cases in one loop |

Two lessons. **Read the failures, don't only count them**: two of the "agent failures" were broken tests. And the YAML bug had been there since the suite was written, because the evals had never run against a real model. A test that has never run hasn't tested anything.

## How ShopHelper does it

The fake model lets unit tests script a whole conversation, including tool calls, so the graph's logic is tested in milliseconds. Then the same system runs for real.

Each eval case calls the real service, as a real customer:

```python file=evals/test_golden.py
resp = await svc.chat(session_id, case["message"], _principal(case))
```

Wording changes between runs, so the check has to allow for that. This line fixes the apostrophe failure above, and it's a small example of what eval code looks like:

```python file=evals/test_golden.py
answer = resp.answer.lower().replace("’", "'")  # models also write curly apostrophes
```

**A green run can mislead.** The suite once passed 27 of 27 several times, then one refund case failed. Re-running passed. It would have been easy to call that noise. So the rate was measured:

| How it was run | Submitted |
| --- | --- |
| The same prompt, 20 times in a row | 20 of 20 |
| The same prompt, with other questions in between | **0 of 20** |

LM Studio caches the start of recent prompts, so repeating a prompt repeats its outcome, and the runs weren't independent. Which result you got depended on what ran just before. A customer asking that exact sentence would usually have been told a refund was coming, with nothing submitted.

So: an intermittent failure is a finding, not bad luck. Measure a rate, not one run. And make sure your samples really are independent.

**Results don't carry over.** A pass here says Qwen with local rules works. It says nothing about Claude with Bedrock Guardrails. Prompts tuned for one model can behave differently on another, so changing the model means running the evals again.

## In the market

Checked on 2026-11-06.

[Anthropic's guide to agent evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) gives useful shared words:

| Word | Meaning | Here |
| --- | --- | --- |
| **Task** | One test, with inputs and success criteria | One golden case |
| **Trial** | One attempt at a task | One run of that case |
| **Grader** | Logic that scores it | The checks in `test_golden.py` |
| **Transcript** | The full record of a trial | The trace |
| **Outcome** | The final state of the world | The order in the database |

It separates two kinds of eval. **Capability evals** ask what the agent can do, and should start with a low pass rate. **Regression evals** ask whether it still does what it did, and should sit near 100%. ShopHelper's golden set is the second kind, and that's a limit: at 37 of 37 it can't show anything getting better.

## Try it

1. Run `uv run pytest tests/agent -q`, and note how long it takes. No model is involved.
2. Open `evals/golden_cases.yaml`, and find `order_cancelled`. Read the comment beside its message: that's the first failure above.
3. Open `evals/report.json`, if you've run the evals before. Compare `answer` for two cases: wording varies, but the facts are there.

## Interview questions

### How is testing an AI system different from normal software?

**Strong answer:** Normal tests assert exact results, but model output varies, and a prompt change can break something far away with no error. So I keep unit tests with a fake model for my own logic, and add evals, which run real inputs through the real model and check outcomes like tool calls and database state. I look at rates, not single runs. In my project a refund worked 20 of 20 times repeated, and 0 of 20 when mixed with other questions, because of prompt caching.

**Follow-up:** How do you make sure samples are independent?

### Your eval suite passes, but users report problems. Why might that be?

**Strong answer:** The suite only covers what's in it. Real questions may be worded differently, or the cases may be too easy, or the checks too loose. It may also have passed by luck, if results vary. I'd pull real failures into the set, read the transcripts, and check that each test can fail. Mine once had a tool call and a fluent answer with no real information in it, so "the tool ran" wasn't enough.

**Follow-up:** How do you find those failures in production?

### An eval fails once, then passes on a re-run. What do you do?

**Strong answer:** I treat it as a finding. I'd measure the rate by repeating it, with unrelated prompts in between so the runs are independent, and read what the failing run did. If a real customer would hit it, it's a bug at some rate. Mine turned out to be a refund the model promised but didn't submit, and it was hidden because repeated prompts hit a cache.

**Follow-up:** What failure rate is acceptable?

## Check yourself

### What can a unit test with a fake model not tell you?

- [ ] Whether your code handles a tool result — that's what it's for.
- [x] Whether the real model picks the right tool — right: that needs an eval.
- [ ] Whether your function has a bug — unit tests catch those.

### Two of the first "agent failures" were what?

- [x] Bugs in the tests — right: which is why you read failures.
- [ ] Model weaknesses — those were the other two.
- [ ] Network errors — they weren't.

### Why was 20 of 20 misleading?

- [ ] The test was too short — length wasn't the issue.
- [ ] The model was switched — it wasn't.
- [x] Repeated prompts weren't independent samples — right: a cache repeated the outcome.
