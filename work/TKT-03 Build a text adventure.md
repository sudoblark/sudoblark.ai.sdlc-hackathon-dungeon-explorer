---
status: backlog
---
## Description

A small text adventure in the style of the classic interactive fiction games: about five rooms, a few items and a locked door, played by typing commands such as `look`, `go north`, `take lamp` and `use key`. The world loads from a data file, so anyone can write a new adventure without touching the code. The game logic is kept apart from the terminal, so it can be tested without anyone typing.

## Agent instructions

1. Ask the person which language, test runner and linter to use, what to call the project's folder, and what the adventure is about. Wait for their answers.
2. Propose a commit plan, and the post-commit tests that prove the finished project works, as rows in the tables below. Commits go in landing order. The first commit sets up the folder with its test runner and linter, and each later commit adds one behaviour with its tests. Wait for the person's sign-off, then propose `docs(work): plan TKT-03 (TKT-03)` for them to commit.
3. Work the plan one row at a time.

## Commit plan

| # | Commit message | What it covers | Status |
| --- | --- | --- | --- |

## Post-commit testing

| # | Check | How | Status |
| --- | --- | --- | --- |

## Acceptance criteria

- [ ] The person signed off the language, the tooling, the folder name and the adventure's theme
- [ ] The person signed off the commit plan
- [ ] Rooms, exits, items and the locked door load from a data file, not from code
- [ ] `look`, `go <direction>`, `take <item>`, `inventory` and `use <item>` work
- [ ] The door opens only with its key, and reaching the last room wins the game
- [ ] The game logic is tested without typing into the terminal
- [ ] A command it doesn't understand gets a helpful reply, not a crash

## Stretch goals

Once every acceptance criterion is met, a team with time to spare can add these to the plan as new commits:

- Saving and loading a game
- Characters to talk to, with simple dialogue loaded from the data file
- Puzzles that need two items combined
