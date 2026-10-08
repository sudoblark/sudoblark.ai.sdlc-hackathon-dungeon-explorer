---
status: backlog
---
## Description

A turn-based dungeon explorer drawn in ASCII in the terminal. Each level is generated from a seed: rooms joined by corridors, a few items to pick up, and stairs down to the next level. The player moves one step per command, carries an inventory, and has a mini-map showing the parts of the level they've explored. The core is the generation and the map, with combat as a stretch goal for teams with time to spare. The same seed always generates the same dungeon, which is what makes it testable.

## Agent instructions

1. Ask the person which language, test runner and linter to use, and what to call the project's folder. Wait for their answers.
2. Propose a commit plan, and the post-commit tests that prove the finished project works, as rows in the tables below. Commits go in landing order. The first commit sets up the folder with its test runner and linter, and each later commit adds one behaviour with its tests. Wait for the person's sign-off, then propose `docs(work): plan TKT-05 (TKT-05)` for them to commit.
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
- [ ] Each level is generated from a seed, with rooms joined by corridors, items to pick up, and stairs down to the next level
- [ ] The same seed always generates the same dungeon
- [ ] The player moves one step per command, and can't walk through walls
- [ ] Items picked up go into an inventory, which the player can list
- [ ] A mini-map shows the parts of the level the player has explored

## Stretch goals

Once every acceptance criterion is met, a team with time to spare can add these to the plan as new commits:

- Monsters that chase the player when they can see them
- Attacking a monster by walking into it
- Hit points, and game over when they reach zero
