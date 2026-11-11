---
title: How interviews run
checked: 2026-11-07
---

## What you'll learn

- The kinds of round you're likely to meet
- What each round is really testing
- How to answer so an interviewer can follow you
- How to spend the time you have before an interview

## The simple explanation

An AI engineer interview isn't one test. It's a series of conversations, and each looks for different evidence that you can do the job.

Think of a driving test. There's a theory paper, a drive around town, and an examiner watching how you handle a surprise. Knowing the rules isn't enough, and neither is driving well once. AI interviews work the same way: they check what you know, what you can build, and how you think when something goes wrong.

The biggest surprise for many people is that "AI engineer" often isn't a separate process. Prep guides report that these questions appear inside normal software engineering loops. So you still need ordinary engineering skills, with AI knowledge on top.

Nobody can promise you a format. Companies differ, and they change. What follows is what's commonly reported, not a rule. **Always ask the recruiter what each round covers.** It's a normal question, and the answer is worth more than any guide, including this one.

## An example

Here are the kinds of round you may meet. Not every company has all of them, and the order varies.

| Round | What happens | What it's really testing |
| --- | --- | --- |
| **Recruiter call** | Your background, and why this job | Is the role a fit, and can you explain yourself simply? |
| **Concept screen** | "Explain how RAG works" | Do you understand what happens behind an API call? |
| **Coding** | Build a small feature, or debug code you've never seen | Can you work in real code, not just puzzles? |
| **System design** | "Design a production RAG system" | Can you make trade-offs and plan for failure? |
| **Project deep dive** | "Walk me through something you built" | Did you really do it, and do you know why it's built that way? |
| **Behavioural** | "Tell me about a time you shipped something risky" | Your judgement, especially about shipping AI responsibly |

Take the same topic through three rounds, and see how the question changes:

| Round | The question | A weak answer | A strong answer |
| --- | --- | --- | --- |
| Concept | "What's a reranker?" | Recites a definition | Says what it does, why, and what it costs |
| Design | "Search results are poor. What now?" | "Add a reranker" | Measures retrieval first, then decides |
| Deep dive | "Did you use one?" | Implies yes | "Not in the app, but I tested one. Reranking the top 8 took the right chunk first from 17 to 20 of 20, on a small test" |

That last one is the pattern to copy. It's honest and specific, and it has a number you measured.

**How to answer anything.** Four habits work in almost every round:

1. **Say what you understood first.** "So the goal is fewer wrong answers, not faster ones?" A wrong assumption is the most expensive mistake in an interview.
2. **Give the short answer, then the detail.** Lead with the conclusion, and let them ask for more.
3. **Name the trade-off.** Every choice costs something. Saying what you gave up shows you considered it.
4. **Say "I don't know" cleanly.** Then say how you'd find out. Guessing confidently is much worse.

For behavioural questions, use a simple shape: the situation, what you did, what happened, and what you learned. Keep it near two minutes, and use *I*, not *we*, so they can see your part.

## How ShopHelper does it

This course was built to feed these rounds. Here's what to use for each:

| Round | Prepare from |
| --- | --- |
| Concept screen | [How LLMs work](../01-how-llms-work/01-tokens.md), [agents](../03-agents/02-the-agent-loop.md), [RAG](../05-rag/01-why-rag.md) |
| Coding | The project itself: read code you didn't write, and change it |
| Debugging | [Debugging scenarios](03-debugging-scenarios.md) |
| System design | [System design practice](02-system-design-practice.md) |
| Project deep dive | [How this project was built](../11-building-with-ai/04-how-this-project-was-built.md) |
| Behavioural | The stories in `memory/learnings.md` and `memory/decisions.md` |

Every lesson ends with interview questions. Each one has a strong answer and a likely follow-up, because the follow-up is where people get stuck. There are over 200 of them.

A project helps most in the deep dive. Many candidates can define RAG. Fewer can say what broke in theirs. These are real results you can quote, and each has a lesson behind it:

| Topic | What you can say |
| --- | --- |
| Evals | [37 cases](../07-evals-and-testing/03-golden-sets.md), 12 of them attacks |
| Reliability | False refund promises went from [0 of 20 to 60 of 60](../11-building-with-ai/04-how-this-project-was-built.md) on the tested wordings |
| Latency | [Median 2.95 s, p95 9.69 s](../10-running-in-production/02-the-metrics-that-matter.md), over 66 real turns |
| Limits | A known warranty refund bug, recorded and shipped on purpose |

One warning: [never claim something the project hasn't done](../11-building-with-ai/04-how-this-project-was-built.md). These numbers came from a local Qwen model on a test shop, so say that too. Being exact about your evidence is what makes it believable.

**What to do with the time you have.** This is our suggestion, not research:

| Time left | Focus on |
| --- | --- |
| One week | Your project story, and the interview questions in stages 3, 5 and 7 |
| Two weeks | Add the system design walkthroughs, out loud, against a timer |
| A month or more | The whole course in order, with a mock interview each week |

Practise out loud. An answer that feels clear in your head often falls apart when you say it.

## In the market

Checked on 2026-11-07. Most writing here comes from companies selling interview prep, so treat it as direction, not fact.

| Source | What it reports |
| --- | --- |
| [Aced (formerly Exponent)](https://www.aced.io/blog/ai-engineer-interview-questions) | These questions show up inside software engineer, ML engineer and forward-deployed loops. The screen is "a SWE screen with retrieval and serving questions layered in". Coding is project-style, often with an AI assistant allowed |
| [PracHub](https://prachub.com/resources/ai-engineer-interview-questions-2026-rag-agents-evals-and-production-systems) | Four common surfaces: a project deep dive, a build or debugging task, an architecture discussion, and a production or behavioural scenario. "No single round order or question set applies to every employer" |
| [Penn career services](https://careerservices.upenn.edu/blog/2026/06/25/45-ai-engineer-interview-questions-answers-2026-guide/) | Behavioural rounds at AI companies probe judgement about shipping AI responsibly |

Two claims we couldn't confirm, so don't repeat them: that a fixed share of questions are about generative AI, and that "design a RAG chatbot" is always the warm-up. Neither appeared in these guides when we read them.

**What differs between companies:**

| It depends on | So find out |
| --- | --- |
| The team | Product, platform or forward-deployed roles weigh skills differently |
| The company's stage | Is it building a new product, or running one at scale? |
| AI tool rules | Whether you may use an assistant, in each round. See [the AI-assisted round](04-the-ai-assisted-round.md) |

## Try it

1. Count the practice questions: `grep -c '^\*\*Strong answer:\*\*' docs/learn/*/*.md | awk -F: '{s+=$2} END {print s}'`.
2. Open any lesson's **Interview questions** on this site. Answer the first one out loud, against a two-minute timer, and only then open the strong answer. What did you leave out?
3. Try its follow-up. If you couldn't answer, that's the lesson to re-read.
4. Write down three questions to ask a recruiter about their rounds.
5. Pick one row of the "What you can say" table, and say it in two sentences, including what the number doesn't prove.

## Interview questions

### Walk me through a project you're proud of.

**Strong answer:** I built a customer support agent for a small test shop, to learn how these systems really work. It uses a LangGraph agent with tools, RAG over the policies, an MCP server, and a human approval step for refunds. The part I'd highlight is the testing: 37 evals, 12 of them attacks. One exposed the agent promising refunds it hadn't requested, so I moved that check from the prompt into code. It's a learning project, on a local model, with no real customers. What would you like to go deeper on?

**Follow-up:** What would break first with real traffic?

### What would you ask the recruiter before the interview?

**Strong answer:** What each round covers and how long it is, who I'll meet, and whether I can use AI tools in each round. I'd also ask what the team builds, and what a strong first six months looks like. Formats vary a lot, so that beats guessing, and it helps me spend my preparation on the right things.

**Follow-up:** What would you do if the rules on AI tools weren't clear?

### You're asked something you don't know. What do you do?

**Strong answer:** I say so plainly, then reason from what I do know, and say how I'd find out. For example: "I haven't used that database. If it's a vector store, I'd want to know its index type, filtering and cost, so I'd check those first." That shows how I think. Bluffing is risky, because the follow-up will expose it.

**Follow-up:** Tell me about something technical you got wrong recently.

## Check yourself

### Why ask the recruiter what each round covers?

- [ ] It's a test of confidence — it's simply useful.
- [x] Formats vary, and guides can't tell you this company's — right: it's a normal question.
- [ ] Recruiters give out the questions — they won't, but they'll tell you the format.

### What's strongest in a project deep dive?

- [ ] Claiming you built everything alone — the first detailed question exposes it.
- [ ] Listing every technology you used — a list shows no judgement.
- [x] A specific result, and what it doesn't prove — right: that's believable.

### You're given a design question. What comes first?

- [ ] Draw the architecture — you may solve the wrong problem.
- [x] Check what you understood — right: a wrong assumption is the costliest mistake.
- [ ] Name the database you'd use — that's far too early.
