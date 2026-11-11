---
title: Debugging scenarios
checked: 2026-11-07
---

## What you'll learn

- A method for debugging an AI system without guessing
- Five scenarios an interviewer might give you, with full answers
- Why "change the prompt" is usually the wrong first move
- How to tell these as stories from your own work

## The simple explanation

In a debugging round you get a symptom, such as "customers say the bot gave a wrong answer", and you're asked what you'd do. The interviewer isn't waiting for the right cause. They're watching how you search for it.

Think of a doctor. A poor one hears "headache" and prescribes pills straight away. A good one asks when it started, what changed, and runs a test that rules things out. Debugging AI is the same. The pills here are "tweak the prompt" or "use a bigger model". They might help, and you'd never know why.

An AI system is a chain: the input, retrieval, the prompt, the model, tools, then the output. A wrong answer can start at any link. So the skill is **splitting the chain, and testing each part**. One prep guide puts it well: a strong answer should ["split the pipeline before changing prompts"](https://prachub.com/resources/ai-engineer-interview-questions-2026-rag-agents-evals-and-production-systems).

## An example

Use the same six steps every time:

| Step | What to say |
| --- | --- |
| **Symptom** | Restate it. Who's affected, how often, since when? |
| **Ask first** | What changed? Can I reproduce it? Can I see the trace? |
| **Narrow it down** | Check each link in the chain, cheapest first |
| **Cause** | Name it, and say what evidence proves it |
| **Fix** | The smallest change at the real cause |
| **Prevent** | A test, so it can't quietly come back |

Saying these steps aloud is half the answer. Many candidates stop at the fix. The last step shows you've run real systems.

Scenarios 1 to 3 are real, from this project. Scenarios 4 and 5 are practice cases, built on real measurements and real checks. Being able to say "this happened to me" is worth a lot, so learn the real ones as stories.

## Scenario 1: The right document exists, but the answer is wrong

*Real, from this project. Full version in [debugging a wrong answer](../05-rag/08-debugging-a-wrong-answer.md).*

**Symptom:** Asked "How much is ShopHelper Care for a laptop stand?", the agent said Care wasn't available, because a stand "is not an electronic product". The policy says otherwise.

**Ask first:** Does the policy really say so? Is the stored copy current? Does it happen for one wording or many?

**Narrow it down:** Walk the chain. The document was right, the chunks were current, and the search query was sensible. The Care rule even came back first. So retrieval looked fine. The last check was to read the passages exactly as the model received them.

**Cause:** The chunk said "electronics only", and the chunk *defining* electronics wasn't retrieved. The model had a rule with an undefined word, and it guessed. The evidence is in the passages themselves.

**Fix:** Make the rule stand alone: the Care line now names the categories. All 16 test wordings were then right. A bigger model or more prompt rules would have cost more, and missed the cause.

**Prevent:** Test several wordings, not one. When writing documents for RAG, remember each chunk is read alone, so a line that depends on a definition should carry it.

## Scenario 2: The agent says it's done, and nothing happened

*Real, from this project.*

**Symptom:** A customer asks for a refund. The agent replies "I'll process that refund", and no refund request exists. The customer waits for something that will never come.

**Ask first:** Does the trace show a tool call? Is it every refund, or some wordings? Did the tool fail, or was it never called?

**Narrow it down:** Compare what the agent said with what it did. The trace showed no `request_refund` call, so the tool didn't fail. The model wrote a promise instead of acting. Measuring wordings separately showed it was concentrated: one wording scored 0 of 20.

**Cause:** Models sometimes describe an action instead of taking it. Text and tool calls are separate outputs, and nothing tied them together.

**Fix:** A prompt rule only reduced it, so the check went into code. A pattern spots a refund promise with no matching tool call:

```python file=src/shophelper/agent/graph.py
REFUND_PROMISE = re.compile(
```

The agent then gets one nudge to act. If it still doesn't, code replaces the reply with an honest one. That reached 60 of 60 on the tested wordings.

**Prevent:** Eval cases that check the *action*, not the wording. In general, anything a customer relies on needs a check in code.

## Scenario 3: All the evals pass, and the bug is still there

*Real, from this project.*

**Symptom:** An eval run passes, you run it several times to be sure, and it keeps passing. But the failure still appears elsewhere.

**Ask first:** What's different between the test and the real thing? Are the samples really independent of each other?

**Narrow it down:** Look at how the test runs, not at the agent. One refund wording scored 20 of 20 when repeated, and 0 of 20 when mixed with other questions. Same prompt, same model: only the order changed.

**Cause:** LM Studio's prompt cache. Repeated prompts repeated their result, so 20 runs were really one sample, seen 20 times.

**Fix:** Put other questions between samples, then measure again. That exposed the real failure rate.

**Prevent:** Distrust perfect scores from repeats. Vary the wording, mix the order, and check that a test can fail by breaking the code on purpose. Learn this one well: "my test was lying" is a far more memorable story than "my test caught a bug".

## Scenario 4: The chat gets slower as the conversation goes on

*A practice scenario, using real measurements from this project.*

**Symptom:** The first reply feels quick. By the twentieth message, people wait several seconds before any word appears.

**Ask first:** Is it the wait for the first word, or the whole reply? Is it only long conversations? Did anything deploy?

**Narrow it down:** Split the time. Compare time to first token with total time, and plot latency against input tokens. Then count model calls per turn. Measured on the local model:

| Prompt size | First token | Output speed |
| --- | --- | --- |
| 48 tokens | 0.60 s | 63 tokens a second |
| 1,314 tokens | 1.42 s | 39 tokens a second |
| 3,852 tokens | 3.99 s | 26 tokens a second |

Don't stop at the first pattern, though. The three slowest turns in our logs took around 10 seconds, with under 1,800 input tokens each, and all three used `search_policy`. A tool turn means two model calls. So there can be two causes at once.

**Cause:** Every turn re-sends the whole conversation, so the prompt keeps growing, and [reading it takes time](../01-how-llms-work/05-generating-a-reply.md). Each extra model call pays that again.

**Fix:** Trim or summarise old messages. Keep the fixed part of the prompt first, so prompt caching can help on a hosted model. Stream, so the wait is less painful. ShopHelper doesn't trim history yet, so say that if you use this.

**Prevent:** Track [p95 latency](../10-running-in-production/02-the-metrics-that-matter.md) and input tokens per turn, with an alert on both. A slow rise is easy to miss without a graph.

## Scenario 5: A customer sees someone else's data

*Real checks from this project, told as a practice scenario. No real customer was involved.*

**Symptom:** Someone reports seeing another person's order. Treat it as an incident first: stop the harm, then investigate.

**Ask first:** Is it still happening? Did it come from the agent, the API, or the browser? Whose data, and how much? Who needs to be told?

**Narrow it down:** There are three likely places. **The agent:** did a tool use an identity from the model's text? **The server:** does the query filter by owner? **The browser:** after a sign-out on a shared computer, did old data stay on screen? Reproduce with two test accounts.

**Cause:** Here are the three real versions this project defends against. Identity can get lost on its way to a tool: inside a LangGraph node, the MCP interceptor's `request.runtime` is `None`, so identity travels in a `ContextVar`. A tool can take a customer's identity from the message, when it should use the session. And the browser can keep the previous user's cached data.

**Fix:** Identity comes from the session and [never from the model](../06-building-the-app/07-authorization-and-isolation.md). Each query filters by owner. The browser clears its cache on sign-in and sign-out:

```typescript file=web/src/features/auth/useAuth.ts
queryClient.clear()
```

It also rebuilds the signed-in part of the page for each user:

```tsx file=web/src/App.tsx
<ChatProvider key={user?.id ?? 'guest'} user={user}>
```

**Prevent:** Attack evals: 7 of this project's 37 cases try to reach another customer's data. Add a positive control too: check that each user still sees their *own* data. Without it, a server that treats everyone as the same user also shows "no leaks".

## How ShopHelper does it

These are the tools that made those answers possible. In an interview, describing them shows you've debugged a real system:

| To see | Use |
| --- | --- |
| What the agent did, step by step | The trace on **How it works** |
| What the model really received | The `search_policy` step in the trace |
| What's stored | **What's stored**, and the RAG explorer |
| Cost and latency per turn | The `chat_completed` log line |
| Whether it's fixed | `scripts/evals_local.sh -k <cases>` |

There are gaps too, and you should name them. The logs don't record which prompt or model version gave an answer, and LangSmith tracing isn't running locally. So an old answer can't be fully replayed.

## Try it

1. Scenario 1: sign in, open **How it works**, and ask "How long is the warranty on a laptop stand?". Open the `search_policy` step, and find the fact in the passages.
2. Scenario 4: list your slowest turns, with their input tokens:

   ```bash
   docker compose logs api --no-log-prefix | grep chat_completed | sed -E 's/.*"tools": (\[[^]]*\]), "input_tokens": ([0-9]+).*"latency_ms": ([0-9]+).*/\3 ms, \2 tokens, \1/' | sort -n | tail -5
   ```

   Is the slowest turn the one with the most tokens? What do the slow ones have in common?
3. Scenario 2: find the code check with `grep -n '_promises_unrequested_refund' src/shophelper/agent/graph.py`, and read what happens on each path.
4. Ask a friend to read you a symptom, or pick one yourself. Answer aloud with all six steps, in under five minutes.
5. Write one debugging story of your own: what you saw, what you ruled out, the cause, and what stops it coming back.

## Interview questions

### The right document exists, but the bot gives a wrong answer. What do you do?

**Strong answer:** I wouldn't touch the prompt yet. I'd reproduce it and split the chain: is the document current, did it chunk well, was the query sensible, did the passage come back, and what did the model really receive? On my project everything looked fine until I read the passages. The rule came back, but the definition of a word in it sat in another chunk, so the model guessed. The fix was to make the line stand alone, then test 16 wordings.

**Follow-up:** How would you find this if you had no trace?

### Quality dropped overnight, and nobody changed the code. Where do you look?

**Strong answer:** Something changed even if the code didn't. I'd check the model version, provider notices, prompt or config changes, document updates and the kinds of questions coming in. Then I'd run my evals against the current setup, and compare with a past run. If evals pass while users complain, the eval set has a gap, so I'd add real failing conversations to it. I'd log model and prompt versions, because without them this takes much longer.

**Follow-up:** What if the provider updated the model silently?

### Tell me about a bug that was hard to find.

**Strong answer:** My evals said a refund flow was fine: 20 of 20, repeated. It wasn't. The local model's prompt cache was repeating its own answer, so I'd measured one sample 20 times. When I mixed other questions in between, the same wording scored 0 of 20. The agent was promising refunds without calling the tool. I fixed it with a check in code, and it reached 60 of 60. Now I distrust perfect repeats, and I break code on purpose to prove a test can fail.

**Follow-up:** How do you decide how many samples are enough?

## Check yourself

### A customer got a wrong answer. What's the best first move?

- [ ] Add a rule to the prompt — you don't yet know the cause.
- [ ] Switch to a bigger model — costly, and it may not help.
- [x] Reproduce it, and check each link in the chain — right: split it before changing anything.

### The agent said it refunded, and no refund exists. What do you check first?

- [x] The trace, for whether a tool call happened — right: that separates "failed" from "never called".
- [ ] The tone of its message — the words aren't the problem.
- [ ] The refund policy document — that's not where this breaks.

### A test passes 20 of 20 on one repeated prompt. Why might that mean little?

- [ ] Twenty is too many — it isn't.
- [x] The runs may not be independent — right: a cache can make them one sample.
- [ ] Models never repeat themselves — they can, especially with a cache.
