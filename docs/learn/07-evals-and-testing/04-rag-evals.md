---
title: RAG evals
checked: 2026-11-06
---

## What you'll learn

- Why retrieval and generation are measured separately
- The main metrics, in plain words
- This project's real numbers
- Why "the tool ran" isn't a passing test

## The simple explanation

A RAG answer has two chances to go wrong: finding the passage, and using it. If you only score the final answer, you can't tell which failed.

Think of a student in an open-book exam. A wrong answer could mean they opened the wrong chapter, or read the right one and misunderstood. The fix is different, so you need to know which.

So measure each half:

| Half | Question | Metric | Needs |
| --- | --- | --- | --- |
| Retrieval | Is the right passage in the top k? | **Hit rate** or recall | Known answers |
| Retrieval | How high does it rank? | **MRR** | Known answers |
| Retrieval | How much of what came back was useful? | **Context precision** | A judge or labels |
| Generation | Is each claim supported by the passages? | **Faithfulness** | A judge |
| Generation | Does it answer the question? | **Answer relevancy** | A judge |
| Whole | Is it actually right? | **Correctness** | A reference answer |

**MRR, mean reciprocal rank**, is simple: first place scores 1, second scores 1/2, third scores 1/3, then take the average. Higher means the right chunk comes earlier.

Note what faithfulness doesn't check. A faithful answer agrees with the passages, even if the passages are out of date. So faithful doesn't always mean correct.

## An example

Here are retrieval numbers from this project: 20 questions, each with a fact that must appear in a chunk.

| Measure | Result |
| --- | --- |
| Hit rate at 1 | 17 of 20, or 0.85 |
| Hit rate at 4 | 20 of 20, or 1.00 |
| MRR | 0.91 |

MRR comes from those 17 first places, plus the three misses at ranks 3, 2 and 3. That's (17 + 1/3 + 1/2 + 1/3) ÷ 20.

The agent reads the top 4, so hit rate at 4 is the one that matters most here. It says retrieval is fine. It also comes with a warning: there are only 24 chunks, so top 4 is a sixth of everything. [That test can't see much.](../05-rag/02-embeddings-in-depth.md)

The retrieval test costs almost nothing: no chat model, just embeddings and SQL. So you can try a change to chunking and see the result in seconds, which is why it's worth keeping apart from the slower evals.

## How ShopHelper does it

Generation is checked in the golden set. Sixteen cases ask for the judge, and every one must reach a score of 4 or more:

```python file=evals/test_golden.py
verdict = judge_faithfulness(case["message"], passages, resp.answer)
```

The judge sees the passages that were really returned for that turn, read from the agent's saved state, not a stored copy.

A case that has no answer should be scored as a success when the agent says so. The judge's rubric states this:

```text
Saying that the information is not available, when the passages don't contain it, is faithful.
```

**A tool call isn't a right answer.** The shop's chat offers starter questions, and each must be one the agent can really answer. Asking them for real took four rounds:

| Round | Result | What it found |
| --- | --- | --- |
| 1 | 32 of 37 | A phone case got the 90-day warranty, not the 1-year one. Two starters made the agent ask for an order number |
| 2 | 36 of 37 | The policies now define electronics, which fixed the warranty. One starter still asked for an order number |
| 3 | 52 of 57 | "What is your delivery policy?" called the search tool, and gave a fluent answer with no delivery times in it |
| 4 | 57 of 57 | "What are your shipping options and delivery times?" retrieves the right passage |

Round 3 is the lesson. The tool ran, and the answer read well, but it didn't say what the customer asked. A faithfulness judge might well have passed it, because nothing in it was false. The check caught it only because it looked for the actual terms. That's answer relevancy, and it's a separate thing from faithfulness.

The phone case wasn't a model bug either. The policy really was unclear, because a phone case doesn't sound like electronics. Fixing the document fixed it for every model.

**Not built here.** The retrieval numbers above came from a separate experiment. It isn't part of the eval suite, so a chunking change wouldn't be caught by a test. Adding it would be a good next step, and it's small.

## In the market

Checked on 2026-11-06.

[Ragas](https://docs.ragas.io/en/latest/concepts/metrics/) is the best-known library for these metrics. Its common starting set is faithfulness, answer relevancy, context precision and context recall. Most of those use a model as a grader, so they cost money, vary a little, and need [checking against your own labels](06-llm-judges.md).

Anthropic's [contextual retrieval post](https://www.anthropic.com/news/contextual-retrieval) reports a retrieval failure rate for the top 20 chunks. That's hit rate at 20, turned around, and it shows how simple the core metric is.

Which should you start with?

1. **A hit rate**, on questions with known answers. It's cheap and needs no judge.
2. **Faithfulness**, since inventing policy does the most harm.
3. **Questions with no answer**, to check the agent admits it.
4. **Correctness**, on a smaller hand-labelled set.

## Try it

1. Sign in, open **How it works**, then **RAG explorer**.
2. Write down 5 questions, and the policy that should answer each.
3. Search each one, and record the rank of the right chunk. Work out hit rate at 1, hit rate at 4, and MRR.
4. Search "What is your delivery policy?", and then "What are your shipping options and delivery times?". Compare which chunks come back.

## Interview questions

### How do you evaluate a RAG system?

**Strong answer:** I measure the two halves separately. Retrieval uses questions with known answers: hit rate at k, and MRR. It's cheap, so I can test chunking changes quickly. Generation uses faithfulness, meaning each claim is supported by the passages, plus answer relevancy. I include questions with no answer. In my project hit rate at 4 was 20 of 20, and MRR was 0.91, though 24 chunks is too few for that to be a hard test.

**Follow-up:** How big should the question set be?

### What's the difference between faithfulness and correctness?

**Strong answer:** Faithfulness means the answer agrees with the retrieved passages. Correctness means it's true. If a stale policy is retrieved, an answer can be faithful and wrong. And relevancy is different again: in my project one answer was fluent and contained nothing false, but it left out the delivery times the customer asked for. So I check all of them, and catch that last one with a required-terms check.

**Follow-up:** Which matters most for a support bot?

### Faithfulness dropped after a change. What do you look at?

**Strong answer:** I read the failing cases first. I'd check whether retrieval changed, since worse passages can make the model fill the gaps. Then the prompt and model. I'd check the judge too, because its scores can move on their own. If retrieval metrics held steady and faithfulness fell, I'd focus on generation.

**Follow-up:** What if only some topics dropped?

## Check yourself

### Why measure retrieval separately?

- [x] A wrong answer could come from either half — right: and the fix differs.
- [ ] Retrieval is the only part that matters — both matter.
- [ ] It's required by pgvector — it's not about the tool.

### The right chunk is at rank 2. What does it add to MRR?

- [ ] 2 — it's the reciprocal.
- [x] 1/2 — right: first scores 1, second 1/2.
- [ ] 0 — it was still found.

### An answer matches an out-of-date passage. What is it?

- [ ] Faithful and correct — it's out of date.
- [ ] Unfaithful — it agrees with the passage.
- [x] Faithful, but wrong — right: faithfulness only compares with the passages.
