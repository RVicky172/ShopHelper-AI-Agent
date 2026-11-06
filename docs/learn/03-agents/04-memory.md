---
title: Memory
checked: 2026-11-06
---

## What you'll learn

- Why "memory" is really a storage question
- The difference between short-term and long-term memory
- What a checkpoint is
- Why this project stores conversations twice

## The simple explanation

Every model call starts blank. A chatbot only seems to remember because the app resends the conversation each time. So "memory" isn't in the model. It's a storage question: what do you save, and how do you give it back?

There are two kinds:

| Kind | Lasts | Holds | Example |
| --- | --- | --- | --- |
| **Short-term** | One conversation | The messages so far | "that order" means the one just mentioned |
| **Long-term** | Across conversations | Facts worth keeping | "this customer prefers email" |

Think of a doctor. The notes during today's appointment are short-term. The patient's file is long-term. The doctor doesn't reread every old appointment, only what's relevant.

Memory also has a cost. All of it goes in the context, so more memory means more tokens. And stored personal data has to be protected.

## An example

Here's what memory does in a conversation:

```text
Customer: Where is order 1001?
Agent:    It was delivered on 1 November.
Customer: Can I return it?
```

"It" means order 1001 only because the first two messages are sent again with the third. The model didn't remember. The app replayed the conversation.

Now suppose the server restarts between those messages. If the conversation was only in memory, it's gone, and "it" means nothing. So real agents save state outside the process.

## How ShopHelper does it

This project keeps two kinds of record, for two different readers:

| | `chat_history` | `checkpoints*` |
| --- | --- | --- |
| Reader | People: support staff, the UI | The agent |
| Contains | Readable messages only | Everything: tool calls, results, paused work |
| Written by | `service.py` | LangGraph, automatically |
| Privacy | Stores masked text | Stores masked input and tool data |
| Purpose | Display and audit | Resuming work |

They look redundant, but they aren't. Think of a conversation transcript next to a save file in a video game.

A **checkpointer** saves the full state after every step, keyed by a `thread_id`. Here that's the session id:

```python file=src/shophelper/agent/service.py
"configurable": {"thread_id": session_id, "user_id": user_id},
```

The next message on that session loads the saved state and carries on. Since it's in Postgres, it survives restarts. A paused refund would still be waiting after a reboot.

The checkpointer is chosen by settings: Postgres locally, DynamoDB on AWS, and in-memory for tests. The graph doesn't know which it's using.

**Not in ShopHelper:** long-term memory. A customer's next conversation starts fresh, and nothing is remembered across conversations. For a support agent that's a reasonable choice, because orders can always be looked up, and storing less is safer.

## In the market

Checked on 2026-11-06.

| Option | What it gives you |
| --- | --- |
| [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) | Short-term thread state through checkpoints, and longer-term memory across sessions |
| [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) | Sessions, a memory layer for an agent's working context |
| [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview) | Sessions you can resume or fork |
| [Claude's memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) | Files you control, across conversations |
| Your own tables | Full control, which is what this project uses for history |

Long-term memory adds real questions. What's worth keeping? How do you correct something wrong? How long is it kept, and can a customer delete it? Stored memory is also a target. OWASP's [AI agent security cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html) lists **memory poisoning**: malicious data stored to influence later sessions or other users. It advises checking content before storing it, keeping memory separate per user, and setting limits and expiry.

## Try it

1. Sign in, open the chat, and ask "Where is order 1001?".
2. Then ask "When was it delivered?". The agent knows what "it" means.
3. Run `docker compose restart api`, and ask "What was it again?". It still knows, because the state was in Postgres.
4. In pgAdmin, compare `chat_history` with `checkpoints` for one session. You'll see many more checkpoints than messages, one for each step.

## Interview questions

### How do you give an agent memory?

**Strong answer:** The model is stateless, so memory is storage. Short-term memory is the conversation, resent each call. I save it in a checkpointer keyed by thread, so it survives restarts. Long-term memory is facts kept across conversations, retrieved when relevant. I'd only add that if it's worth the privacy and accuracy risk. In my project a customer's orders can always be looked up, so I don't keep long-term memory.

**Follow-up:** How do you stop memory growing forever?

### Why store conversations twice?

**Strong answer:** They serve different readers. The history table has clean, masked messages for people. Checkpoints hold the agent's full state, including tool calls and paused work, so it can resume. Mixing them would make the UI parse internal state, and it would tie the audit trail to the framework's format.

**Follow-up:** What's a downside of keeping two copies?

## Check yourself

### Why can the agent understand "it" in a follow-up question?

- [ ] The model remembers the last message — models keep nothing between calls.
- [x] The app sends the earlier messages again — right: memory is really storage.
- [ ] It guesses — it sees the earlier messages.

### What does a checkpoint hold that the chat history doesn't?

- [x] Tool calls, results and paused work — right: everything needed to resume.
- [ ] Nothing: they're the same — the history has readable messages only.
- [ ] The model's parameters — those never change.

### Why might you skip long-term memory?

- [ ] It's impossible to build — it isn't.
- [x] It adds privacy and accuracy risks you may not need — right: store less when you can look it up.
- [ ] Models can't read it — they can, if you send it.
