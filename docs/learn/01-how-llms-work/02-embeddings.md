---
title: Embeddings
checked: 2026-11-06
---

## What you'll learn

- How meaning can be turned into numbers
- Why that lets a computer search by meaning, not just matching words
- How similarity is measured
- Why similarity scores are less simple than they look

## The simple explanation

Computers compare numbers easily, but not meaning. An **embedding** bridges that: a list of numbers that stands for the meaning of some text. An **embedding model** turns text into that list.

Picture a map. Cities that are close on the map are close in real life. An embedding is like a position on a map of meaning: text about refunds lands near other text about refunds, and far from text about bread.

A real map has 2 directions. This project's embedding model uses 768. Nobody can picture that, and no single number means anything you could name. But the idea is the same: close means similar.

So to find text similar to a question, you turn the question into an embedding, then look for the nearest ones. That's called **semantic search**, and it's the first half of [RAG](../05-rag/01-why-rag.md).

The list of numbers is called a **vector**. To compare two, we use **cosine similarity**, which measures whether they point the same way. Close to 1 means very similar.

## An example

Here's a real result from this project's embedding model. The question was "How long do refunds take?", compared with six other sentences:

| Sentence | Similarity |
| --- | --- |
| Approved refunds go back to the original payment method within 5-7 business days. | 0.874 |
| Standard shipping takes 3-5 business days. | 0.699 |
| When will I get my money back? | 0.614 |
| What is your return policy? | 0.506 |
| The capital of France is Paris. | 0.383 |
| How do I bake sourdough bread? | 0.345 |

The best match shares only one real word with the question, "refunds". Unrelated sentences score low. That's the power of it.

But look closer. "When will I get my money back?" asks the same thing in other words, yet it scored *below* a sentence about shipping. A likely reason: the shipping sentence is shaped like an answer about time, and it was labelled as a document, while the other is a question. Whatever the cause, it shows that embeddings capture more than topic.

So don't read these as percentages. A score only means something compared with others from the same model. An unrelated sentence doesn't score 0.

## How ShopHelper does it

Turning text into vectors is one call:

```python file=src/shophelper/rag/pipeline.py
def embed(texts: list[str], prefix: str) -> list[list[float]]:
    resp = _client().embeddings.create(
        model=get_settings().embedding_model, input=[prefix + t for t in texts]
    )
    return [item.embedding for item in resp.data]
```

Notice `prefix`. This model expects to be told whether text is a question or a document:

```python file=src/shophelper/rag/pipeline.py
DOCUMENT_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "
```

That's specific to this model, and [its model card](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5) says it's required. Leave it out, and search quality drops with no error. Always read the card.

The vectors are stored in Postgres, and the size must match the model:

```sql file=src/shophelper/core/schema.sql
embedding    VECTOR(768) NOT NULL,     -- must equal the embedding model's dimensions
```

The most important rule: **embeddings from different models can't be compared.** Each model makes its own map. Change your embedding model, and you must re-embed everything.

## In the market

Checked on 2026-11-06. Sizes are from each provider's own docs.

| Model | Size | Where it runs | Notes |
| --- | --- | --- | --- |
| [nomic-embed-text-v1.5](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5) | 768, can shrink | Your machine | Used here locally. Open, Apache 2.0 |
| [Amazon Titan Text Embeddings V2](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html) | 1,024, 512 or 256 | AWS Bedrock | Used here on AWS |
| [OpenAI text-embedding-3-small](https://developers.openai.com/api/docs/guides/embeddings) | 1,536, can shrink | OpenAI's API | |
| [OpenAI text-embedding-3-large](https://developers.openai.com/api/docs/guides/embeddings) | 3,072, can shrink | OpenAI's API | |

**More numbers isn't simply better.** Larger vectors take more storage and slower searches. Several models let you shorten vectors for a small loss in quality.

**How to choose:** check that it handles your languages, whether your data may leave your systems, and the cost at your volume. Then test it on your own questions, because public benchmarks may not match your documents.

## Try it

1. Sign in, open **How it works**, then **RAG explorer**.
2. Search "how long do refunds take". Look at the row of numbers: that's the start of the question's vector.
3. Compare the scores of the results.
4. Try "when do I get my money back". Does the same passage win?

## Interview questions

### What's an embedding, and what do you use it for?

**Strong answer:** It's a vector of numbers representing the meaning of text, produced by an embedding model, where similar meanings land close together. I use it for semantic search: I embed document chunks once, store them, embed the question at query time and find the nearest. In my project that's a 768-dimension model with pgvector. It finds relevant text even when the words differ.

**Follow-up:** When would keyword search beat embeddings?

### You want to change your embedding model. What's involved?

**Strong answer:** You have to re-embed everything, because vectors from different models aren't comparable. If the size changes, the database column changes too. I'd build the new index alongside the old one, compare retrieval quality on a test set, then switch and keep the old one until I'm confident. For a large corpus that re-embedding is a real cost, so I'd plan for it.

**Follow-up:** How would you switch without downtime?

### Is a similarity score of 0.8 good?

**Strong answer:** It depends. Scores are only meaningful relative to each other, from the same model. In my tests an unrelated sentence scored around 0.35, and a sentence asking the same thing in other words scored lower than one about shipping. So I wouldn't set a fixed cut-off without measuring. I'd look at where relevant and irrelevant results fall on real questions.

**Follow-up:** How would you stop the system answering when nothing relevant was found?

## Check yourself

### What does it mean if two embeddings are close together?

- [x] The texts are similar in meaning, as that model sees it — right: close on the map means similar.
- [ ] The texts share the same words — they may share none.
- [ ] One text was copied from the other — closeness isn't about copying.

### You switch to a new embedding model. What must you do?

- [ ] Nothing, as vectors are universal — each model makes its own map.
- [ ] Re-embed only new documents — old and new vectors couldn't be compared.
- [x] Re-embed everything — right: vectors from different models aren't comparable.

### How should you read a similarity score of 0.6?

- [ ] It's 60% relevant — it isn't a percentage.
- [x] Only compared with other scores from that model — right: even unrelated text scores above 0.
- [ ] As a pass, because it's over 0.5 — there's no universal cut-off.
