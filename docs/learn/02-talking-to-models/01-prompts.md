---
title: Writing good prompts
checked: 2026-11-06
---

## What you'll learn

- What a system prompt is, and how it differs from a user message
- The habits that make prompts work
- Why every rule should come from a real failure
- What a prompt can't do

## The simple explanation

A **prompt** is what you send the model. A chat has two main parts:

| Part | Who writes it | What it's for |
| --- | --- | --- |
| **System prompt** | You, the developer | Standing instructions, sent on every call |
| **User message** | The customer | What they want right now |

Think of a new employee on their first day. The system prompt is their induction. They're clever, but they know nothing about your shop. Anthropic's guide uses the same picture: a brilliant new employee who lacks context on your norms. It also gives a good test: show your prompt to a colleague with no background. If they'd be confused, the model will be too.

The habits that work:

- **Be clear and direct.** Say exactly what you want, including what "good" looks like.
- **Give the reason.** "Don't ask for a card number, because support never needs it" works better than a bare rule, because the model can apply the idea to new cases.
- **Show examples.** A few examples are among the most reliable ways to set format and tone.
- **Give it structure.** Separate instructions from data with clear labels or tags, especially when pasting in documents.
- **Say what to do, not only what to avoid.** It's easier to follow.

There's no magic wording. Prompting is mostly clear writing, then testing.

## An example

Here's a weak system prompt:

```text
You are a helpful assistant. Help customers with their orders.
```

It leaves everything open. Should it look up orders or guess? What if it doesn't know?

A better one says what to do in each case:

```text
You are a support assistant for an online store.
- When a message names an order number, call get_order_status before replying.
  Its status may have changed, so never answer from memory.
- If the policy passages don't answer the question, say you don't know.
```

Same model, very different behaviour. Note the second line: it gives a reason.

## How ShopHelper does it

Here are some real rules from the system prompt:

```python file=src/shophelper/agent/graph.py
- Never ask for card numbers, CVV, passwords or OTPs.
- Politely decline requests unrelated to the store, its orders or its policies.
```

Nearly every rule exists because something went wrong. Here's how one grew:

1. The model wrote "I'll process the refund", and stopped without doing anything.
2. So this rule was added:

```python file=src/shophelper/agent/graph.py
- Never say you will do something: if an action is needed, call the tool now, in this reply.
```

3. It worked, until one wording failed every time. So a check in code was added too. See [The agent loop](../03-agents/02-the-agent-loop.md).

That's the normal cycle: watch it fail, add a rule, test across different wordings, and if it must always hold, move it into code.

**Prompts need testing like code.** A change that fixes one case can break another. So in this project any prompt change runs the evals, and a refund test must still pass. See [Evals](../07-evals-and-testing/01-why-testing-ai-differs.md).

A prompt is also not a security boundary. Customers can type anything, including "ignore your instructions". [Security](../08-security/04-guardrails.md) covers why you can't rely on a prompt to stop that.

## In the market

Checked on 2026-11-06.

Each provider publishes a guide, and it's worth reading the one for your model, because they differ in the details. Anthropic's [prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) is a good one to start with.

As models improve, heavy prompt tricks matter less. Plain, specific instructions tend to carry across models, while tricks tuned to one model often don't. So when a model changes, re-run your tests rather than assuming your prompt still works.

## Try it

1. Sign in, and open the chat.
2. Ask "What's the capital of France?". The prompt's last rule should make it decline.
3. Ask "Can I give you my card number?". Compare the answer with the card rule above.

## Interview questions

### How do you write and improve a system prompt?

**Strong answer:** I start small, with clear and specific instructions, and give reasons where it helps. Then I test on real examples and add rules only for failures I've actually seen, so every line earns its place. I treat prompts like code: versioned and tested, because a fix for one case can break another. If a rule must always hold, I enforce it in code instead.

**Follow-up:** How do you know a prompt change didn't break something?

### Your system prompt has grown to 200 lines and results are getting worse. What do you do?

**Strong answer:** I'd measure before cutting. Long prompts add cost and delay, and rules can conflict. I'd remove rules one group at a time and run my evals, to see which ones still matter. Some might move to code, or to retrieved context so they appear only when relevant. A newer model may also not need some of them.

**Follow-up:** How would you handle rules that only apply to some requests?

## Check yourself

### What's the difference between a system prompt and a user message?

- [x] The developer writes the system prompt, and it's sent every time — right: it's the standing instructions.
- [ ] The system prompt is hidden from the model — the model reads it.
- [ ] A user message can't change behaviour — it can, which is why injection is a risk.

### Where should most rules in a system prompt come from?

- [x] Failures you've actually seen — right: every rule should earn its place.
- [ ] A long list of everything that might go wrong — that adds cost and conflicts.
- [ ] Copying other companies' prompts — their failures aren't yours.

### What can't a prompt give you?

- [ ] Better formatting — it can.
- [ ] A consistent tone — it can.
- [x] A guarantee — right: for that you need code.
