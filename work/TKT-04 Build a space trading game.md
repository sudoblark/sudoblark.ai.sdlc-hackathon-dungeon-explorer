---
status: backlog
---
## Description

A turn-based trading game in the terminal, in the spirit of the classic space trading games. The player flies between a handful of planets, buys cargo where it's cheap, sells it where it's dear, and tries to finish with the most credits in a fixed number of turns. Prices shift every turn from a seeded random generator, so a game can be replayed exactly, which is what makes it testable.

## Agent instructions

1. Ask the person which language, test runner and linter to use, and what to call the project's folder. Wait for their answers.
2. Propose a commit plan, and the post-commit tests that prove the finished project works, as rows in the tables below. Commits go in landing order. The first commit sets up the folder with its test runner and linter, and each later commit adds one behaviour with its tests. Wait for the person's sign-off, then propose `docs(work): plan TKT-04 (TKT-04)` for them to commit.
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
- [ ] At least four planets and three kinds of cargo, with prices that change every turn
- [ ] `buy`, `sell`, `travel` and `status` commands, with a limit on how much the hold carries
- [ ] The game ends after a fixed number of turns and shows the final credits
- [ ] The same seed replays the same prices
- [ ] A trade that isn't possible gets a clear reply, not a crash

## Stretch goals

Once every acceptance criterion is met, a team with time to spare can add these to the plan as new commits:

- Random events between planets, such as pirates or a market crash, from the same seed
- Ship upgrades, such as a bigger hold or faster engines, bought with credits
- A high-score table kept between games
