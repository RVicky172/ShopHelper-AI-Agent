---
title: RAG, long context or fine-tuning?
checked: 2026-11-06
---

## What you'll learn

- The three ways to give a model your knowledge
- What each is good at
- How to choose, with real numbers
- Why the answer is often a mix

## The simple explanation

Say a model needs to know your company's information. There are three ways:

| Option | Picture | How |
| --- | --- | --- |
| **Long context** | Hand them the whole book | Put everything in the prompt |
| **RAG** | Open-book exam | Search, then pass the relevant pages |
| **Fine-tuning** | Send them on a course | Train further on your examples |

Each suits a different job:

| | Long context | RAG | Fine-tuning |
| --- | --- | --- | --- |
| **Good for** | Small or one-off documents | Large, changing knowledge | Style, format, narrow tasks |
| **Updates** | Instant | Instant, with a re-embed | Retrain |
| **Cost per question** | High: everything is read | Low | Low |
| **Set-up work** | None | Moderate | High |
| **Shows its source** | Sometimes | Yes | No |
| **Main risk** | Cost, and details getting lost | Search misses the answer | Facts blur or go stale |

The most common mistake is using fine-tuning to add facts. Facts change, and a trained-in fact can't show where it came from. Fine-tuning teaches *how* to answer, not *what's true today*.

## An example

Here's a real comparison for ShopHelper's policies, which total about 1,400 tokens. Prices are [Claude Sonnet 5.5's list rates](https://platform.claude.com/docs/en/about-claude/models/overview), for the input side only:

| Approach | Input tokens | Input cost per 1,000 questions |
| --- | --- | --- |
| All 9 policies in every prompt | About 1,400 extra | About $2.80 |
| Prompt caching on those policies | About 1,400, mostly cached | About $0.28 to read, plus writes |
| RAG, top 4 passages | About 300 extra | About $0.60 |

At this size, the honest answer is that **any of them would work**. Anthropic's [contextual retrieval post](https://www.anthropic.com/news/contextual-retrieval) makes the same point: under about 200,000 tokens, you can include everything and skip RAG.

So why does ShopHelper use RAG? Partly because the project exists to teach it. But it also scales: with 10,000 documents, putting everything in the prompt stops being an option.

Long prompts have a quality cost too. The paper [Lost in the Middle](https://arxiv.org/abs/2307.03172) found models used information best at the beginning or end of the input, and did worse when it was in the middle. Newer models have improved, but you should test yours, and not assume a big window means it reads everything equally.

## How ShopHelper does it

| Need | Approach | Why |
| --- | --- | --- |
| Policies | RAG | They change, and answers can show a source |
| Live orders | A tool | Data changes constantly |
| Tone and rules | System prompt | Easy to change, and testable |
| Fine-tuning | Not used | Nothing here needs it |

Notice a fourth option in that table. **Live data isn't a RAG problem.** "Where is my order?" should be a database lookup, not a document search. Using the right tool for each kind of information matters more than picking one technique.

Here's how one policy change went in this project: one edit to a file, then `docker compose up setup`, which re-embedded just that document. With fine-tuning, that same change would mean new training data and a new model.

## In the market

Checked on 2026-11-06.

Limits move quickly. Current Claude models have a [1 million token window](https://platform.claude.com/docs/en/about-claude/models/overview), which makes long context more practical than it was, especially with [prompt caching](../01-how-llms-work/07-context-windows-and-prompt-caching.md). So "RAG is always needed" is out of date. So is "RAG is dead". Cost, freshness, access control and citations still favour search for large or private collections.

**Access control** is worth a mention. With RAG you can filter what each user may see before the model reads it. Putting everything in one prompt loses that.

**How to choose:**

1. Is it live data? Use a tool.
2. Does everything fit, and is it small? Try long context with caching.
3. Is it large or changing, or do you need sources or per-user access? Use RAG.
4. Do you need a consistent style, or a cheaper model for a narrow job? Then consider fine-tuning.

## Try it

1. Sign in, open **How it works**, and ask "How long do refunds take?".
2. Note the input tokens on the final model call.
3. Work out what it would be if all 9 policies were sent instead: replace the passages with about 1,400 tokens.
4. Multiply by 1,000 questions a day. At what number of documents would you change your mind?

## Interview questions

### When would you use RAG, long context, or fine-tuning?

**Strong answer:** Long context for small or one-off documents, with caching if they repeat. RAG for large or changing knowledge, or when I need sources and per-user access. Fine-tuning for behaviour, like a format or tone, or to make a small model good at a narrow job. Not for facts, because they change. Live data needs a tool. My project's policies are only about 1,400 tokens, so long context would work too. RAG is what scales.

**Follow-up:** Do bigger context windows make RAG obsolete?

### Your knowledge base is 500 pages. What do you build?

**Strong answer:** I'd start by testing the simple option, because that's around 200,000 tokens, which fits in a large window. With prompt caching it might be good enough, and it's far less to build. I'd measure quality, cost and speed on real questions. If documents change often, need citations, or different users see different things, I'd move to RAG.

**Follow-up:** What would make you choose RAG straight away?

### Can you fine-tune a model to know your product catalogue?

**Strong answer:** I wouldn't. Prices and stock change, fine-tuned facts blur, and it can't cite a source. I'd give it a tool that reads the catalogue, or search it. Fine-tuning might help it answer in the right style. So facts come from systems of record, and the model only explains them.

**Follow-up:** What's a good use of fine-tuning, then?

## Check yourself

### A customer asks where their order is. What's the right approach?

- [ ] RAG over documents — orders aren't documents.
- [ ] Fine-tuning — you'd never keep up.
- [x] A tool that reads the database — right: live data needs a lookup.

### What's fine-tuning good at?

- [ ] Keeping facts up to date — every change would mean retraining.
- [x] Teaching a style, format or narrow task — right: how to answer, not what's true today.
- [ ] Showing the source of an answer — it can't.

### Your documents total 50 pages and rarely change. What should you try first?

- [x] Long context, with prompt caching — right: it's the least to build, if it's good enough.
- [ ] A dedicated vector database — that's more than you need.
- [ ] Fine-tuning — that's the wrong tool for facts.
