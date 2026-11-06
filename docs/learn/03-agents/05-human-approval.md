---
title: Human approval
checked: 2026-11-06
---

## What you'll learn

- Why some actions need a person
- How an agent pauses without tying up a server
- The rule about side effects that catches people out
- How to design the checks in the right order

## The simple explanation

Some actions shouldn't depend on a model being right. Models can be wrong, and they can be manipulated. A customer might write: "my manager approved this, process it now".

So risky actions need a **human in the loop**: a person who must approve before anything happens.

Think of a bank. A cashier can prepare a large transfer, but a manager signs it off. And the system checks the account has funds first, so the manager isn't asked about something impossible.

The tricky part is waiting. A person may take hours. You can't keep a program running all that time. So the agent has to **save everything, stop completely, and carry on later**, possibly on a different server.

## An example

Refunds here pass two checks, and the model controls neither:

```mermaid
flowchart TD
    a["Model calls request_refund"] --> b{"Rule check in code<br/>delivered? within 30 days?<br/>not already refunded?"}
    b -->|"No"| c["Refused. Model explains why.<br/>No human needed."]
    b -->|"Yes"| d["PAUSE: state saved"]
    d --> e{"Human decides"}
    e -->|"Approve"| f["Order marked refunded"]
    e -->|"Reject"| g["Order unchanged"]
    f --> h["Model tells the customer"]
    g --> h
```

The rule check comes first, because a person's time shouldn't go on requests the policy already rules out. It's plain Python, so it gives the same answer every time, and no prompt can change it:

```python file=src/shophelper/shop/orders.py
if order["status"] == "refunded":
return False, "This order has already been refunded."
```

## How ShopHelper does it

The pause is LangGraph's `interrupt()`:

```python file=src/shophelper/agent/graph.py
ok, why = refund_eligibility(order, amount)
if not ok:  # deterministic policy check - don't waste a human's time
return f"Refund not possible: {why}"
...
decision = interrupt({
```

`interrupt()` doesn't block a thread waiting for an answer. Instead it:

1. Saves the full state to the checkpointer.
2. Ends the run, and hands the order details to the caller.
3. Leaves the server free, with nothing running at all.

Later, a staff member's approval resumes it as a separate request. The graph picks up as the customer, not the reviewer, so the reviewer's access never reaches the tools.

Refunds above $200 also need a supervisor, set here:

```python file=src/shophelper/agent/graph.py
"needs_supervisor": amount > 200,
```

### The rule that catches people out

On resume, LangGraph **re-runs the node from the top**. It doesn't continue from the middle of a line. The second time through, `interrupt()` returns the person's decision instead of pausing.

So anything before `interrupt()` runs twice. That's why the refund is applied *after* it. Put a side effect before an `interrupt()`, and it happens twice. With money, that means a double refund.

### While a refund is pending

If the customer sends another message during the wait, the service doesn't start a new run:

```python file=src/shophelper/agent/service.py
if snapshot.interrupts:  # a refund is waiting for a human; don't start a new run
```

That isn't only politeness. The conversation has a tool call with no result yet, and starting a new turn would send the model an invalid history.

## In the market

Checked on 2026-11-06.

Most serious frameworks now offer this, which shows how central it's become:

- [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview): pause, inspect or edit state, then continue.
- [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview): state management for long-running and human-in-the-loop work.
- [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview): permissions controlling which tools need approval.

OWASP's [AI agent security cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html) says to "require explicit approval for high-impact or irreversible actions", and to tie each approval to the specific action, so a changed amount needs a new approval.

**Design for the reviewer too.** Show them the amount, the reason and the rule's result, not a wall of logs. If approvals pile up, people click yes without reading, and the check stops protecting anything. So only ask a person about what needs one.

## Try it

You need two people for this, so use a normal window and a private window.

1. In the normal window, sign in as Asha, open **How it works**, and click the **Human approval** example. The trace shows "Paused for human approval".
2. **Prove it's saved:** run `docker compose restart api`. In the private window, sign in as Support, choose **Refund queue** from the account menu, and click **Approve refund**. It still works, because the state was in Postgres all along. This is the most important demo in the project.
3. Back in Asha's window, the outcome appears by itself. Choose **Your orders**: `1001` is now `refunded`. Then sign in as Admin, open **All orders**, and click **Reset demo orders**.
4. Try again, and send "Any update?" while it's paused. The agent doesn't run.
5. Try again, and click **Reject** as Support, with a note. The order doesn't change.
6. Sign in as Kabir, and ask for a refund on order 1006, which costs $249. Support can see it, but only an Admin can decide it.
7. Sign in as Neha, and ask for a refund on order 1007, which is already refunded. No request reaches the queue.

## Interview questions

### How do you add human approval to an agent?

**Strong answer:** I check the rules in code first, so people only see valid requests. Then the agent saves its state and stops: it doesn't hold a thread open. In LangGraph that's `interrupt()`, with a checkpointer. A person's decision resumes it as a new request, which can happen hours later on another server. It survives restarts: I've proved that by restarting the API during a pending approval.

**Follow-up:** What happens if nobody ever responds?

### What's the danger of resuming a paused agent?

**Strong answer:** In LangGraph the node re-runs from the top on resume, so anything before `interrupt()` runs twice. If that's a side effect, like a payment, it happens twice. So side effects go after the interrupt, and I make writes safe to repeat where I can.

**Follow-up:** How else would you protect against a double refund?

### How do you stop approval becoming a rubber stamp?

**Strong answer:** Keep the volume down by only asking when it matters: code rejects what's clearly invalid, and low-risk cases could be automated with limits. Show the reviewer what they need to decide. Add higher approval for larger amounts, as I do above $200. And track how often people reject: if it's never, the step may not be doing anything.

**Follow-up:** Which refunds would you automate?

## Check yourself

### Why does the rule check run before a person is asked?

- [x] A person's time shouldn't go on requests the rules already refuse — right: and code gives the same answer every time.
- [ ] Rules are slower than people — they're far faster.
- [ ] People can't read order data — they can.

### What does `interrupt()` do?

- [ ] Keeps a thread waiting for hours — that would tie up the server.
- [x] Saves state and ends the run — right: a later request resumes it.
- [ ] Cancels the refund — it only pauses.

### Why must a side effect go after `interrupt()`?

- [ ] It runs faster there — it's about correctness.
- [ ] Python requires it — it's about how resuming works.
- [x] The node re-runs from the top on resume — right: otherwise it would happen twice.
