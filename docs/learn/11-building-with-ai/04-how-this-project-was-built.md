---
title: How this project was built
checked: 2026-11-07
---

## What you'll learn

- How ShopHelper really went from one script to a full app
- What a person did, and what the agent did
- Where the process caught mistakes, and where it didn't
- How to talk about AI-built work honestly

## The simple explanation

ShopHelper was built with Claude Code, by one person directing it. The history is all here: the commits, specs, decisions and mistakes.

Think of a film director. They may not hold the camera, but they choose the story, reject bad takes, and answer for the result. Directing an agent is similar. Most of the typing was the agent's. The goals, approvals and hard calls were the owner's.

That doesn't make it easy, and it doesn't make the work someone else's. It does mean you should describe it accurately. An interviewer will ask, and "I built all of this by hand" falls apart at the first detailed question. "I directed it, and here's how I checked it" holds up, if you can really explain the code.

## An example

The project's main story has three days in it. Dates come from `memory/progress.md`, because git only shows two commit dates: most of the work was committed on 2026-11-06.

| Date | What happened |
| --- | --- |
| 2026-11-01 | Twelve steps, one idea at a time: a raw Bedrock agent loop with one tool, then an API, history, RAG, guardrails, evals, two ways to deploy on AWS, monitoring and CI/CD. The AWS stack was torn down the same day |
| 2026-11-04 | Claude on Bedrock was blocked by a use-case form, so the project went local first (D-003). Spec-driven development adopted (D-001). Accounts and the storefront built |
| 2026-11-06 | Care questions, a code structure clean-up, and this course |

**What changed halfway matters most.** The first day had no specs: each step was small enough to hold in your head. As the project grew and sessions piled up, that stopped working. Nothing carried over between sessions, so the project needed [written specs and memory](03-spec-driven-development.md).

**Who did what** is easy to check. When this was written, 47 of the 69 commits on `main` carried a `Co-Authored-By: Claude` line. That's a rough measure, and it shows the shape:

| The owner | Claude Code |
| --- | --- |
| Chose what to build and why | Drafted specs, plans and tasks |
| Answered open questions | Wrote most code, tests and lessons |
| Approved each spec and plan | Ran checks and fixed failures |
| Reviewed style, and tried the app | Recorded results, decisions and gotchas |
| Made calls about risk and scope | Stopped when a decision wasn't its to make |

## How ShopHelper does it

Here are real cases, with what caught each one. They're the useful part of this lesson.

| What went wrong | What caught it | Lesson |
| --- | --- | --- |
| The agent falsely promised refunds: 0 of 20 on one wording | A failing eval, then a code fix: 60 of 60 | A prompt rule can look fixed and not be. Feature 020 was moved back from Implemented |
| A refund wording scored 20 of 20 repeated, and 0 of 20 mixed with other questions | Measuring it a second way | LM Studio's prompt cache made repeats look reliable. Passing several times proved little |
| A lesson misquoted a schema comment | The snippet test | A rule in code beats remembering to check |
| An interview claim had no source that supported it | Reading the source, not a summary | The answer was reworded |
| "Open What's stored" read fine, but was a heading, not a button | Running the Try it step | Do the exercise, don't just write it |
| A "no leaks" check could pass on a broken server | Adding a positive control | Check that each user still sees their own data |

The first row shows the pattern. A rule in the prompt only reduced the false promises, so the final check is code in `graph.py`:

```python file=src/shophelper/agent/graph.py
REFUND_PROMISE = re.compile(
```

**Sabotage checks** run through all of these. After writing an important test, you break the code on purpose, confirm the test fails, then restore it. The accounts feature recorded 16 of 16 sabotage checks caught on its staff refund work. A test that has never failed hasn't proved anything.

**Not everything was caught.** Be honest about these too:

- A customer who mentions a warranty can still be wrongly refused a refund, at 0 of 8 on one wording. The owner chose to ship and put the fix in the backlog (D-023).
- The MCP server is a version behind the current spec.
- The eval results quoted in this course come from Qwen, running locally, not from Claude.
- LangSmith tracing is wired in, but it's off locally and [never ran with a real model on AWS](../10-running-in-production/01-monitoring-and-tracing.md). The logs hold no prompt or model version either, as [managing prompts and models](../10-running-in-production/04-managing-prompts-and-models.md) admits.

**What made it work.** Looking back, four habits did most of it:

1. **Small steps:** one task, then a check, then the next.
2. **Evidence over reports:** numbers were measured, and a claim needed output behind it.
3. **Real runs:** every Try it step and browser flow was run, and running them found things that reading didn't.
4. **Written memory:** decisions, gotchas and progress are in files, so the next session starts with them.

The project keeps those files in git. The gotchas in `memory/learnings.md` are worth reading before an interview: each one is a real story.

## Not in ShopHelper

Some things a job would have, this project doesn't:

- **A team.** There's one owner, so no code review from another person, and no real production users.
- **Real traffic.** It's a fictional shop. The measurements came from test turns, not customers.
- **Long-term upkeep.** All of it was built in a week, so nothing here shows how it ages.

Say so if you're asked. Knowing the limits of your evidence is itself a sign of experience.

## Try it

Run these from the project root.

1. See how it started: `git log --reverse --format='%ad %s' --date=short | head -5`.
2. Measure the split: `git log --oneline | wc -l`, then `git log --format=%B | grep -c 'Co-Authored-By: Claude'`. These counts grow as work continues.
3. Do a sabotage check. Open `docs/learn/11-building-with-ai/03-spec-driven-development.md`, and change one word in the line quoted from `specs/constitution.md`. Run `uv run pytest tests/test_course.py -k code_examples -q`. It should fail and name the line. Restore it with `git checkout -- docs/learn/11-building-with-ai/03-spec-driven-development.md`.
4. Read `memory/learnings.md`, and pick the two gotchas you could explain best. Tell one aloud in a minute: what happened, how it was found, what changed.
5. Write your own version of the table above, with what you really did. If you only read this project and didn't build it, say that too.

## Interview questions

### How much of this project did you write yourself?

**Strong answer:** Claude Code wrote most of the code, and I'll be direct about that: 47 of the first 69 commits carry its co-author line. My work was deciding what to build, approving each spec and plan, making the risk calls, and checking the results. I can explain how it works, and I'm happy to walk through any part. What I'd point to is the process: every requirement has a test, and I break code on purpose to prove those tests work.

**Follow-up:** Pick a file. Why is it written that way?

### Tell me about a time the AI got something wrong.

**Strong answer:** The agent promised refunds it couldn't give. A failing eval exposed it, at 0 of 20 on one wording. What made it interesting is that another run looked fine: repeated prompts scored 20 of 20, because the local model's prompt cache repeated its result. Once I mixed in other questions, the failure showed up. A prompt rule couldn't hold it, so the fix went into code, and it then scored 60 of 60. I learned to distrust repeat passes, and to put anything a customer relies on in code.

**Follow-up:** How do you know it's really fixed?

### What would you do differently?

**Strong answer:** I'd log the prompt and model version from the start, and have tracing running locally, not just wired in, because they're cheap early and I can't debug old answers without them. I'd start specs sooner too. The first day had none, which was fine for tiny steps, but memory should exist before you need it. And I'd enforce the checks with a hook, not just an instruction.

**Follow-up:** Which of those would you do first, and why?

## Check yourself

### How should you describe a project an agent mostly wrote?

- [ ] Say you wrote it all — it falls apart at the first detailed question.
- [ ] Say you did little — you'd hide the real work of directing and checking.
- [x] Say what you directed and how you checked it — right: and be able to explain the code.

### Why break code on purpose after writing a test?

- [x] To prove the test can fail — right: a test that has never failed proves nothing.
- [ ] To make the suite slower — that's not a goal.
- [ ] To find bugs in the code — it's testing the test.

### A check passes 20 of 20 on the same prompt. What should you think?

- [ ] It's proven — repeats can share a cached result.
- [x] Try it mixed with other questions — right: that's how the real failure appeared here.
- [ ] Run it 20 more times — that repeats the same weakness.
