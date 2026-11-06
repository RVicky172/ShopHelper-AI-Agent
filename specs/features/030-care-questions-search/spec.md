# 030 — Care Questions Always Search the Policy

**Status:** Implemented
**Roadmap phase:** Backlog · **Created:** 2026-11-06 · **Owner:** RVicky172

## Summary

Customers who ask about ShopHelper Care or a warranty should get the answer from the store's policy. Today they often don't: only 12 of
24 interleaved Care questions searched the policy (D-016). The rest got a dead end, such as a request for an order number, and earlier
prompts invented which products Care covers. Two prompt rewrites didn't fix it, so the agent needs a check in code that doesn't depend on
the model choosing to search.

## User Stories

- **US-1:** As a customer, I want a correct answer about ShopHelper Care, so that I know whether I can buy it and what it costs.
- **US-2:** As a customer, I want an honest reply if the agent can't find the answer, so that I'm not told something made up.
- **US-3:** As a customer asking about something else, I want the same speed and answers as before, so that this fix costs me nothing.
- **US-4:** As a learner, I want to see this check explained, so that I understand when a prompt isn't enough.

## Acceptance Criteria

### Care and warranty questions

- [x] **AC-1:** Every question in the protected set (Q1) calls `search_policy` before the customer gets an answer, in the same turn. Measured
      on the 8 wordings from D-016, 3 interleaved rounds: 24 of 24. _(measurement)_
- [x] **AC-2:** The same holds for at least 8 new wordings, written before the fix and not used to tune it, 3 interleaved rounds: 24 of 24.
      _(measurement)_
- [x] **AC-3:** In those 48 attempts, a question about a lifestyle product says Care isn't available for it, and a question about an
      electronics product says 2 years, or $19.99 when the price is asked. No answer names a lifestyle category as covered. Every answer is
      read, and none is passed by a keyword check alone. _(measurement)_
- [x] **AC-4:** A question that was already asked earlier in the conversation still searches again in its own turn. _(unit)_
- [x] **AC-5:** If the policy search fails, the customer gets a fixed, honest reply that points them to support, and the model
      isn't asked to answer. _(unit)_
- [x] **AC-6:** On a protected question, no answer is written before the search, so the chat never shows one that's later
      withdrawn. _(unit + e2e)_

### Everything else stays the same

- [x] **AC-7:** A question outside the protected set gets no extra model call. Unit tests cover at least 10 near misses, such as "take care",
      "customer care", "skincare", and "How do I care for my kettle?". _(unit)_
- [x] **AC-8:** A protected question costs no extra model call. _(unit)_
- [x] **AC-9:** Refund requests with no warranty mention still submit: 45 of 45 interleaved attempts on the final code. Those that mention a
      warranty are a known bug, not fixed here (D-023). _(measurement)_
- [x] **AC-10:** The chat starters still get real answers, 57 of 57, read in full where the strict check flags one. _(measurement)_

### Proof and explanation

- [x] **AC-11:** The golden evals gain the 4 wordings that failed in D-016, and all cases pass. With the check removed, at least 3 of those 4
      fail, which proves they test it. _(e2e + sabotage)_
- [x] **AC-12:** `docs/learn/` explains why a prompt wasn't enough here, with the real numbers and a Try it step that was run. _(manual)_
- [x] **AC-13:** D-016 and 021's AC-39 note are updated to say the gap is closed, and the backlog entry is removed. _(manual)_

## Non-Functional Requirements

- Performance: a question outside the protected set takes no longer than before. A protected one adds no model call.
- Security: the check reads the customer's message and never gives the model any new way to change data (Constitution V).
- Compatibility: `/chat/stream` changes stay additive (Constitution IX). No new dependency.

## Out of Scope

- Follow-ups that don't name the topic, such as "what about a mug?" after a Care question.
- Other policy topics, such as shipping or payments. They search reliably in the measurements so far. A general rule is a separate feature.
- Misspellings, such as "warrenty".
- `raw_agent.py`, which is a learning comparison and doesn't serve customers.
- Testing on Claude, which belongs to Phase 1.

## Open Questions

All answered by the owner on 2026-11-06, who accepted the proposals.

- **Q1** What counts as a protected question? _Answer:_ the message contains "ShopHelper Care", "warranty",
  "warranties", "extended coverage" or "protection plan", in any letter case. "Care" alone doesn't count, because it's too common a word.
- **Q2** Should the check run on AWS too, or only locally? _Answer:_ everywhere, like the refund check. It fixes a bug
  in shared agent code, adds no setting, and has no cost unless it fires. AWS would pick it up on its next deploy, untested on Claude until
  Phase 1. Making it local only would mean a new setting, and leave AWS customers with the bug.
- **Q3** What should the honest reply in AC-5 say? _Answer:_ "I couldn't check our policy just now, so I don't want to
  guess. Please ask again, or contact support."

## Changelog

- 2026-11-06 — Created, from the backlog entry and D-016.
- 2026-11-06 — Questions answered and spec Approved.
- 2026-11-06 — Owner narrowed AC-9 to refunds that state a problem (D-022).
- 2026-11-06 — Owner took refunds that mention a warranty out of AC-9, as a known bug (D-023). AC-9 records the 45 of 45 measured.
- 2026-11-06 — All 13 criteria proven, status Implemented.
- 2026-11-06 — Plan review: code searches before the model answers, instead of sending the model back (D-018). AC-5, AC-6 and AC-8 reworded.
