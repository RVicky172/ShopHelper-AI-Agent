---
title: Embeddings in depth
checked: 2026-11-06
---

## What you'll learn

- How to choose a distance measure
- What query and document prefixes do, as measured
- Why a small test set can't tell you much
- What shortening vectors costs

## The simple explanation

You met [embeddings](../01-how-llms-work/02-embeddings.md) in stage 1: lists of numbers where similar meanings sit close together. Using them well means a few practical choices.

**How do you measure "close"?** There are three common ways:

| Measure | Compares | Used when |
| --- | --- | --- |
| **Cosine** | The direction two vectors point | Most text search |
| **Dot product** | Direction and length | Vectors already normalised, so it's faster |
| **Euclidean** | Straight-line distance | Less common for text |

Think of two people walking. Cosine asks "are they heading the same way?", however far each has gone. That suits text, where length shouldn't change meaning. Use the measure the model card recommends.

**Questions and answers aren't alike.** "How long do refunds take?" and "Refunds take 5-7 days" mean related things, but one's a question and one's a statement. Some models ask you to label which is which, with a prefix.

**Size is a trade-off.** More dimensions can hold more detail, but take more storage and slower search. Some models are trained so a vector can be shortened with little loss, which is called **Matryoshka** learning, after the nesting dolls.

## An example

We built a test: 20 real questions, each with a fact that must appear in the retrieved chunks. We ran it on this project's 24 chunks, with and without the prefixes:

| Setup | Right chunk first | Right chunk in top 4 |
| --- | --- | --- |
| With prefixes | 17 of 20 | 20 of 20 |
| Without prefixes | 17 of 20 | 20 of 20 |

No difference. [The model card](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5) says prefixes are required, so does that mean they don't matter?

No. It means **this test can't see the difference**. There are only 24 chunks, and top 4 is a sixth of everything. With so little to choose from, nearly any setup looks good. Prefixes are likely to matter more on a big collection, where many chunks compete.

This is one of the most useful lessons in RAG: a result on a small test only tells you about a small test. Before trusting it, ask "could this test have shown a difference?". We kept the prefixes because the model's authors require them, not because we proved anything here.

## How ShopHelper does it

The two prefixes are constants, applied at each end:

```python file=src/shophelper/rag/pipeline.py
DOCUMENT_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "
```

Both sides need to match how the model was trained. The chunks get the document prefix at ingest, and the question gets the query prefix at search:

```python file=src/shophelper/rag/pipeline.py
vectors = embed(chunks, DOCUMENT_PREFIX)
vector = Vector(embed([query], QUERY_PREFIX)[0])
```

The index uses cosine, matching the `<=>` in the query. If those two disagree, the index won't be used:

```sql file=src/shophelper/core/schema.sql
ON policy_chunks USING hnsw (embedding vector_cosine_ops);
```

Locally this uses nomic at 768 dimensions, and AWS uses Titan at 1,024. Those two sets of vectors can't be mixed, which is fine, because each environment embeds its own copy.

## In the market

Checked on 2026-11-06.

| Option | Shortening | Source |
| --- | --- | --- |
| nomic-embed-text-v1.5 | 768 down to 512, 256, 128 or 64, with a small drop in performance | [Model card](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5) |
| Titan Text Embeddings V2 | 1,024, 512 or 256 | [AWS docs](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html) |
| OpenAI text-embedding-3 | A `dimensions` setting | [OpenAI docs](https://developers.openai.com/api/docs/guides/embeddings) |

Public leaderboards can help you shortlist models. But they test other people's data, so test the top few on your own questions.

**Batching** matters at ingest. Embedding one chunk per request is slow, and most APIs accept a list. ShopHelper sends each document's chunks together.

## Try it

1. Sign in, open **How it works**, then **RAG explorer**.
2. Search "Can I send this back?", and note the top score.
3. Search "return policy", and compare. Which is more similar to the document, and why might that be?

## Interview questions

### Why use cosine similarity for text?

**Strong answer:** It compares direction rather than length, so a long passage and a short one about the same thing can still match. Most text embedding models are built for it, but I'd follow the model card. If vectors are normalised, dot product gives the same ordering, and it's cheaper. What matters is that the query, the index and the model all agree.

**Follow-up:** What happens if the index uses a different distance from the query?

### A test shows a change makes no difference to retrieval. What do you conclude?

**Strong answer:** I check whether the test could have shown a difference first. I tested query prefixes on my 24 chunks and saw no change, but top 4 out of 24 is an easy target. So the honest conclusion is that this test can't tell, not that prefixes don't matter. I'd need more documents, harder questions, or a stricter measure like whether the right chunk comes first.

**Follow-up:** How big should a retrieval test set be?

### How would you cut the storage cost of a billion embeddings?

**Strong answer:** Use fewer dimensions, if the model supports shortening, and quantise the numbers to fewer bits. Then measure recall on real questions, because each saves space at some cost in quality. Large stores can also use cheaper tiers for rarely searched data. I'd try these in that order, and stop when quality drops below what the product needs.

**Follow-up:** What's the risk of quantising?

## Check yourself

### Why might prefixes show no benefit on 24 chunks?

- [x] With so few chunks, nearly any setup finds the right one — right: the test can't see the difference.
- [ ] Prefixes never matter — the model's authors require them.
- [ ] The test proves they should be removed — it proves nothing either way.

### What does Matryoshka learning let you do?

- [ ] Train a model faster — it's about the vectors.
- [x] Shorten vectors with little loss — right: like nesting dolls, smaller versions sit inside.
- [ ] Search several languages — that's separate.

### Your query uses cosine, and your index uses Euclidean. What happens?

- [ ] It runs twice as fast — they have to match.
- [x] The index won't be used for that query — right: they must agree.
- [ ] Results get more accurate — nothing improves.
