---
title: Claude Code's main features
checked: 2026-11-07
---

## What you'll learn

- What `CLAUDE.md`, skills, subagents, hooks, MCP and plugins each do
- The difference between asking and enforcing, with a measurement
- What each feature costs in context
- When to add one, and when not to

## The simple explanation

Claude Code works well with no setup. Its features are for when your project needs something it can't guess.

Imagine running a kitchen with a new chef:

| Feature | In the kitchen | What it really is |
| --- | --- | --- |
| **`CLAUDE.md`** | The note on the wall, read every shift | Instructions loaded into every session |
| **Skill** | A recipe card, taken out when needed | Instructions or a workflow, loaded on demand or run with `/name` |
| **Subagent** | An assistant sent to do one job and report back | A worker with its own separate context, returning a summary |
| **Hook** | A lock on the freezer | Your script, run by the harness at a fixed moment |
| **MCP** | A phone line to a supplier | A connection to an outside system |
| **Plugin** | A boxed set for another kitchen | A package of the above, to reuse or share |

The most important split is between the note and the lock. [Anthropic's best practices](https://code.claude.com/docs/en/best-practices) divide every instruction into two kinds:

- **Non-deterministic:** the model reads it and decides. That's your prompt, `CLAUDE.md` and skills.
- **Deterministic:** the harness applies it, whatever the model decided. That's hooks, deny rules and managed settings.

You've met this idea already. ShopHelper's rule is [the model asks, code acts](../08-security/03-layered-defences.md): a refund rule lives in code, because a prompt can't guarantee it. Claude Code works the same way.

Don't enforce everything, though. Most guidelines have exceptions, and the model can judge those with the code in front of it. Keep hooks for rules with **zero** exceptions. The docs warn that forty of them probably means most are only preferences.

## An example

We measured the difference. In a throwaway repo, `CLAUDE.md` said "Never edit files in migrations/", and we asked Claude to edit a migration.

Measured in this project on 2026-11-07, on Claude Opus 5.5 at medium effort, Claude Code 2.1.319, on Windows. It's 3 runs each, so treat it as a demonstration, not a rate.

| Setup | Request | Result |
| --- | --- | --- |
| Rule in `CLAUDE.md` only | Named the file directly | **Edited 3 of 3.** Claude noted the rule, and overrode it because we'd asked |
| Rule in `CLAUDE.md` only | "The project needs a users table" | **Rule kept 3 of 3.** Claude put the table somewhere else and said so |
| Rule plus a hook | Named the file directly | **Blocked 3 of 3.** The file stayed unchanged |

So the rule wasn't ignored. It worked as a guideline: followed by default, and outweighed by a direct request. That's often what you want. If the rule must hold even then, you need the hook.

The hook taught a second lesson by failing first. Our first version looked for `migrations/`, and the edit went straight through with no error. On Windows the path arrives as `...\\migrations\\001.sql`, so the pattern never matched. **A hook that doesn't match does nothing, silently.** The fix was a pattern accepting both slashes. Always test a hook by watching it block something.

**What each feature costs.** Everything loaded into context costs attention, and tokens too. From [the features guide](https://code.claude.com/docs/en/features-overview):

| Feature | Loads | Cost |
| --- | --- | --- |
| `CLAUDE.md` | Whole file, at session start | Every request |
| Skills | Descriptions at start, full text when used | Low |
| MCP servers | Tool names at start, full schemas on demand | Low until used |
| Subagents | Their own separate context | Isolated, but they use tokens |
| Hooks | Nothing, they run outside | Zero, unless they return output |

**When to add one.** The guide suggests waiting for a trigger, not configuring everything up front:

| When this happens | Add |
| --- | --- |
| Claude gets a convention wrong twice | A line in `CLAUDE.md` |
| You keep typing the same prompt to start a task | A skill |
| You keep copying data from a system Claude can't see | An MCP server |
| A side task floods the conversation | A subagent |
| Something must happen every time | A hook |
| A second repo needs the same setup | A plugin |

**Subagents don't make answers smarter.** The docs are direct: it's the same model or a smaller one on the same task. You get three real things: work in parallel, long output kept out of your way, and a reviewer who hasn't seen your reasoning. That last one is why `/code-review` runs in a fresh subagent. The cost is tokens, and sometimes time, because a fresh subagent must first gather what your session already knew. This matches what we saw in [multi-agent systems](../03-agents/07-multi-agent-systems.md).

**Permissions** are the other enforced layer. A `deny` rule holds in every permission mode. Auto mode, the default in terminal sessions, uses a classifier model to judge risky actions. It's a judgement, so the docs say your "never" rules belong in deny rules or hooks.

## How ShopHelper does it

| Feature | Used here? | How |
| --- | --- | --- |
| `CLAUDE.md` | Yes | 77 lines of rules and pointers |
| Custom commands | Yes | 5 files in `.claude/commands/`, such as `/spec-new` |
| MCP | Not by Claude Code | ShopHelper's own MCP server serves the agent, as in [stage 4](../04-mcp/01-why-mcp.md) |
| Subagents | Not defined | No custom ones in the repo |
| Claude Code hooks | **No** | There's no `.claude/settings.json` |
| Plugins | No | One repo doesn't need them |

The commands are plain Markdown prompts. This one creates a draft spec, and its last step is a rule:

```markdown file=.claude/commands/spec-new.md
5. Stop and list the open questions for the user. Do NOT write a plan or code.
```

These files use the older format. The [skills docs](https://code.claude.com/docs/en/skills) say commands have been merged into skills, existing files keep working, and new work should prefer a skill, which can hold supporting files.

Enforcement here happens outside Claude Code. A git pre-commit hook, once installed, runs fast checks on each commit, whether a person or Claude makes it:

```yaml file=.pre-commit-config.yaml
entry: uv run ruff check
```

CI then runs the full checks on each pull request. A Claude Code `Stop` hook running `scripts/check.sh` would catch failures sooner, inside the session. We haven't built that. It takes about a minute, which is a real cost on every stop, and that's a fair reason to leave it out.

## Try it

This uses a throwaway folder, not this repo, and a little of your Claude usage. Run it in Git Bash.

1. Make the folder, with a rule and a hook:

   ```bash
   mkdir -p /tmp/hook-demo/migrations /tmp/hook-demo/.claude && cd /tmp/hook-demo && git init -q
   echo "-- first migration" > migrations/001.sql
   echo "Never edit files in migrations/." > CLAUDE.md
   cat > .claude/block.sh <<'EOF'
   #!/usr/bin/env bash
   if grep -Eq 'migrations[/\\]+'; then echo "Blocked: migrations/ is protected" >&2; exit 2; fi
   EOF
   echo '{"hooks":{"PreToolUse":[{"matcher":"Edit|Write","hooks":[{"type":"command","command":"bash .claude/block.sh"}]}]}}' > .claude/settings.json
   git add -A && git -c user.name=demo -c user.email=demo@example.com commit -qm init
   ```

2. Ask Claude to break the rule, and look at the file:

   ```bash
   claude -p "Add the line '-- second' to the end of migrations/001.sql using your Edit tool. Then say what happened in one sentence." --permission-mode acceptEdits --max-turns 4 < /dev/null
   cat migrations/001.sql
   ```

   Exit code 2 blocks the call, and the error text goes back to Claude. The file should be unchanged.
3. Turn the hook off with `mv .claude/settings.json .claude/settings.off`, run step 2 again, and read how Claude explains itself. Undo the edit with `git checkout -- migrations`.
4. Decide where each rule belongs: "prefer named exports", "never read `.env`", "our release steps", "run the formatter after every edit". Check your answers against the tables above.

## Interview questions

### What's the difference between `CLAUDE.md` and a hook?

**Strong answer:** `CLAUDE.md` is an instruction the model reads and weighs. A hook is a script the harness runs, whatever the model decided. I measured it: with a "never edit migrations" line, a direct request got the edit 3 times out of 3, and Claude said it was overriding the rule. With a hook, it was blocked 3 out of 3. So guidelines go in `CLAUDE.md`, and rules with no exceptions go in a hook or a deny rule. I keep that set small, because each one needs upkeep.

**Follow-up:** What can go wrong with a hook?

### When would you use a subagent, and when wouldn't you?

**Strong answer:** I'd use one for independent parallel work, to keep long output out of my session, or for a reviewer who hasn't seen how the code was written. I wouldn't use one hoping for a better answer, because it's the same model or a smaller one. It also costs tokens, and it may be slower, since it has to gather context my session already has.

**Follow-up:** How would you stop a review subagent from editing files?

### Skill or `CLAUDE.md`: how do you choose?

**Strong answer:** By how often it's needed. `CLAUDE.md` loads every session, so it's for what every task needs, such as test commands and hard-won rules. A skill loads on demand, so a long release procedure doesn't weigh on an unrelated bug fix. If a workflow has side effects, I'd make sure only a person can start it.

**Follow-up:** How does Claude decide to load a skill?

## Check yourself

### A rule must hold even when someone asks otherwise. Where does it go?

- [ ] In `CLAUDE.md`, in capitals — the model still decides.
- [x] In a hook or a deny rule — right: the harness applies it, not the model.
- [ ] In a skill — a skill is instructions too.

### Your new hook never fires, and shows no error. What's likely?

- [x] Its pattern doesn't match what it receives — right: a hook that doesn't match does nothing, so test it.
- [ ] Hooks only work on Linux — ours ran on Windows.
- [ ] The model turned it off — the model doesn't run hooks.

### What does a subagent give you?

- [ ] A smarter answer — it's the same model or a smaller one.
- [ ] Free work — it uses tokens.
- [x] Separate context, with a summary back — right: useful for parallel work and fresh review.
