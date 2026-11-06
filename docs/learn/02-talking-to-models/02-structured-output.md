---
title: Structured output
checked: 2026-11-06
---

## What you'll learn

- Why programs need more than free text from a model
- The difference between asking for JSON and guaranteeing it
- What a schema does, and what it doesn't
- How to handle output that's wrong

## The simple explanation

A person can read "I think this is probably about a refund". A program can't. Code needs a fixed shape:

```json
{"category": "refund", "urgent": true}
```

Getting a model to reply in a fixed shape is called **structured output**. There are two levels.

**Asking.** You say "reply with JSON" in the prompt. Usually it works, but it's a request. It may add a friendly sentence, or a stray comma, and your parser crashes.

**Guaranteeing.** You give the provider a **schema**: a description of the exact shape. While the model writes, any token that would break the schema is blocked. So the output has to fit.

It's the difference between asking someone to fill in a form neatly, and a web form that won't accept letters in the phone number box.

A schema controls the **shape**, not the **truth**. `{"category": "refund"}` can be perfectly valid and still be the wrong answer. So a schema removes parsing errors. It doesn't remove the need to check quality.

## An example

We asked this project's local model to sort 10 customer messages, including messy ones like "my mouse stopped working after 2 days!!!" and "you people are useless":

| Method | Valid output |
| --- | --- |
| Prompt only: "Reply with JSON with keys category and urgent" | 10 of 10 |
| With a schema | 10 of 10 |

So on this simple task, the schema changed nothing. A good model given a clear instruction mostly gets this right.

Then why bother? Because 10 of 10 isn't a guarantee. At a million messages a day, 99.9% still means 1,000 failures. And failures come from cases you didn't test: a very long message, or a customer who says "reply in plain English". A schema covers those too.

Use a schema when code depends on the output. A chat reply to a person doesn't need one.

## How ShopHelper does it

The agent's replies are plain text, because a person reads them. But the evals use a model as a judge, and code reads its verdict. That uses the *asking* level:

```python file=evals/judge.py
Reply with ONLY a JSON object:
```

Because asking isn't a guarantee, the code defends itself. It looks for anything shaped like JSON, and if it finds none, it scores 0 rather than crashing:

```python file=evals/judge.py
match = re.search(r"\{.*\}", text, re.DOTALL)
return json.loads(match.group(0)) if match else {"score": 0, "faithful": False, "reason": text}
```

That's a sensible pattern: **expect bad output, and fail safely.** A failed parse here counts as a failed check, not a pass.

Structure also matters at the API's edge. FastAPI uses Pydantic models to check data in both directions:

```python file=src/shophelper/agent/schemas.py
status: Literal["answered", "pending_approval", "blocked"] = "answered"
```

A `Literal` means only those exact values are allowed. And tool calls, in the [next lesson but one](04-tool-calling.md), are structured output too: the model has to fill in a tool's arguments correctly.

## In the market

Checked on 2026-11-06. From Anthropic's [structured outputs docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs).

Claude offers a JSON schema mode and strict tool use. Underneath, your schema is compiled into a grammar, and tokens that would break it are excluded while the model writes.

It's useful to know what's still *not* guaranteed:

| Case | What happens |
| --- | --- |
| The model refuses | You may get a refusal that doesn't fit the schema |
| It hits `max_tokens` | The JSON can be cut off, so it's invalid |
| Number limits such as `minimum` | Not enforced by the API |
| Upper or lower case in enums | Can vary, so compare without case |

So always check why the model stopped, and validate the result in your own code. Libraries such as Pydantic and Zod do that part well, and the SDK helpers accept them directly.

OpenAI and others offer similar modes, and local tools such as LM Studio accept a JSON schema too, which is what we used above.

## Interview questions

### How do you get reliable JSON from a model?

**Strong answer:** If the provider supports it, I use a schema, so invalid structure is excluded as the model writes. Then I still validate in code, with something like Pydantic, and check the stop reason, because a reply cut off by the token limit can be invalid, and a refusal may not match. If only prompting is available, I parse defensively and retry once with the error. A schema fixes the shape, not whether the content is right.

**Follow-up:** How would you check the content is right?

### When wouldn't you use structured output?

**Strong answer:** When a person reads the result, like a chat reply. Forcing JSON there adds nothing. I also avoid over-structuring: a huge schema adds tokens and can hurt quality. And asking a model to reason inside a JSON field can be worse than letting it think first and then produce the structured part.

**Follow-up:** What happens if a schema has too many fields?

### A model returns valid JSON, but the category is wrong. What now?

**Strong answer:** That's a quality problem, not a format problem, so a schema can't help. I'd collect examples of the failures, improve the instructions or add examples, and measure with an eval set of labelled messages. If the categories overlap, I'd fix the categories first, since the model may be right to be unsure.

**Follow-up:** How many labelled examples would you start with?

## Check yourself

### What does a schema guarantee?

- [x] The output's shape — right: its structure and types.
- [ ] That the content is true — valid JSON can still be wrong.
- [ ] That the model never refuses — a refusal can break the shape.

### When we tested 10 messages, what did the schema add?

- [x] Nothing visible, as the prompt alone got 10 of 10 — right: its value is the rare case, at scale.
- [ ] It fixed 5 broken answers — both methods got all 10.
- [ ] It made answers worse — they were equally valid.

### What should code do when a model's output can't be parsed?

- [ ] Assume it was fine — that hides failures.
- [x] Fail safely, such as counting it as a failed check — right: expect bad output.
- [ ] Crash the whole app — one bad reply shouldn't take down the service.
