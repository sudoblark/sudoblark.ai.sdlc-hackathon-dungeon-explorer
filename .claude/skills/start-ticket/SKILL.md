---
name: start-ticket
description: Starts or resumes a ticket from work/, building its commit plan one commit at a time. Use when the person gives a ticket number to work on.
argument-hint: TKT-NN
disable-model-invocation: true
---

# Start a ticket

Ticket: $ARGUMENTS

The ticket is the file in `work/` whose name starts with this number. If no number was given, ask for one.

1. **Read `AGENTS.md` and follow it.** If it conflicts with these steps, these steps win.
2. **Read the ticket.** Check every ticket it depends on has `status: done`. If one doesn't, stop and say so.
3. **Set its `status` to `in-progress`.** The person commits that with the first planned commit.
4. **Follow its agent instructions,** and stop at every sign-off point they name.
5. **Work only the first row of the commit plan whose Status isn't ✅.** Build that scope, run the project's checks and show the results, propose the commit message, and stop.
6. **Iterate until you're both happy.** If you have concerns, say so; don't just agree. The person makes the commit and decides what goes in it.
7. **When the person says it has landed, set that row's Status to ✅,** then start the next row. The person commits the ✅ with the next planned commit. Only their word earns it, because it's how a fresh session knows where to pick up.
8. **Never grow the current commit.** Work that turns up and belongs to this ticket becomes a new row in the plan, with the reason it's needed. Work that doesn't belong goes in a new ticket, through the `log-ticket` skill. Either way, the plan changes before the work does.
9. **Ticket edits outside a planned commit are their own commit,** such as a plan change or a new ticket. Propose a `docs(work): <what changed> (TKT-NN)` message for each one straight away.
10. **When every commit row is ✅, work through the post-commit testing, one check at a time.** Run what you can and show the output, and walk the person through anything they need to try by hand. Set a check's Status to ✅ only when the person confirms it passed. A failure becomes a new row in the commit plan that names its cause, and testing resumes once that commit has landed.
11. **When every commit and check is ✅,** tick the acceptance criteria you've seen met, set `status: done`, and draft the pull request at the end of the ticket in the shape below. Propose `docs(work): close TKT-NN (TKT-NN)` for the person to commit, with the testing ✅ marks, and stop.

## Pull request shape

Someone who never saw the chat should be able to review the work from the ticket, this pull request and the git log alone.

```markdown
## Pull request

**Title:** `<type>(<scope>): <what the ticket delivers> (TKT-NN)`

<One paragraph: what changed and why, and what it deliberately leaves out.>

- **<Area>:** <what changed, in one line>

**Testing:** <what was run and seen to pass, and what a reviewer should try by hand.>

Fixes TKT-NN
```
