---
title: Contextual retrieval
checked: 2026-11-06
---

## What you'll learn

- Why a chunk can lose its meaning
- How contextual retrieval fixes that
- What it costs, and what gain was reported
- Cheaper fixes to try first

## The simple explanation

Chunks are searched alone. So a sentence that made sense in its document can become unclear:

```text
The company's revenue grew by 3% over the previous quarter.
```

Which company? Which quarter? The embedding of that sentence can't know, so a search for "ACME Q2 revenue" may miss it.

**Contextual retrieval**, [described by Anthropic](https://www.anthropic.com/news/contextual-retrieval), fixes it at ingest. For each chunk, a model reads the whole document and writes a short note saying where the chunk fits. The note is added to the chunk before embedding:

```text
This is from ACME Corp's Q2 2023 SEC filing. Revenue was $314 million last quarter.
The company's revenue grew by 3% over the previous quarter.
```

Think of a photo album. A loose photo of three people at a beach means little. Write "Dad's 60th birthday, Goa, 2019" on the back, and you can find it later.

It costs one model call per chunk, once, at ingest. Prompt caching helps a lot, because the whole document is the same for every chunk in it.

## An example

Anthropic's reported failure rates, for the top 20 chunks retrieved:

| Method | Failure rate | Reduction |
| --- | --- | --- |
| Plain embeddings | 5.7% | |
| Contextual embeddings | 3.7% | 35% |
| Plus contextual BM25 | 2.9% | 49% |
| Plus reranking | 1.9% | 67% |

It put the one-time cost at $1.02 per million document tokens, using prompt caching. These are Anthropic's own results and assumptions, on its own test, so treat them as a guide.

A separate [2025 study](https://arxiv.org/html/2504.19754v1) found the same pattern: contextual retrieval with rank fusion and reranking gave the best accuracy, at a high compute cost.

## How ShopHelper does it

ShopHelper uses a cheap version of the same idea. Every chunk repeats its document's title:

```python file=src/shophelper/rag/pipeline.py
chunks.append("\n".join([title, *current]).strip())
```

So "within 5-7 business days" arrives as:

```text
# Refund Policy
- Approved refunds go back to the **original payment method** within **5-7 business days**. We do not issue cash refunds.
```

That's context, with no model call.

The [laptop stand bug](03-chunking.md) showed where it runs out. The Care rule said "electronics only", and the definition of electronics was in another chunk. A title couldn't fix that. Contextual retrieval might have, by adding a note about what counts as electronics.

The fix used was simpler: the Care line now carries its own definition. **When you control the documents, fixing them is the cheapest option of all.**

So the order to try:

1. **Add titles and headings** to chunks. Free.
2. **Make important lines stand alone**, if you control the documents. Nearly free.
3. **Contextual retrieval**, for large collections you can't rewrite, such as years of PDFs.

Full contextual retrieval is **not in ShopHelper**. With 9 short, tidy documents, it would add a step for little gain.

## In the market

Checked on 2026-11-06.

| Approach | How it adds context | Cost |
| --- | --- | --- |
| Titles and headings | Copies them into each chunk | Almost none |
| [Contextual retrieval](https://www.anthropic.com/news/contextual-retrieval) | A model writes a note per chunk | One call per chunk, at ingest |
| Late chunking | Embeds the document first, then splits, so each chunk's vector carries context | Needs a long-context embedding model |
| Parent and child chunks | Searches small chunks, returns the larger section | More storage |

The [2025 study](https://arxiv.org/html/2504.19754v1) found late chunking more efficient, but with results that varied by model and data. Test it before assuming.

Anthropic's post also notes that if your knowledge base is under about 200,000 tokens, roughly 500 pages, you can include all of it in the prompt and skip RAG. All 9 policies here are about 1,400 tokens. [The last lesson in this stage](09-rag-long-context-or-fine-tuning.md) weighs that up.

## Try it

1. Sign in, open **How it works**, then **RAG explorer**.
2. Scroll to **What's stored**, open `warranty.md`, and read each chunk.
3. For each one, ask: if this were the only thing the model saw, would it make sense?
4. Find the Care chunk, and see how it now names the electronics categories.

## Interview questions

### What's contextual retrieval?

**Strong answer:** Chunks lose meaning when read alone, so at ingest a model writes a short note for each one, saying where it sits in the document, and that's added before embedding. Anthropic reported it cut retrieval failures by 35%, or 67% with BM25 and reranking. The cost is a model call per chunk, reduced by prompt caching. I'd try cheaper things first: my project repeats the title on each chunk, and when I hit a real bug from missing context, I fixed the document.

**Follow-up:** When is it clearly worth it?

### You inherit 10 years of messy PDFs. How do you get good retrieval?

**Strong answer:** I can't rewrite them, so I'd invest in processing. First extract text properly, keeping headings and tables. Chunk by structure where I can. Then build a test set from real questions, and measure. Contextual retrieval is a good fit here, since the documents can't be fixed. I'd add a reranker, and hybrid search for codes and names, and I'd keep metadata like date and source, so old documents don't win.

**Follow-up:** How do you handle tables?

## Check yourself

### Why can a chunk be hard to find?

- [x] It may lose the context that says what it's about — right: "revenue grew 3%" doesn't say whose.
- [ ] Chunks are stored in random order — order isn't the issue.
- [ ] The model can't read short text — it reads it fine.

### When does contextual retrieval do its work?

- [ ] On every question — that would be slow.
- [x] Once, at ingest — right: the note is added before embedding.
- [ ] Only when a search fails — it happens in advance.

### You control the documents. What's the cheapest fix for a chunk that lacks context?

- [ ] A bigger embedding model — that won't add missing facts.
- [ ] Contextual retrieval — it costs a call per chunk.
- [x] Make the line stand alone — right: that's how the Care bug was fixed.
