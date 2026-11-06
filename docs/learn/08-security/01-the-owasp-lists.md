---
title: The OWASP lists
checked: 2026-11-06
---

## What you'll learn

- What OWASP is, and why interviewers mention it
- The two lists that matter for AI work
- How each risk applies to a real agent
- Where this project stands against them

## The simple explanation

**OWASP** is a non-profit that publishes security guidance. Its Top 10 lists are a shared vocabulary: when a security team says "LLM01", everyone knows it means prompt injection.

Think of a home safety checklist. It doesn't make your house safe by itself. It tells you where to look: smoke alarms, loose wires, the back door.

An AI app adds risks a normal app doesn't have, because it takes untrusted text and hands it to something that follows instructions. There are two lists to know:

| List | Covers | Published |
| --- | --- | --- |
| [Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/) | Apps that use a model | 2025 edition |
| [Top 10 for Agentic Applications](https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/) | Agents that take actions | December 2025 |

The first asks "what can go wrong with a model?". The second asks "what can go wrong when it can act?".

## An example

Here's the LLM list, mapped onto this shop:

| ID | Risk | In this project |
| --- | --- | --- |
| LLM01 | Prompt Injection | Measured in [the next lesson](02-prompt-injection.md) |
| LLM02 | Sensitive Information Disclosure | Owner filter in SQL, and masking |
| LLM03 | Supply Chain | Lock files, and pinned hashes in Docker |
| LLM04 | Data and Model Poisoning | Policies are written by the owner, so the risk is low |
| LLM05 | Improper Output Handling | The chat renders Markdown without raw HTML |
| LLM06 | Excessive Agency | The model can't refund anything |
| LLM07 | System Prompt Leakage | It leaks, so it holds no secrets |
| LLM08 | Vector and Embedding Weaknesses | One shared set of public policies |
| LLM09 | Misinformation | Answers come from passages, and evals check it |
| LLM10 | Unbounded Consumption | A step limit, and a length limit. **No rate limit** |

Read LLM07 again. The system prompt isn't secret, and we prove that next lesson. The right response isn't to hide it better. It's to keep anything sensitive out of it.

And LLM10 is a real gap: nothing stops someone sending thousands of messages, each one costing a model call.

## How ShopHelper does it

Here's the agentic list:

| ID | Risk | Means | In this project |
| --- | --- | --- | --- |
| ASI01 | Agent Goal Hijack | Injected text changes what the agent is doing | Partly open: see the next lesson |
| ASI02 | Tool Misuse | Good tools used badly | Few tools, and rules in code |
| ASI03 | Identity & Privilege Abuse | Acting with someone else's rights | Identity never passes through the model |
| ASI04 | Agentic Supply Chain | Bad tools or servers | MCP server is our own |
| ASI05 | Unexpected Code Execution | Model output gets run | The agent can't run code |
| ASI06 | Memory & Context Poisoning | Bad data saved for later | History is per conversation |
| ASI07 | Insecure Inter-Agent Communication | Agents trust each other too much | Signed token to the MCP server |
| ASI08 | Cascading Failures | One error spreads | One agent, and a step limit |
| ASI09 | Human-Agent Trust Exploitation | Tricking the human reviewer | Staff see stored values |
| ASI10 | Rogue Agents | Agents acting outside their role | Limited tools and approval |

The strongest single idea in this project answers several of these at once. It's in the constitution:

```text
The model never performs an action itself. Anything that changes data or moves money is decided in
deterministic code, not in a prompt.
```

Compare that with ASI09. A human approving things isn't automatically safe, because a tired person clicks yes. So the reviewer's screen shows amounts from the database, never the model's words about them.

## In the market

Checked on 2026-11-06.

- [OWASP's AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html) is the practical companion. It's where to look when you're building.
- Some articles describe a 2026 edition of the LLM list. OWASP's own page still showed 2025 when we checked, so quote the page and not the blogs.
- [MITRE ATLAS](https://atlas.mitre.org/) maps real attacks on AI systems, and the [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) is what larger companies often use for governance.

In an interview, don't recite the list. Pick the two or three risks that matter for the system you're discussing, and say what you'd do.

## Try it

1. Open the [LLM Top 10](https://genai.owasp.org/llm-top-10/), and read LLM06.
2. For each row of the first table above, decide if you agree with "in this project". Which would you test first?
3. Find one gap we haven't listed.

## Interview questions

### What are the biggest security risks in an LLM application?

**Strong answer:** Prompt injection comes first on OWASP's list, and it has no complete fix, so I design as if it will succeed. Next is excessive agency: what can a hijacked model do? And sensitive data disclosure. In my project the model can't move money, and identity never passes through it, so a successful injection has limited reach. I'd name unbounded consumption too, since I have no rate limit yet.

**Follow-up:** How is an agent's risk different from a chatbot's?

### What's excessive agency?

**Strong answer:** Giving a model more power than the job needs: too many tools, too much access, or actions without checks. The fix is least privilege. My agent has a few tools, the MCP server is read-only, and a refund has to pass code rules and a human. So the most a hijacked model can do is ask.

**Follow-up:** How would you decide which actions need a human?

## Check yourself

### What's LLM01?

- [x] Prompt injection — right: first on the list.
- [ ] Excessive agency — that's LLM06.
- [ ] Supply chain — that's LLM03.

### The system prompt leaks. What's the right response?

- [ ] Add a rule saying never reveal it — that's easily talked around.
- [x] Keep secrets out of it — right: assume it can be read.
- [ ] Encrypt it — the model has to read it.

### What does the agentic list add?

- [ ] Web security basics — that's a different list.
- [ ] Model training advice — that isn't its focus.
- [x] Risks from agents that can act — right: tools, identity and approvals.
