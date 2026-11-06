---
title: Chunking
checked: 2026-11-06
---

## What you'll learn

- Why documents get cut into pieces before they're searched
- How chunk size trades precision against context
- How ShopHelper chunks its policies, in about 20 lines
- A real bug caused by chunking, and how it was fixed
- Which strategies exist, and how to choose

## The simple explanation

RAG finds the passages most relevant to a question and gives them to the model. So you need passages to find. **Chunking** means cutting each document into small pieces, called **chunks**, before storing them.

Why not store whole documents? Think of a shop assistant asked "how long do refunds take?". You'd want them to open the right page, not hand over the whole staff manual. A search works the same way. A small chunk about one idea matches a question well. A whole document mixes many ideas, so it matches everything weakly.

So chunk size is a trade-off:

| Too small | Too large |
| --- | --- |
| Loses context: "within 30 days" of what? | Blurs several ideas together |
| The answer may be split across chunks | Wastes space in the prompt, which costs money |
| Finds exact wording well | Finds the right document, but the wrong detail |

There's no perfect size. The right answer depends on your documents and your questions, so it's something to measure, not guess.

## An example

Take the start of the refund policy:

```text
# Refund Policy
- Refunds are only issued for orders that have been delivered and are within the 30-day refund window.
- Orders that have not shipped yet should be cancelled instead of refunded.
- Approved refunds go back to the original payment method within 5-7 business days.
```

Cut every 60 characters, and a rule breaks in half: "Refunds are only issued for orders that have been deliv". Neither half makes sense alone.

Cut on line breaks instead, and each rule stays whole. But now one chunk might just say "within 5-7 business days". Of what? The title fixes that:

```text
# Refund Policy
- Approved refunds go back to the original payment method within 5-7 business days.
```

Now both the search and the model know the subject.

## How ShopHelper does it

The whole chunker is one small function:

```python file=src/shophelper/rag/pipeline.py
def chunk_markdown(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = lines[0] if lines and lines[0].startswith("#") else ""
    body = lines[1:] if title else lines
    ...
    for line in body:
        if current and len("\n".join([title, *current, line])) > max_chars:
            chunks.append("\n".join([title, *current]).strip())
            current = []
        current.append(line)
```

It makes two choices:

1. **Split on line boundaries.** Each bullet in these policies is a complete rule, so a rule is never cut in half.
2. **Repeat the title on every chunk**, so a chunk still says what it's about.

`MAX_CHUNK_CHARS` is 350. Measured in the running database, 9 policies make 24 chunks, averaging 252 characters, from 89 to 377. One goes over 350 because a single line is never split.

This suits short, bullet-pointed policies. A long article with paragraphs would need something else.

### A real bug: chunks arrive alone

Here's what makes chunking more than a tidy-up job. The agent told a customer ShopHelper Care wasn't available for a laptop stand, because "it is not an electronic product". That's wrong. Laptop accessories are electronics.

The model wasn't ignoring the policy. Printing the retrieved passages showed the cause. The warranty policy had one chunk saying Care is for "electronics only", and a *different* chunk defining electronics. The search returned the first, not the second. So the model saw a rule using a word it had no definition for, and guessed.

The fix was one line: the Care rule now names the categories itself. All 16 test wordings were then answered correctly.

**The lesson:** a chunk is read alone. If a sentence depends on a definition elsewhere, that definition may not arrive. When an answer is wrong, print the passages before blaming the model.

## In the market

Checked on 2026-11-06.

| Strategy | How it works | Good for | Cost |
| --- | --- | --- | --- |
| Fixed size | Cut every N characters, often with overlap | A quick baseline | Can cut ideas in half |
| Recursive | Split on headings, then paragraphs, then sentences | Most documents: a common default | Low |
| By structure | Split on the document's own parts, as ShopHelper does | Markdown, policies, code | Needs clean structure |
| Semantic | Start a new chunk where the meaning shifts | Long, unstructured text | Needs embedding calls |
| Parent and child | Search small chunks, return the larger section | When answers need surrounding text | More storage |
| Late chunking | Embed the whole document, then split | Keeping document-wide context | Needs a long-context embedding model |
| Contextual retrieval | A model writes a short note placing each chunk in its document, added before embedding | Chunks that lose meaning alone, like our bug | A model call per chunk |

**Overlap** means repeating the end of one chunk at the start of the next, so an idea on a boundary isn't lost.

One [2025 study](https://arxiv.org/html/2504.19754v1) compared the newer methods. Contextual retrieval with reranking gave the best accuracy, at a high compute cost. Late chunking was cheaper, but its results varied with the model and data. Fixed and semantic chunking differed little without added context. That's one study, so treat it as a hint and test on your own documents.

**How to choose:** start with the simplest thing that respects your documents' structure. Build a small set of real questions with known answers, then change one thing at a time and measure. [Evals](../07-evals-and-testing/01-evals.md) shows how.

## Try it

1. Sign in, open **How it works**, then **RAG explorer**.
2. Scroll to **What's stored**, open `refunds.md`, and read its chunks. Check that each one starts with its title.
3. Search "how long do refunds take". Find which chunk comes first, and read what it contains.
4. Search "ShopHelper Care laptop stand". Notice that the Care chunk now names laptop accessories itself.

## Interview questions

### How would you choose a chunk size for a RAG system?

**Strong answer:** I wouldn't pick one number up front. Too small loses context, and too large blurs ideas and wastes prompt space. I'd start from the documents' structure, so a rule or section stays whole, and use a recursive splitter as a baseline for unstructured text. Then I'd build a small set of real questions with known answers and measure retrieval as I change one thing at a time. In my project the policies are short bullet points, so I split on lines, up to 350 characters, and repeat the title.

**Follow-up:** How would you measure whether a change helped?

### A RAG answer is wrong, but the right document is in your database. How do you debug it?

**Strong answer:** I'd find out which step failed before changing anything. First, print the retrieved passages. If the right chunk isn't there, it's a retrieval problem: chunking, embeddings or the query. If it's there and the answer's still wrong, it's a generation problem. I hit this in my project: the agent got a rule right but misclassified a product, because the rule's chunk said "electronics only" and the definition of electronics was in another chunk that wasn't retrieved. The fix was making the chunk stand alone.

**Follow-up:** What if the right chunk is retrieved, but ranked too low?

### What's contextual retrieval, and when is it worth it?

**Strong answer:** A model writes a short note for each chunk, saying where it sits in its document, and that note is added before embedding. It helps when chunks lose meaning alone, which is exactly the failure I hit. The cost is a model call per chunk at ingest, which adds up on a large corpus. So I'd try cheaper fixes first, like better structure or titles, and use it if measurements show a real gain.

**Follow-up:** How would you keep that cost down?

## Check yourself

### Why repeat the document title on every chunk?

- [ ] To make the chunks bigger — size isn't the point, and it does add a little.
- [x] So a chunk still says what it's about when read alone — right: "within 30 days" means nothing without its subject.
- [ ] Because the database needs a title column — it doesn't: the title goes in the chunk's text.

### The right chunk exists, but it wasn't retrieved. What kind of problem is that?

- [x] A retrieval problem — right: the model never saw it, so a better prompt can't help.
- [ ] A generation problem — that's when the chunk arrives and the model still gets it wrong.
- [ ] A hallucination problem — hallucination may follow, but it's the symptom here, not the cause.

### What's the best way to pick a chunking strategy?

- [ ] Use whichever is newest — newer methods can cost more, with no gain on your documents.
- [ ] Use 512 tokens, since most teams do — a common number isn't a measured answer.
- [x] Start simple, then measure on real questions — right: the best choice depends on your documents.
