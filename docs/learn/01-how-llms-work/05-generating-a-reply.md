---
title: How a reply is generated
checked: 2026-11-06
---

## What you'll learn

- The two phases of every model call: prefill and decode
- What the KV cache is, and why it matters
- Why long prompts make the first word slow
- What to measure when a chat feels slow

## The simple explanation

When you send a message, the model does two very different jobs.

**Prefill: reading.** The model reads your whole prompt at once. All the tokens can be processed together, so this is fast per token. But nothing appears until it's finished.

**Decode: writing.** The model writes one token at a time. Each new token depends on the last, so they can't be done together.

Think of a student in an exam. Reading the question paper is a quick scan of the whole page. Writing the answer is one word at a time, and that can't be rushed.

So two numbers describe how fast a model feels:

| Measure | Meaning | Depends on |
| --- | --- | --- |
| **Time to first token** | How long until words appear | Mostly prompt length |
| **Tokens per second** | How fast words appear after that | The model and hardware |

There's a trick that makes writing possible. To write each token, the model needs what it worked out about every earlier token. Redoing that each time would be hugely wasteful. So it keeps those results in memory: the **KV cache**. Prefill fills it, and decode adds to it. It's like the student's rough notes: no need to reread the paper for every word.

The cost is memory. The cache grows with every token, and [one well-known paper](https://arxiv.org/abs/2309.06180) describes it as huge and constantly changing size. That's why long conversations need more memory, and why the serving tool vLLM manages it like an operating system manages memory.

## An example

These were measured on this project's local model, on this machine. Each prompt was unique, so nothing was reused:

| Prompt size | Time to first token | Writing speed |
| --- | --- | --- |
| 48 tokens | 0.60 s | 63 tokens a second |
| 1,314 tokens | 1.42 s | 39 tokens a second |
| 2,580 tokens | 2.73 s | 31 tokens a second |
| 3,852 tokens | 3.99 s | 26 tokens a second |

Two things to see:

- **Reading takes about a second per 1,000 tokens here.** Triple the prompt, and the wait for the first word roughly triples.
- **Writing got slower as the prompt grew**, because each new token has more earlier tokens to look at.

Your hardware will differ, and a cloud model is usually much faster. The shape is what matters.

## How ShopHelper does it

The agent often makes two model calls per question: one to choose a tool, one to answer. So the customer waits for two prefills. The trace page shows this. In one real turn:

- Model call 1 was the code's own search, so it took almost no time
- Model call 2 had its first token at 0.82 s, with 1,757 tokens in
- The whole turn took 3.51 s

Because a reply can take seconds, ShopHelper streams it, so words appear as they're written:

```python file=src/shophelper/agent/service.py
async for mode, payload in self.graph.astream(
```

Streaming doesn't make the model faster. It makes the wait feel shorter, because the customer starts reading at the first token, not the last. [Streaming](../06-building-the-app/03-streaming.md) covers how.

The cap on how much the model may write also limits the worst case:

```python file=src/shophelper/core/config.py
max_tokens: int = 1024
```

## Try it

1. Sign in, open **How it works**, and click the **Tool call** example.
2. In the trace, find "First token at" on the last model call.
3. Compare it with the time on **Turn finished**. The gap is mostly decode.
4. Ask a question that needs a long answer, such as "Explain your return policy in detail". Watch how the words arrive at a steady pace.

## Interview questions

### A chat product feels slow. How do you investigate?

**Strong answer:** I'd split the time up, because the fixes differ. Time to first token is mostly prompt length, so if that's high I'd shorten the prompt, cut retrieved context, or use prompt caching. If tokens per second is the problem, I'd look at the model or ask for shorter replies. Then I'd count model calls: an agent can make several in a row, so each adds a full wait. I'd also stream, so the wait feels shorter.

**Follow-up:** What would you do if the agent needs three tool calls?

### What's the KV cache?

**Strong answer:** During generation, each new token needs information from all earlier tokens. The KV cache keeps those results so they aren't recomputed for each new token. Prefill builds it, decode adds to it. It trades memory for speed, and it grows with the context, so long prompts limit how many requests a server can handle at once.

**Follow-up:** Why does that matter for cost?

### Why is prefill fast per token, while decode is slow?

**Strong answer:** In prefill all the prompt tokens are known, so they can be processed in parallel, and the hardware is kept busy. In decode each token depends on the one before, so it's one at a time, and much of the time goes on moving data through memory. In my measurements prefill ran at about 1,000 tokens a second, and decode at 26 to 63.

**Follow-up:** How do providers serve many users at once, then?

## Check yourself

### You double your prompt's length. What gets noticeably worse?

- [x] Time to first token — right: the model must read it all before writing.
- [ ] Nothing, as prompts are free — every token has to be read.
- [ ] Only the price — it also changes how long the wait is.

### Why does streaming help?

- [ ] It makes the model write faster — the writing speed doesn't change.
- [x] The customer starts reading at the first token — right: the wait feels much shorter.
- [ ] It uses fewer tokens — the token count is the same.

### What does the KV cache trade?

- [ ] Accuracy for speed — it doesn't change the answer.
- [x] Memory for speed — right: stored results avoid repeating work, but take up memory.
- [ ] Cost for quality — it's about reusing work.
