# 030 — Care Questions Always Search the Policy · Implementation Plan

**Spec:** `./spec.md` · **Status:** Approved

## Approach

### §1 Code searches first, instead of sending the model back

The spec assumes the refund check's shape: let the model answer, spot the problem, send it back. Here that has a real cost. `agent()`
streams tokens as the model writes, so a discarded answer would already be on the customer's screen (AC-6), each protected question would
pay for an extra model call, and the model could refuse a second time.

So code makes the decision before the model runs. When a turn's message is a protected question and this turn has no `search_policy` call,
`agent()` skips the model and returns a tool call that code wrote, using the customer's message as the query. The graph then runs as
usual: `route` sends it to `tools`, the passages come back, and the model answers from them.

- No answer is drafted before the search, so there's nothing to discard (AC-6).
- It adds no model call, so AC-8 holds at 0 rather than 1.
- It can't depend on the model cooperating, which is what failed in D-016.

**This changed the approved spec.** AC-5, AC-6 and AC-8 mentioned sending the model back. The owner approved the new wording (D-018).

### §2 When the search itself fails

The model can't refuse any more, but the search can fail, for example with the MCP server down. `run_tool` then returns an error
`ToolMessage`, and the model would answer with no passages, which is the original bug. So on a protected turn whose search failed, `agent()`
returns the fixed reply from Q3 without calling the model.

### §3 Matching a protected question

One compiled pattern, in the style of `REFUND_PROMISE`, for the Q1 terms, with word boundaries and any letter case. It reads only the last
`HumanMessage`, which is already masked by the input guardrail. Each turn stands alone, using the same slice as
`_promises_unrequested_refund`, so a repeated question searches again (AC-4). The nudge in the refund check is never stored, so it can't
match.

### §4 Refunds that mention a warranty

"It's under warranty, please refund order 1001" searches first, then reaches the model as usual, which still looks up the order and calls
`request_refund`. AC-9 measures this. A human still approves every refund, and the search is read-only.

### §5 Saved measurement script

The refund script for AC-40 was never committed, so it had to be rebuilt. `evals/measure_policy.py` keeps the 3 measurements in the repo:
Care questions, refunds and starters. It isn't a test, so pytest doesn't collect it.

### §6 The Care line carries its own definition (added 2026-11-06, D-019)

The spike showed the search alone isn't enough: the Care chunk arrives without the chunk defining electronics. `warranty.md`'s Care line now
names the categories. No terms changed.

## Spec Changes (applied 2026-11-06)

- **AC-5:** "If the policy search fails, the customer gets a fixed, honest reply that points them to support, and the model isn't asked to
  answer." _(unit)_
- **AC-6:** "On a protected question, no answer is written before the search, so the chat never shows one that's later withdrawn."
  _(unit + e2e)_
- **AC-8:** "A protected question costs no extra model call." _(unit)_
- **Non-functional requirements:** "A protected one adds at most one model call" becomes "adds no model call".

## Files

| File | Change | Purpose |
| ---- | ------ | ------- |
| `src/shophelper/graph.py` | modify | Pattern, `_needs_policy_search`, `_search_failed`, the two branches at the top of `agent()` |
| `knowledge/policies/warranty.md` | modify | §6, re-embedded by `setup` |
| `tests/test_graph.py`, `tests/fakes.py` | modify | AC-4 to AC-8, using `ScriptedChatModel`, which now counts its calls |
| `tests/test_mcp.py` | modify | "How long is the warranty?" now searches through code, so its script drops the model's search call |
| `evals/golden_cases.yaml` | modify | The 4 wordings that failed, making 37 cases |
| `evals/measure_policy.py` | new | §5 |
| `docs/learn/01-agents-and-the-loop.md` | modify | AC-12, beside the refund check, with a Try it step |
| `docs/learn/06-streaming.md` | modify | One note: a `model_step` can come from code, with 0 tokens |
| `specs/architecture.md`, `specs/testing-strategy.md`, README, `docs/` | modify | New rule, case count 33 to 37 |
| `memory/decisions.md`, 021 `spec.md`, `specs/roadmap.md` | modify | AC-13 |

No change to `service.py`, `mcp_server.py`, the web app, the prompt or the database.

## Data Structures & Interfaces

```python
POLICY_TOPIC = re.compile(
    r"\b(shophelper care|warrant(y|ies)|extended coverage|protection plan)\b", re.IGNORECASE
)
NO_POLICY_ANSWER = "I couldn't check our policy just now, so I don't want to guess. Please ask again, or contact support."

def _current_turn(messages) -> tuple[HumanMessage | None, list[AnyMessage]]: ...  # shared with the refund check
def _needs_policy_search(messages) -> bool: ...  # protected, and no search_policy call this turn
def _search_failed(messages) -> bool: ...        # protected, and this turn's search returned an error

async def agent(state):
    if _needs_policy_search(state["messages"]):
        return {"messages": [AIMessage("", tool_calls=[search_call(question)])]}  # unique id per call
    if _search_failed(state["messages"]):
        return {"messages": [AIMessage(NO_POLICY_ANSWER)]}
    ...  # unchanged
```

## Techniques

- A deterministic step in front of the model: the same idea as Constitution V, applied to a read, not a write.
- The stream keeps its shape. The code's step produces `model_step`, `tool_start` and `tool_end` with no new event, and `model_step` reports
  0 tokens, which is true.
- `_summarise` needs nothing new: `tools_used` and citations come from the messages as before.

## Test Approach

| AC | Test | Type |
| -- | ---- | ---- |
| AC-1, AC-2, AC-3 | `evals/measure_policy.py care`: 16 wordings, 3 interleaved rounds, answers read in full | measurement |
| AC-4 | `tests/test_graph.py`: the same question twice in one session gives 2 searches | unit |
| AC-5 | `tests/test_graph.py`: a failing search tool gives the fixed reply, and the model isn't called | unit |
| AC-6 | `tests/test_graph.py`: stream order has no `token` before `tool_end`; one browser check in the chat widget | unit + e2e |
| AC-7 | `tests/test_graph.py`: 10 near misses, parametrized, with no forced search | unit |
| AC-8 | `tests/test_graph.py`: counts model calls on a protected question | unit |
| AC-9 | `evals/measure_policy.py refunds`: 60 attempts, 12 mentioning a warranty, confirmed in the database | measurement |
| AC-10 | `evals/measure_policy.py starters`: 57 questions | measurement |
| AC-11 | `scripts/evals_local.sh`, then again with the check removed | e2e + sabotage |
| AC-12, AC-13 | Try it step run; docs and memory read through | manual |

## Risks & Mitigations

- **Search runs, but the answer is still poor.** The fix guarantees the passages, not how the model uses them. "How much is Care for a laptop
  stand?" also needs it to treat a stand as electronics. **Spike first:** patch the check in, then run the 8 D-016 wordings before building
  the rest. If answers stay poor, stop and report.
- **The raw message is a weak search query.** A long message may retrieve the wrong passages. The spike checks that `warranty.md` comes back.
- **Claude on AWS is untested.** An `AIMessage` with empty content and a code-written tool call should convert for Bedrock, but only Phase 1
  can prove it. A unit test can't. Recorded as a known limit.
- **The trace shows a "model step" the model didn't take.** Accurate at 0 tokens, but it could confuse a learner, so the docs explain it.
- **New wordings could be tuned to the fix.** AC-2's wordings are written in the first task, before the code.

## Constitution Check

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Spec before code | ✅ | Spec updated first: AC-5, AC-6 and AC-8 (D-018) |
| II. Test-gated delivery | ✅ | Unit tests written first, sabotage for AC-11 |
| III. Small dependencies | ✅ | None added |
| IV. Memory maintained | ✅ | Decision recorded, D-016 updated |
| V. The model asks, code acts | ✅ | Code adds a read-only search. No state-changing tool moves, and refunds are untouched |
| VI. AWS stays the default | ✅ | No setting. Runs everywhere, as agreed in Q2 |
| VII. Local first | ✅ | Works with Docker and LM Studio only |
| VIII. Built to learn | ✅ | Chapter 1 gains the real numbers and a Try it step |
| IX. Stream changes additive | ✅ | No new or changed events |
