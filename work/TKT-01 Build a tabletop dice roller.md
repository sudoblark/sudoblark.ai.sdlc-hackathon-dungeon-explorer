---
status: backlog
---
## Description

A command-line dice roller for tabletop games. It takes standard dice notation, rolls it, and shows the working, so a player can see why they rolled 14 and not just that they did. It covers plain rolls such as `3d6`, modifiers such as `1d20+5`, and keeping the best or worst dice, such as `4d6kh3` for character stats or `2d20kh1` for advantage. Rolls can be seeded, so the same seed always gives the same result, which is what makes a dice roller testable.

## Agent instructions

1. Ask the person which language, test runner and linter to use, and what to call the project's folder. Wait for their answers.
2. Propose a commit plan, and the post-commit tests that prove the finished project works, as rows in the tables below. Commits go in landing order. The first commit sets up the folder with its test runner and linter, and each later commit adds one behaviour with its tests. Wait for the person's sign-off, then propose `docs(work): plan TKT-01 (TKT-01)` for them to commit.
3. Work the plan one row at a time.

## Commit plan

| # | Commit message | What it covers | Status |
| --- | --- | --- | --- |

## Post-commit testing

| # | Check | How | Status |
| --- | --- | --- | --- |

## Acceptance criteria

- [ ] The person signed off the language, the tooling and the folder name
- [ ] The person signed off the commit plan
- [ ] `3d6`, `1d20+5` and `4d6kh3` each show every die rolled, which ones count, and the total
- [ ] The same seed always gives the same rolls
- [ ] Notation it can't read gets a clear error, not a crash

## Stretch goals

Once every acceptance criterion is met, a team with time to spare can add these to the plan as new commits:

- Exploding dice, such as `3d6!`, where a die that rolls its maximum adds another die
- Several groups in one roll, such as `2d6+1d8+3`
- The minimum, maximum and average of a roll, and a chart of how likely each total is, without rolling it
