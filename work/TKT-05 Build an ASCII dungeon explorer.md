---
status: in-progress
---
## Description

A turn-based dungeon explorer drawn in ASCII in the terminal. Each level is generated from a seed: rooms joined by corridors, a few items to pick up, and stairs down to the next level. The player moves one step per command, carries an inventory, and has a mini-map showing the parts of the level they've explored. The core is the generation and the map, with combat as a stretch goal for teams with time to spare. The same seed always generates the same dungeon, which is what makes it testable.

## Agent instructions

1. Ask the person which language, test runner and linter to use, and what to call the project's folder. Wait for their answers.
2. Propose a commit plan, and the post-commit tests that prove the finished project works, as rows in the tables below. Commits go in landing order. The first commit sets up the folder with its test runner and linter, and each later commit adds one behaviour with its tests. Wait for the person's sign-off, then propose `docs(work): plan TKT-05 (TKT-05)` for them to commit.
3. Work the plan one row at a time.

## Decisions

- **Python, pytest and ruff, in `dungeon-explorer/`.** The person chose these. `random.Random(seed)` makes generation repeatable with no dependencies.
- **uv manages the environment,** through `pyproject.toml` and a committed `uv.lock`. It's already installed, and `uv run` gives everyone the same pytest and ruff versions. The project needs Python 3.12 or later, so hackathon machines without the newest Python can still run it, and the checks are run on both 3.12 and 3.14.
- **Line-based commands:** type a command and press Enter. `input()` is easy to drive from tests and works in any terminal. curses would give single keypresses, but it's hard to test and Windows doesn't ship it. The cost is pressing Enter after every move.
- **A pure core, with input and output only in the CLI.** Generation, the game rules and rendering return data or strings, so tests can check exact output without a terminal.
- **Each level's seed comes from the game seed and the depth,** so level N of seed S is always the same, whatever the player did on the levels before it.
- **Items are picked up automatically** when the player steps on them. The acceptance criteria need an inventory, not a pick-up command, and it means one less command.
- **Rogue-style exploration:** entering a room reveals the whole room and its walls, and the eight tiles around the player are always revealed, which maps corridors as the player walks them. This is deterministic and needs no line-of-sight maths.
- **Two views on screen:** a full-scale 31×15 view around the player, and a mini-map of the whole 64×32 level at half scale. Because the level is bigger than the view, the mini-map is the player's only overview of it. Side by side, the two fit in an 80-column terminal.

## Commit plan

| # | Commit message | What it covers | Status |
| --- | --- | --- | --- |
| 1 | `chore(dungeon-explorer): scaffold with pytest and ruff (TKT-05)` | `dungeon-explorer/` containing `pyproject.toml` (managed by uv, with pytest and ruff as dev dependencies and the ruff settings), `uv.lock`, the `src/dungeon_explorer` package, one smoke test, `.gitignore`, and a README explaining how to run the checks. | |
| 2 | `feat(generate): place seeded rooms on a level (TKT-05)` | A `Level` made of wall and floor tiles, and `generate_level(seed, depth)`, which carves non-overlapping rectangular rooms into it. Tests: rooms stay inside the level and never overlap or touch; the same seed and depth always give the same level; different seeds give different levels. | |
| 3 | `feat(generate): join the rooms with corridors (TKT-05)` | L-shaped corridors carved from each room to the next. Tests: a flood fill from the first room reaches every floor tile; the same seed always gives the same corridors. | |
| 4 | `feat(generate): place items, stairs and start (TKT-05)` | The player's start in the first room, stairs down (`>`) in a different room, and a few items on room floors: potion `!`, gold `$`, scroll `?`, dagger `)`. Tests: everything sits on floor and no two share a tile; the stairs aren't in the start room; the same seed always gives the same placement. | |
| 5 | `feat(game): move the player one step at a time (TKT-05)` | A `Game` that holds the level, the player's position and the depth. `move(direction)` steps one tile north, south, east or west; walking into a wall leaves the player in place and gives a message. Tests: every direction, and walls and the level's edges blocking. | |
| 6 | `feat(game): pick up items into an inventory (TKT-05)` | Stepping onto an item takes it off the level and adds it to the inventory, with a message. The inventory lists items in the order they were picked up. Tests: picking up, the listing, and an empty inventory. | |
| 7 | `feat(game): descend the stairs to the next level (TKT-05)` | `descend()` on the stairs generates the level for depth + 1 from the same seed and puts the player at its start, keeping the inventory. Anywhere else, it's refused with a message. Tests: the depth goes up; the inventory is kept; a seed's level 2 is the same whatever happened on level 1; descending off the stairs is refused. | |
| 8 | `feat(game): track the explored tiles (TKT-05)` | Rogue-style exploration, as described under Decisions; a new level starts with nothing explored. Tests: the start room is explored at the start, walking a corridor reveals its neighbours, and unvisited rooms stay unexplored. | |
| 9 | `feat(render): draw the view around the player (TKT-05)` | A 31×15 view, centred on the player at full scale, showing explored tiles, items, stairs and `@`. Anything unexplored or off the level is blank. Tests compare exact strings drawn from a small hand-built level. | |
| 10 | `feat(render): draw the mini-map of explored tiles (TKT-05)` | The whole level at half scale, one character for every 2×2 block of tiles: `@` for the player, `>` for stairs once seen, `.` for explored floor, `#` for explored walls, and blank for everything else. Tests compare exact strings. | |
| 11 | `feat(cli): play the game in the terminal (TKT-05)` | The game loop. It parses commands (`w` `a` `s` `d` to move, `i` inventory, `>` descend, `?` help, `q` quit) and each turn draws the view, the mini-map, the depth, the seed and the last message. It's started with `dungeon-explorer --seed N`; without a seed it picks one and shows it. Adds a "How to play" section to the README. Tests drive the loop with scripted input and check what it prints. | |

## Post-commit testing

| # | Check | How | Status |
| --- | --- | --- | --- |
| 1 | The checks pass on the finished project | In `dungeon-explorer/`, run `uv run pytest`, `uv run ruff check` and `uv run ruff format --check`. All three pass. | |
| 2 | It runs from a fresh clone by following the README | Clone the branch into a temporary folder and follow the README's steps through to `uv run dungeon-explorer --seed 42`. The first screen draws with no errors. | |
| 3 | The same seed always draws the same dungeon | Run `printf 'q\n' \| uv run dungeon-explorer --seed 42` twice and diff the two outputs: they match. With `--seed 43`, the output differs. | |
| 4 | Walls block movement | Play with `--seed 42` and walk into a wall. The `@` doesn't move, and the message says a wall is in the way. | |
| 5 | Picked-up items appear in the inventory | Walk onto an item and see the pick-up message, then enter `i`: the item is listed. | |
| 6 | The stairs lead down | `>` away from the stairs is refused. On the stairs, it draws level 2, the depth shows 2 and the inventory is unchanged. Replaying the same seed gives the same level 2. | |
| 7 | The mini-map shows only the explored parts | At the start, the mini-map shows only the start room. Walking a corridor fills it in behind the player, and the unexplored parts stay blank. | |

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
