---
title: How to work with Claude Code
checked: 2026-11-07
---

## What you'll learn

- What a coding agent is, and how it differs from a chatbot that writes code
- The three things that decide whether a session goes well
- How to steer a session, and when to start again
- How to stay responsible for code you didn't type

## The simple explanation

Claude Code is an agent that works on your project. You describe a task. It reads your files, edits them, runs commands, looks at the result, and repeats until it thinks it's finished.

That's the same [agent loop](../03-agents/02-the-agent-loop.md) ShopHelper uses. ShopHelper's tools look up orders. Claude Code's tools read files, edit code and run commands. [Anthropic's docs](https://code.claude.com/docs/en/how-claude-code-works) call the phases gather context, take action and verify results. They call the layer around the model, which provides the tools and manages the context, the **harness**.

Think of a capable new colleague on their first day. They're quick and they read code well. But they weren't in last week's meeting, and they don't know what "done" means here. Each new session is another first day, because a session starts with no memory of earlier ones.

[Anthropic's best practices](https://code.claude.com/docs/en/best-practices) come down to three jobs for you:

| Your job | Why | Without it |
| --- | --- | --- |
| **Tell it what it can't see** | Decisions and processes that were never written in the repo | It builds the wrong thing, or rediscovers the same fact every session |
| **Give it a check to run** | Something that comes back pass or fail | It stops when the work *looks* done, and you become the test suite |
| **Enforce the rules with no exceptions** | A prompt is a request, not a guarantee | It usually obeys, and "usually" isn't always enough |

The second one matters most. An agent with a test to run can find and fix its own mistakes. An agent without one can only tell you it's finished.

## An example

Compare two prompts for the same job. The second is adapted from Anthropic's page:

| Vague | Specific |
| --- | --- |
| "fix the login bug" | "users report login fails after the session times out. Look at token refresh in `src/auth/`, write a failing test that reproduces it, then fix it" |

The specific one gives three things Claude can't work out alone: the symptom, where to look, and what "fixed" means. The failing test is the check. Claude can now run it and see for itself.

Vague prompts are fine when you're exploring, such as "what would you improve in this file?". You'll just correct more as you go.

**Steering a session.** Three controls cover most of it:

| Control | What it does | Use it when |
| --- | --- | --- |
| `Esc` | Stops Claude and keeps the work so far | It's heading the wrong way |
| `/rewind` | Rolls code, conversation or both back to an earlier prompt | You want to undo a bad direction |
| `/clear` | Starts a fresh conversation | You're moving to an unrelated task, or two corrections haven't worked |

The last rule surprises people. After two failed corrections, the conversation holds two wrong attempts, and Claude keeps re-reading them. The docs say `/clear` and one better prompt works better "almost every time" than a third correction.

One warning: rewind covers files Claude changed with its own file tools. A file changed by a shell command isn't restored, and nothing on a remote system is. Keep using git.

**Plan first when the change is unclear.** Plan mode lets Claude explore and propose without editing your source files. When you don't yet know what you want, ask it to interview you and write a spec, then build from that in a fresh session.

**Some old advice has expired.** The docs list habits you can now drop: "think harder" isn't a control (the effort setting is), ALL CAPS mostly makes Claude over-apply a rule, and describing your file layout in `CLAUDE.md` wastes space, because Claude reads the repo itself. Advice about these tools ages fast, so check the date on what you read, including here.

## How ShopHelper does it

This project was built with Claude Code, and the three jobs each have a home.

**What it can't see** lives in `CLAUDE.md`, loaded into every session. It's 77 lines, under the 200 the docs recommend. Most lines point at other files or state a rule that isn't visible in the code:

```markdown file=CLAUDE.md
- **Don't deploy to AWS or create paid resources** unless the user asks in that session.
- **The model asks, code acts.** Never put a state-changing tool on the MCP server (Constitution V).
```

A session has no memory, so `CLAUDE.md` tells it where to pick up:

```markdown file=CLAUDE.md
1. Read `memory/MEMORY.md` (current state + active feature).
2. Read the newest entry in `memory/progress.md`.
```

**The check** is one command, and the file says so:

```markdown file=CLAUDE.md
`scripts/check.sh` must pass before any task is marked done.
```

That runs lint, types, unit tests and the frontend checks. For the agent's behaviour, evals are the check, as in [test levels](../07-evals-and-testing/02-test-levels.md).

**Rules with no exceptions** are the weak spot, and the next lesson shows why. The line above is an instruction, so Claude could skip it. CI runs the same kinds of checks on a pull request, but nothing stops a session from ending with them unrun. Here the backstop is a person reading the result.

**Human review.** The owner approves each spec and plan, and made the calls an agent shouldn't, such as shipping with a known bug (D-023).

## In the market

Checked on 2026-11-07. These tools change monthly, and none of this is a ranking.

| Tool | Where it works | Note |
| --- | --- | --- |
| [Claude Code](https://code.claude.com/docs/en/how-claude-code-works) | Terminal, desktop, IDE, web, CI | Runs locally by default, or in the cloud |
| [Codex CLI](https://learn.chatgpt.com/docs/codex/cli) | Terminal | OpenAI's tool, working on your local repository |
| [Copilot coding agent](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent) | GitHub's cloud | Works in the background: one branch and one pull request per task |
| [Cursor](https://cursor.com/docs/agent/overview) | Editor, CLI, web | An agent built around its own editor |
| [Kiro](https://kiro.dev/docs/specs/) | Editor, web | Built around specs, covered in [spec-driven development](03-spec-driven-development.md) |

**How to choose:** the skills in this lesson carry across all of them. Each needs context, a check and limits. Pick by where your team works, what your company allows, and whether you want to watch the work or hand it off.

**One file for several tools:** [AGENTS.md](https://agents.md/) is an open format for agent instructions, and many of these tools read it. Claude Code's docs say it can read an `AGENTS.md` in place of a `CLAUDE.md`, so a team using several tools needn't keep copies.

## Try it

You'll need Claude Code installed. These steps use a little of your Claude usage and change nothing in the repo.

1. In a session in this project, run `/context`. From Git Bash, use `MSYS_NO_PATHCONV=1 claude -p "/context"`, because Git Bash otherwise turns `/context` into a file path. Find **Memory files**. Here, `CLAUDE.md` took 1.4k of a 1M-token window: cheap, but paid on every request.
2. Ask for a plan with no edits:

   ```bash
   claude -p "Plan only, no edits: where would a new order status called 'delayed' have to change? List the files, one line each." --permission-mode plan --max-turns 8
   ```

   When we ran it, the plan named the files, said which needed no change, and asked two questions a person must answer, such as what sets an order to delayed. Run `git status` afterwards to confirm nothing changed.
3. Run `scripts/check.sh` and read the last line. This is what Claude runs to check its work.
4. Rewrite "fix the warranty refund bug" as a specific prompt, using D-023 in `memory/decisions.md`. Include the symptom, where to look, and how you'd prove the fix.

## Interview questions

### How do you get good results from a coding agent?

**Strong answer:** I do three things. I give it what it can't see, such as decisions and how we deploy. I give it a check that passes or fails, usually a failing test, so it can correct itself. And I enforce the rules that can't bend with configuration, not a prompt. Then I watch the first minute and stop it early if it drifts. On my project, `CLAUDE.md` holds the rules, one script is the check, and I review each spec and plan.

**Follow-up:** What do you do when it keeps getting something wrong?

### How do you stay responsible for code an agent wrote?

**Strong answer:** I treat it like a pull request from a fast colleague. I ask for evidence, meaning the command it ran and the output, because "all tests pass" on its own tells me little. I read the diff, and I make sure I can explain it. For anything important, I break the code on purpose to confirm the test really catches it. If I can't explain a change, it doesn't go in.

**Follow-up:** How do you review a very large change?

### Why start a new session rather than keep correcting?

**Strong answer:** Every message stays in the context and gets re-read. After two failed attempts, the wrong approaches are part of what the model sees, and the cost of each turn has grown too. A fresh session with one better prompt, including what I learned, usually does better. Anything that should survive goes in a file, not the chat.

**Follow-up:** What would you lose by clearing, and how do you keep it?

## Check yourself

### What's the most useful thing to give a coding agent?

- [ ] A longer prompt — length isn't what helps.
- [x] A check it can run that passes or fails — right: then it can find its own mistakes.
- [ ] Capital letters on the important rules — that mostly makes it over-apply them.

### You've corrected the same mistake twice. What now?

- [ ] Correct it a third time, more firmly — the failed attempts stay in the context.
- [x] Run `/clear` and write one better prompt — right: fold in what you learned.
- [ ] Switch off the tests — that removes the check.

### What belongs in `CLAUDE.md`?

- [ ] Your folder layout — Claude can read that itself.
- [ ] Everything, to be safe — every line costs attention on every task.
- [x] What Claude can't work out from the repo — right: such as test commands and decisions.
