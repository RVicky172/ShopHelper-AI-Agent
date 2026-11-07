---
title: The AI-assisted round
checked: 2026-11-07
---

## What you'll learn

- Why company rules on AI differ, and how to find out what's allowed
- What interviewers look for when you use AI in front of them
- How to run a round from start to finish
- The common ways people fail it

## The simple explanation

**Company rules differ. Before any interview or take-home, ask the recruiter what's allowed, for each round.** Some companies require AI tools. Some ban them. Some let you use them in one round but not another. Never assume, and never rely on a website's list. If AI isn't allowed, don't use it.

Where AI is allowed, the round tests something new. Imagine a driving test in a car with lane assist. The examiner doesn't care that the car can steer. They watch whether you still check the mirrors, and whether you take over when it drifts. In an AI-assisted round, the tool can write code quickly. The interviewer watches your judgement around it.

So this isn't a test of how fast you get code. It's a test of whether you stay in charge: you break down the problem, direct the tool, check its work, and answer for the result.

Canva, which requires AI tools in this round, says engineers must ["take full ownership of any code they produce"](https://www.canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews/), however it was written.

## An example

Here's how far apart the rules can be, in companies' own words:

| Company | What it says | Source |
| --- | --- | --- |
| **Anthropic** | Take-homes: "Complete these without Claude unless we indicate otherwise." Live interviews: "no AI assistance unless we indicate otherwise." Using Claude to prepare is encouraged | [Candidate guidance](https://www.anthropic.com/candidate-ai-guidance) |
| **Canva** | Says "we now expect Backend, Machine Learning and Frontend engineering candidates to use AI tools" | [Engineering blog](https://www.canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews/) |

One builds Claude, and says don't use it unless told. The other insists on AI tools. So "AI companies allow AI" is simply false.

**Don't trust lists.** When we checked, a [public policy tracker](https://www.techinterview.org/post/3233474911/ai-tool-policy-tracker-tech-companies-2026/) said Anthropic "allows AI tools (including Claude itself) in coding rounds", with no source for that entry. Anthropic's own page says the opposite, unless it tells you otherwise. A rule may also vary by team or round. Only the recruiter can tell you what applies to you.

**Questions to ask the recruiter:**

1. May I use AI tools in this round? In which others?
2. Which tools, and do you provide them or do I bring my own?
3. Can I use the web and documentation?
4. Will you see my prompts?

Asking is normal, and it costs you nothing. Get the answer in writing if you can. If a rule is unclear, ask again, and assume "no" until you hear otherwise. Using AI in secret where it's banned is dishonest, and it can end your application.

**What interviewers look for.** Canva published its criteria, and it's the clearest public account we found. [Its interviewers](https://www.canva.dev/blog/engineering/ai-interview-success/) assess three areas together:

| Area | Means |
| --- | --- |
| **Problem-solving** | Breaking down an unclear problem, choosing scope, seeing edge cases |
| **Technical depth and ownership** | Understanding the code, spotting issues, explaining your choices |
| **AI collaboration** | Using it for suitable tasks, while keeping control and judging its output |

Canva also names three ways people go wrong:

| Pattern | What it looks like | Do this instead |
| --- | --- | --- |
| **AI Showcase** | Showing off the tool, and losing sight of the task | Keep your attention on the problem |
| **Feature Marathon** | Building as much as possible, and accepting output quickly | Do less, and do it properly |
| **Hands-Off** | Treating it as a complete solution generator | Stay the engineer; it's the accelerator |

That's one company's view. It matches CodeSignal's description of [measuring how candidates work with AI](https://codesignal.com/blog/best-ai-assessment-platforms/), but other companies may weigh things differently.

**How to run the round.** This is our suggested routine, drawn from those criteria:

1. **Understand.** Read the task, and ask questions before touching the tool. Agree the scope aloud.
2. **Sketch.** Say your plan and the main pieces. Canva says strong candidates sketch an architecture first.
3. **Direct.** Give the tool small, specific tasks. Use it for skeletons, research and routine code. Slow down for anything complex.
4. **Check.** Read every change. Run it. Write or ask for a test, and look for what's missing.
5. **Explain.** Talk as you go: why you accepted this, why you rejected that.
6. **Finish like a pull request.** Say what works, what doesn't, and what you'd do before production.

**Think aloud.** The interviewer can't see your judgement unless you say it. "I'm rejecting this because it doesn't handle an empty cart" is worth more than a silent fix.

**Assume there's a bug.** Reports say some platforms let an interviewer tell the agent to slip in a bug, to see if you review its work. We couldn't open the page to confirm that, but the habit is right either way: never accept code you haven't read.

**When the tool goes wrong**, stay calm, because recovering well is good evidence. Stop it, say what went wrong, and give a better instruction, or just write that part yourself. Be ready to work without it, because tools can fail, and you may be asked to explain any line.

## How ShopHelper does it

This whole project is practice for this round, because it was built by directing an agent. These habits carry straight over:

| In this project | In the round |
| --- | --- |
| [A spec before code](../11-building-with-ai/03-spec-driven-development.md) | Agree the scope before prompting |
| [A check to run](../11-building-with-ai/01-working-with-claude-code.md) | Write a test early, so the tool can correct itself |
| Sabotage checks | Prove your test can fail |
| Checking claims against the code | Don't believe the tool's summary: read the diff |
| Stopping for the owner's decisions | Tell the interviewer when a choice needs a human |

We ran the exercise below ourselves, and it's a good reminder of where the real gap is. Asked for a small refund check, Claude wrote correct code and tests, and it stated two assumptions: day 30 counts, and future dates are refused. That's what you should hope for. But compare it with the real rule:

```python file=src/shophelper/shop/orders.py
def refund_eligibility(order: dict[str, Any], amount: float) -> tuple[bool, str]:
```

The real one also checks whether the order was already refunded, whether it was delivered at all, and the amount. **Claude didn't get those wrong. Nobody asked.** The code was right, and the requirement was thin. That's why this round rewards understanding the problem: the tool can't supply what you failed to ask for.

## In the market

Checked on 2026-11-07. These change quickly, and vendors describe their own products, so treat this as a guide to what you might meet.

| Platform | What it offers | How we checked |
| --- | --- | --- |
| [CodeSignal](https://codesignal.com/blog/best-ai-assessment-platforms/) | Says its assessments "simulate AI-assisted work rather than treating AI as something to detect or prohibit" | Read on 2026-11-07 |
| [CodeSignal Agentic Interviewing](https://support.codesignal.com/hc/en-us/articles/38841637349015-How-can-I-use-Agentic-Interviewing-in-my-recruiting-process) | A question where candidates use coding agents, assessing how they prompt, review and validate | Read on 2026-11-06. It refused our request on 2026-11-07 |
| [Codility](https://support.codility.com/hc/en-us/articles/49075175492497-Claude-Code) | Claude Code inside its interview environment, as a preview, with prompts that interviewers can review | Read on 2026-11-06. It refused our request on 2026-11-07 |

**What this means for you:** expect your prompts to be visible, on any platform. Write them as if your interviewer is reading, because they may be. Find out in advance which tool you'll get, too. If it isn't the one you know, spend an hour with it first.

## Try it

This uses a throwaway folder and a little of your Claude usage.

1. Ask for something small, and read the result:

   ```bash
   mkdir -p /tmp/ai-round && cd /tmp/ai-round && git init -q
   claude -p "Write refund.py with a function can_refund(delivered_on, today) that returns True if a refund is allowed within 30 days of delivery, and test_refund.py with pytest tests. Keep it small." --permission-mode acceptEdits --max-turns 8 < /dev/null
   cat refund.py
   ```

2. Before reading further, say aloud what it assumed. Is day 30 allowed? What about a date in the future?
3. Compare it with `refund_eligibility` in `src/shophelper/shop/orders.py`. List what the real rule checks that this doesn't. Which of those should you have asked about?
4. Set a 30-minute timer and practise on a task of your own, talking aloud. Afterwards, could you explain every line?
5. Write your own version of the four recruiter questions, and keep them for your next application.

## Interview questions

### Can you use AI tools in this interview?

**Strong answer:** I'd ask that before it starts, not assume. Rules vary by company and by round, so I ask the recruiter what's allowed, which tools, and whether my prompts are visible. If AI isn't allowed, I don't use it. If it is, I'll think aloud, so you can see how I'm using it.

**Follow-up:** What would you do if the instructions were unclear on the day?

### How do you decide what to give the AI and what to do yourself?

**Strong answer:** I give it what's easy to check: boilerplate, routine code, looking up an API. I keep the things that need judgement: understanding the problem, the design, and anything risky, such as security or money. Even then, I read everything it writes. On my project the agent wrote most of the code, but I reviewed each spec, and rules like refund eligibility live in tested code, not in a prompt.

**Follow-up:** Give me an example where you rejected its output.

### The AI gives you code that passes the tests but looks wrong. What do you do?

**Strong answer:** I trust my doubt and investigate, because passing tests only prove what they test. I'd read it, work out what bothers me, and write a test for that case. If the test fails, I've found a gap. If it passes, I've learned something. I'd say all this aloud, because how I check is what's being assessed.

**Follow-up:** How would you do this under time pressure?

## Check yourself

### You're invited to a live coding interview. What should you do about AI tools?

- [ ] Use them, since everyone does — some companies forbid it.
- [ ] Check a public tracker — trackers can be wrong, and rules vary by round.
- [x] Ask the recruiter what's allowed — right: only they can say what applies to you.

### What's being tested in an AI-assisted round?

- [ ] How fast you can produce code — Canva names that as a mistake.
- [x] Your judgement in directing and checking the tool — right: you stay in charge.
- [ ] How many tool features you know — that's the "AI Showcase" pattern.

### The tool's code ran correctly but missed a business rule. Why?

- [x] You didn't tell it the rule — right: it can't supply a requirement nobody stated.
- [ ] The tool is broken — it did what was asked.
- [ ] You needed a longer prompt — what matters is the content.
