---
name: log-ticket
description: Writes a new ticket in work/ from a project idea or a piece of work, with agent instructions, a commit plan and acceptance criteria. Use when the person asks to log, raise, create or plan a ticket, or when work turns up mid-ticket that doesn't belong to it.
---

# Log a ticket

Turn the person's request into a ticket file in `work/`, for them to review and commit. Don't start the work itself: `start-ticket` does that.

## Steps

1. **Understand the request.** If the goal, the scope or the language isn't clear, ask before writing.
2. **Check for duplicates.** Search the tickets in `work/`. If one already covers the request, show it and stop.
3. **Gather only what the plan needs.** Read enough of the code and docs to name the sources and plan the commits, and no more.
4. **Number it.** Take the next free `TKT-NN`, one more than the highest in `work/`, starting at `TKT-01`.
5. **Plan the commits.** Each commit is one small change that works on its own and can be reviewed in a few minutes, listed in the order they land. For a new project, the first commit sets up the skeleton and its checks, such as a test runner and a linter, so every later commit has checks to run. Then plan the post-commit tests: end-to-end checks that prove the finished work does what the ticket says, such as running the program and trying each feature.
6. **Write** `work/TKT-NN <title>.md` in the shape below, creating `work/` if it doesn't exist.
7. **Propose its commit message,** `docs(work): add TKT-NN <short summary> (TKT-NN)`, and stop. A new ticket is always its own commit.
8. **Iterate until the person is happy.** If you have concerns about the plan, say so; don't just agree. They commit the ticket themselves.

## Ticket shape

```markdown
---
status: backlog
---
## Description

What the ticket delivers and why, in a few sentences. Then any ticket
that must be done first: Depends on TKT-01.

## Agent instructions

1. Sources to read first, such as files, docs or examples.
2. Numbered steps, naming every sign-off point: "Propose <x> to the
   person, and wait for their sign-off before writing it."

## Commit plan

| # | Commit message | What it covers | Status |
| --- | --- | --- | --- |
| 1 | `feat(<scope>): <subject> (TKT-NN)` | <the behaviour or files it changes> | |

## Post-commit testing

| # | Check | How | Status |
| --- | --- | --- | --- |
| 1 | <what must work end to end> | <the steps to run it, and what you should see> | |

## Acceptance criteria

- [ ] The person signed off <x>
- [ ] <an outcome someone else could check>
```

- **Title:** imperative and in sentence case, such as "Build a recipe scaler".
- **Status:** `backlog`, `in-progress` or `done`. A new ticket is always `backlog`, and logging one never changes another ticket's status.
- **Sign-off points:** every decision the person makes before work goes on, such as a name, a data format or the language. If the instructions don't name a decision, the agent ends up making it.
- **Commit plan:** one row per commit, in landing order, each with its full commit message as `AGENTS.md` describes. Leave the Status column empty: `start-ticket` sets it to ✅ once the person says that commit has landed.
- **Post-commit testing:** end-to-end checks of the finished work, run once every commit has landed. Leave the Status column empty: `start-ticket` sets it to ✅ once the person confirms the check passed.
- **Acceptance criteria:** outcomes someone else could check, unticked, including each sign-off.
- **Dependencies:** list only tickets that really must be done first, since `start-ticket` stops until they are.
- **Raised from another ticket:** say so in the description, "Raised while working TKT-NN", and why.
- **Short:** someone should be able to read the ticket in under a minute.
