---
title: Context windows and prompt caching
checked: 2026-11-06
---

## What you'll learn

- What a context window is, and what fills it
- Why bigger isn't automatically better
- How prompt caching saves time and money
- Why the order of your prompt matters

## The simple explanation

A model has no memory. Everything it knows about your conversation has to be sent every time. The **context window** is the limit on how much it can take in one call, counted in tokens.

Think of a desk. The model can only work with what's on the desk right now. Anything not on it doesn't exist.

What goes on the desk:

- The system prompt
- Tool descriptions
- The conversation so far
- Tool results and retrieved documents
- The reply it's writing

A big desk doesn't solve everything. More to read costs more, takes longer, and gives important details more to compete with. So you want the *right* things on the desk, not everything.

**Prompt caching** helps with a different waste. Most of a prompt is the same every time, such as the instructions. Without caching, the model reads it all again on each call. With caching, the provider keeps the result of reading it, so identical text at the **start** of a prompt can be reused.

It's like a student who has already read the textbook chapter. For the next question, they only read what's new.

It only works from the start, and it has to match exactly. Change one early word, and everything after it is read again. So the rule is: **stable things first, changing things last.**

## An example

We sent this project's local model the same 3,855-token prompt three times:

| Run | Time to first token |
| --- | --- |
| 1 | 4.05 s |
| 2 | 0.07 s |
| 3 | 0.07 s |

That's about 58 times faster, measured on this machine with LM Studio's own cache.

Now the mistake that wastes it. Suppose a prompt starts like this:

```text
Today is 2026-11-06 12:04:31. You are a helpful support agent...
```

The time changes every call, and it's at the very start. So nothing after it can match, and the cache never helps. Move that line to the end, and the stable part can be reused.

## How ShopHelper does it

The prompt is built with the stable part first:

```python file=src/shophelper/agent/graph.py
context = [SystemMessage(SYSTEM_PROMPT), *state["messages"]]
```

The system prompt comes first and never changes, and the conversation follows. So LM Studio can reuse the start of the prompt.

This local model loads with a 16,640 token window, set in LM Studio to fit this machine's memory, though the [model is designed for 262,144](https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507). One turn here used about 1,750 tokens, so that's plenty, but a long conversation keeps growing. A real product would need a plan for that, such as summarising older turns.

**A surprise from this project:** the cache also affected testing. One refund wording scored 20 of 20 when repeated, and 0 of 20 when other questions came between. Repeating a prompt repeated its result, so the test proved nothing. That's why measurements here put unrelated questions between tries.

Explicit prompt caching on AWS is **not in ShopHelper**. It would be a sensible next step, because the same system prompt goes out on every call.

## In the market

Checked on 2026-11-06. From Anthropic's [prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) and [models overview](https://platform.claude.com/docs/en/about-claude/models/overview).

Current Claude models have a 1 million token window. Other providers differ, so check before you design around a number.

Claude's caching works like this:

| Detail | Value |
| --- | --- |
| What must match | The exact start of the prompt, in order: tools, system, messages |
| Default lifetime | 5 minutes, refreshed each time it's used |
| Cost to write | 1.25 times the input price |
| Cost to read | About a tenth of the input price, or less on some models |
| Minimum size | Depends on the model: from 512 tokens on current ones |

So a cache pays for itself after one reuse. Too short a prompt simply isn't cached, with no error, so check the usage fields to confirm a hit.

Common things that break a cache: changing tool definitions, editing the system prompt, and putting a timestamp near the start.

## Try it

1. Sign in, and open **How it works**.
2. Ask "What is your return policy?". On the final model call, note "First token at" and the tokens in.
3. Ask the exact same question again, in the same conversation, and compare.

You might expect the 0.07 s from the table above. You won't get it. Here it went from 1.44 s to 1.52 s, and the input grew from 1,048 tokens to 1,620. The question is the same, but the prompt isn't: your first question and its answer are now part of it. Caching skips the part that matches, and everything new still has to be read. That's what a cache does in a real chat: it stops the cost growing, and it doesn't make replies instant.

## Interview questions

### Models now have huge context windows. Why not just put everything in the prompt?

**Strong answer:** Cost, speed and quality. You pay for every token, and in my measurements the wait for the first word grew by about a second per 1,000 tokens. More text also means more for the important part to compete with. So I'd retrieve what's relevant instead. A large window is still useful, for example for reading a whole contract once.

**Follow-up:** When would you choose long context over RAG?

### How would you use prompt caching to cut costs?

**Strong answer:** I'd put stable content first: tool definitions, then the system prompt, then fixed reference text, and changing content last. Caching matches the exact start of the prompt, so one changing value early on, like a timestamp, defeats it. On Claude a read costs about a tenth of the input price, and a write 1.25 times, so it pays off after one reuse. Then I'd check the usage fields, because a prompt that's too short is silently not cached.

**Follow-up:** How would you confirm it's working in production?

### How do you handle a conversation that outgrows the context window?

**Strong answer:** Don't wait for the error. Options are keeping the last few turns, summarising older ones, or storing facts and retrieving them when needed. I'd keep the system prompt and anything the task depends on, and count tokens rather than messages. Summaries lose detail, so I'd test what gets lost.

**Follow-up:** What must never be dropped?

## Check yourself

### Where should a changing value like the time go in a prompt?

- [ ] At the very start, so the model sees it first — that stops everything after it being reused.
- [x] Near the end — right: the stable part at the start can still match.
- [ ] Prompts shouldn't contain the time — it's fine, if it's in the right place.

### What's in the context window?

- [ ] Only the customer's latest message — the model would have no instructions or history.
- [x] Everything sent for that call, plus the reply — right: instructions, history, tool results and output.
- [ ] Everything the model learned in training — that's in its parameters.

### Why not fill a 1 million token window on every call?

- [ ] The model would refuse — it wouldn't.
- [x] It costs more, takes longer, and adds noise — right: you want the right things in the window.
- [ ] Only the first 1,000 tokens are read — it reads all of it.
