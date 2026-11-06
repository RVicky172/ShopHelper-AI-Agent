# 9. Evals

## Unit tests aren't enough

Unit tests check your code. They use a fake, scripted model, so they're fast and repeatable. But
they can't tell you whether the real model calls the right tool, or whether a prompt edit broke
refunds.

**Evals** test the behaviour of the whole system, with the real model.

| | Unit tests | Evals |
| --- | --- | --- |
| Model | Fake and scripted | Real |
| Checks | Your logic | The system's behaviour |
| Speed | 2 seconds | About 1 minute |
| Result | Same every time | Can vary between runs |
| Run | `uv run pytest` | `scripts/evals_local.sh` |

## The golden set

[golden_cases.yaml](../../evals/golden_cases.yaml) lists 33 conversations with expected outcomes:

```yaml
- id: refund_eligible_pauses
  message: I'd like a refund for order 1001, the mouse stopped working.
  expect: {tools: [request_refund], status: pending_approval, orders_after: {"1001": delivered}}
```

A language model's wording changes, so exact text matching won't work. Check the things that matter:

| Check | Example | Why |
| --- | --- | --- |
| Tool use | `tools: [request_refund]` | Did it take the right action? |
| Status | `status: pending_approval` | Did the flow go the right way? |
| Key phrases | `contains_any: [shipped]` | Is the fact there, in any wording? |
| Forbidden text | `not_contains: [...]` | Did it leak or promise something? |
| Side effects | `orders_after: {"1001": delivered}` | Is the database right? |
| Judge | `judge: true` | Is the answer faithful to the documents? |

Twelve of the 31 are attacks. Five try to break the guardrails, and seven try to reach another customer's data.
Each case runs as a named customer, using the `as:` field.

## LLM as a judge

Is an answer actually supported by the retrieved passages? String matching can't tell you. So we
ask another model to grade it, using the rubric in [judge.py](../../evals/judge.py), scoring 1-5
for **faithfulness**.

On AWS, Sonnet judges Haiku: a stronger, different model. Locally, Qwen judges itself. Models tend
to go easy on their own output, so treat local judge scores as a rough signal only.

## What evals found in this project

The first run against a real model scored 18 of 20. Working through the failures was the most useful
part, because each had a different cause:

| Failure | Real cause | Fix |
| --- | --- | --- |
| Asked for an order number it had been given | **Bug in the test.** Unquoted `#1005` in YAML starts a comment, so the model received "Can you check order" | Quote the string |
| Answer said "don't", check failed | **Bug in the check.** The model wrote a curly apostrophe (’) | Normalise before comparing |
| Wrote "I'll process the refund" and stopped | **Real model weakness** | Prompt rule: call the tool now |
| Asked the customer to confirm first | **Real model weakness** | Prompt rule: don't ask, a human reviews it |
| 8 of 20 failed with `Event loop is closed` | **Test setup.** The client caches connections across pytest's per-test loops | Run all cases in one loop |

After those fixes, all 20 cases that existed then passed, three runs in a row. Feature 020 added 7 cross-user
attacks, and the shop added 6 cases about which terms apply to which products. All 33 now pass.

### Proving an attack test can fail

An attack that "passes" might only pass because something else stopped it, or because the test is weak. So the
cross-user cases were checked two ways:

1. **Did they reach the code under test?** All 7 called the order tool, so no guardrail was doing the work.
2. **Do they fail without the protection?** With the owner check removed, all 7 failed.

A security test you've never seen fail hasn't proved anything. [Chapter 11](11-accounts-and-isolation.md) has the
results.

Two lessons. **Read the failures, don't only count them**: two of the "agent failures" were broken
tests. And the unquoted YAML bug had been there since the suite was written, because the evals had
never run against a real model. A test that has never run hasn't tested anything.

## A green run can mislead

The suite passed 27 of 27 several times, then one refund case failed. Re-running it passed, and it would have been easy
to call that noise. Instead, the rate was measured:

| How it was run | Submitted |
| --- | --- |
| The same prompt, 20 times in a row | 20 of 20 |
| The same prompt, with other questions in between | **0 of 20** |

LM Studio caches the start of recent prompts, so repeating a prompt repeats its outcome, and runs aren't independent. Which
result you got depended on what ran just before. A customer asking that exact sentence would usually have been told a
refund was coming, with nothing submitted.

Three lessons. An intermittent failure is a finding, not bad luck. Measure a rate, not one run. And when you measure,
make sure the samples are really independent.

### A tool call isn't a right answer

The shop's chat offers starter questions, and each must be one the agent can really answer. Asking them for real took four rounds:

| Round | Result | What it found |
| --- | --- | --- |
| 1 | 32 of 37 | A phone case got the 90-day lifestyle warranty, not the 1-year one. Two starters made the agent ask for an order number |
| 2 | 36 of 37 | The policies now define electronics, which fixed the warranty. One starter still asked for an order number |
| 3 | 52 of 57 | "What is your delivery policy?" called the search tool and gave a fluent answer with no delivery times in it |
| 4 | 57 of 57 | "What are your shipping options and delivery times?" retrieves the right passage |

Round 3 is the lesson. The tool ran, and the answer read well, but it didn't say what the customer asked. The check caught it only
because it looked for the actual terms. And the phone case wasn't a model bug to prompt away: the policy really was unclear, because
a phone case doesn't sound like electronics. Fixing the document fixed it for every model.

## Local results and AWS results differ

A pass here says Qwen with local rules works. It says nothing about Claude with Bedrock Guardrails.
Prompts tuned for one model may behave differently on another, so re-run the evals when you change
models. The attack results are also easier locally, because regex happens to match the exact
attack phrases in the suite.

## Try it

1. Run `scripts/evals_local.sh`, then read `evals/report.json`.
2. Remove the "Never say you will do something" line from the prompt in graph.py, run
   `docker compose restart api`, and run the evals a few times. Watch how often refund cases fail.
   Put the line back. That's what using evals to judge a prompt change looks like.
3. Add a case of your own. For example, a partial refund: "Refund $20 of order 1001", with `as: Asha`.

Next: [Local vs AWS](10-local-vs-aws.md)
