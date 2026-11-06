---
title: Context engineering
checked: 2026-11-06
---

## What you'll learn

- How context engineering differs from prompt engineering
- Why more context can make answers worse
- The main ways to manage what a model sees
- How to find what's really in your prompt

## The simple explanation

A prompt is one part of what a model sees. An agent also sends tool descriptions, history, retrieved documents and tool results, and all of it changes on every call.

**Context engineering** is deciding what goes in. Anthropic [describes it](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) as curating the best set of tokens for each call. Prompt engineering is about writing the instructions. Context engineering is about everything around them.

Think of briefing a colleague before a meeting. You don't hand over every email since January. You pick what they need, in a sensible order. Too little, and they're unprepared. Too much, and the important point gets lost.

That second problem has a name. **Context rot** means a model gets worse at recalling information as the context grows. So context is a limited resource, and each extra token has a cost, even in a huge window.

The main techniques:

| Technique | What it means |
| --- | --- |
| **Retrieve just in time** | Keep a reference, and load the detail when it's needed |
| **Compaction** | Summarise a long conversation, and carry on from the summary |
| **Clearing tool results** | Drop old results the model no longer needs |
| **Note-taking** | The agent writes notes outside the window, and reads them later |
| **Sub-agents** | A helper does a focused job in its own window, and returns a short summary |

## An example

Here's what fills one real turn in this project. It used 1,757 input tokens for "What is ShopHelper Care?":

| Part | What it is | Tokens |
| --- | --- | --- |
| Question | The customer's message | About 14 |
| System prompt | Standing rules | About 300 |
| Tool descriptions and search results | What the model may ask for, and 4 policy passages | About 1,440 |

The customer's own words are under 1% of what the model reads. That's normal: most of a prompt is what you add.

Now compare two ways of answering "How long do refunds take?":

- **Paste all 9 policies into every call.** That's about 1,300 tokens on every question, even "hello", and most of it is irrelevant.
- **Search first.** Only the 4 most relevant passages go in.

The second is cheaper and leaves less to distract the model. But it adds a risk: the search has to find the right thing.

## How ShopHelper does it

**Retrieve just in time.** Policies aren't in the prompt. The agent fetches them with `search_policy` only when needed, and the number of passages is capped:

```python file=src/shophelper/agent/tools.py
def search_policy(query: str, top_k: int = 4) -> dict[str, Any]:
```

**Stable things first.** The system prompt leads, then the conversation:

```python file=src/shophelper/agent/graph.py
context = [SystemMessage(SYSTEM_PROMPT), *state["messages"]]
```

**Hide what the model doesn't need.** Customer emails and phone numbers are masked before the model sees them, and identity never enters the context at all. Leaving something out is the strongest protection there is.

**A bug about context.** Earlier in this course you met the [laptop stand bug](../05-rag/03-chunking.md). The agent had the rule "electronics only", but not the definition of electronics. Too little context, in exactly the wrong place. Printing what the model really received found it in minutes.

**Not in ShopHelper:** summarising long conversations. Each call sends the whole conversation, and nothing trims it. Chats here are short, but a real product would need a plan, or a long chat would eventually hit the 16,640 token limit.

## In the market

Checked on 2026-11-06.

Most frameworks offer pieces of this, such as trimming or summarising messages. Anthropic's [guide to context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) is a good primary source on the techniques above.

Choosing between them:

| Situation | Good fit |
| --- | --- |
| Short support chats | Retrieve just in time, little else |
| Long conversations | Compaction |
| Agents using many tools | Clear old results |
| Long tasks across sessions | Note-taking |
| Big tasks with separate parts | Sub-agents, at a higher token cost |

## Try it

1. Sign in, open **How it works**, and ask "How long do refunds take?".
2. In the trace, open the `search_policy` step, and read which passages came back.
3. Ask yourself: is everything there needed? Is anything missing?
4. Look at the input tokens on the final model call. That's the size of the whole context.

## Interview questions

### What's context engineering, and why does it matter for agents?

**Strong answer:** It's deciding what the model sees on each call: instructions, tools, history, retrieved data and tool results. It matters more for agents because context grows on every step, and quality can fall as it does. So I treat tokens as limited. I retrieve when needed, cap results, and trim or summarise history. In my project policies aren't in the prompt: the agent searches, and gets the top 4 passages.

**Follow-up:** What would you do for an agent that runs for hours?

### Your agent gets worse as a conversation goes on. How do you debug it?

**Strong answer:** I'd log the exact context on the failing calls and read it, since that's what the model saw. I'd look for stale tool results, conflicting information, or instructions lost among noise. Then I'd try clearing old results or summarising, and measure with long test conversations, because short tests won't show this.

**Follow-up:** What are the risks of summarising?

### A customer's chat runs for hours. What do you keep in context?

**Strong answer:** The system prompt, the recent turns, and facts the task depends on, like the order being discussed. Older turns can become a summary. I wouldn't store things the model doesn't need, such as personal details. And I'd keep the full history in the database, so nothing is lost even when it leaves the context.

**Follow-up:** How would you test that the summary kept what matters?

## Check yourself

### What's context rot?

- [x] Recall getting worse as the context grows — right: so more isn't always better.
- [ ] Old messages being deleted — that's something you might choose to do.
- [ ] A model's training data going out of date — that's the knowledge cutoff.

### Why doesn't ShopHelper put all its policies in the prompt?

- [ ] They wouldn't fit — all 9 are only about 1,300 tokens.
- [x] Most would be irrelevant to each question — right: searching costs less and distracts less.
- [ ] It's not allowed — it would work, but wastefully.

### What's the first step when an agent gives a strange answer?

- [ ] Rewrite the prompt — you don't know the cause yet.
- [ ] Switch to a bigger model — that may hide the real problem.
- [x] Read exactly what the model received — right: that's what it had to work with.
