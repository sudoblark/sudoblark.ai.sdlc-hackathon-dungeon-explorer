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
- **Model, view and presenter, built from Robert Nystrom's *Game Programming Patterns*.** The person chose this.
  - **Model:** `level`, `generate` and `game` hold the state and the rules, and never print.
  - **View:** `render` is pure functions that turn the model into text.
  - **Presenter:** three of the book's patterns. **Command** (`commands`) turns typed input into objects that act on the model. **State** (`states`) gives each screen (playing, inventory and help) its own drawing and input handling, and returns the next state. The **Game Loop** (`cli`) draws the current state, reads a line and hands it over, until there's no next state.

  Only `cli` reads input or prints, so tests can check exact output without a terminal. MVVM was considered and dropped: its ViewModel exists to feed a data-binding framework, which a terminal doesn't have, and a turn-based game redraws the whole screen every turn anyway.
- **Each level's seed comes from the game seed and the depth,** so level N of seed S is always the same, whatever the player did on the levels before it.
- **Rooms are joined through doors in their sides.** The person asked for rooms to be joined from the top, bottom, left or right. The planned L-shaped corridors between room centres sometimes ran along another room's wall and opened up that whole side: 308 times over 200 seeds. So each corridor now runs between two doors, routed around every other room's walls. A room with no route to it is dropped. None were dropped over 2,000 seeds, but the rule guarantees every level can be walked end to end.
- **Items are data:** a frozen `Item(name, glyph)`, with the kinds listed in `generate.py`, so the TOML stretch goal can add new kinds without code changes. The person chose this over an enum or a class for each kind. The stairs are a position on the `Level` rather than a kind of tile, so tiles only describe terrain and every walkable tile is floor.
- **The player is a `Player` object on the `Game`,** holding its position, so the inventory and any later hit points have a home, and monsters can follow the same shape. The person chose this, along with a compass `Direction` (north, east, south, west) in `level.py`, and `Game.new(seed)` for starting a game, which leaves the plain constructor free for tests to build games on small hand-made levels.
- **Items are picked up automatically** when the player steps on them. The acceptance criteria need an inventory, not a pick-up command, and it means one less command.
- **Rogue-style exploration:** entering a room reveals the whole room and its walls, and the eight tiles around the player are always revealed, which maps corridors as the player walks them. This is deterministic and needs no line-of-sight maths.
- **Two views on screen:** a full-scale 31×15 view around the player, and a mini-map of the whole 64×32 level at half scale. Because the level is bigger than the view, the mini-map is the player's only overview of it. Side by side, the two fit in an 80-column terminal.

## Commit plan

| # | Commit message | What it covers | Status |
| --- | --- | --- | --- |
| 1 | `chore(dungeon-explorer): scaffold with pytest and ruff (TKT-05)` | `dungeon-explorer/` containing `pyproject.toml` (managed by uv, with pytest and ruff as dev dependencies and the ruff settings), `uv.lock`, the `src/dungeon_explorer` package, one smoke test, `.gitignore`, and a README explaining how to run the checks. | ✅ |
| 2 | `feat(generate): place seeded rooms on a level (TKT-05)` | A `Level` made of wall and floor tiles, and `generate_level(seed, depth)`, which carves non-overlapping rectangular rooms into it. Tests: rooms stay inside the level and never overlap or touch; the same seed and depth always give the same level; different seeds give different levels. | ✅ |
| 3 | `feat(generate): join the rooms with corridors (TKT-05)` | Corridors join rooms through doors: single tiles in a room's top, bottom, left or right wall, never a corner. Working left to right, each room joins whichever already-joined room is cheapest to reach. The route comes from a shortest-path search that prefers few bends and keeps clear of other rooms' walls. A room that nothing can reach is filled back in and dropped. Tests: a flood fill from the first room reaches every floor tile; corridors meet rooms only through single doors in a side; a boxed-in room is dropped; seed 42's map is pinned. | ✅ |
| 4 | `feat(generate): place items, stairs and start (TKT-05)` | The player's start in the first room, stairs down (`>`) in a different room, and a few items on room floors: potion `!`, gold `$`, scroll `?`, dagger `)`. Tests: everything sits on floor and no two share a tile; the stairs aren't in the start room; the same seed always gives the same placement. | ✅ |
| 5 | `feat(game): move the player one step at a time (TKT-05)` | A `Game` that holds the level, the player's position and the depth. `move(direction)` steps one tile north, south, east or west; walking into a wall leaves the player in place and gives a message. Tests: every direction, and walls and the level's edges blocking. | ✅ |
| 6 | `feat(game): pick up items into an inventory (TKT-05)` | Stepping onto an item takes it off the level and adds it to the inventory, with a message. The inventory lists items in the order they were picked up. Tests: picking up, the listing, and an empty inventory. | ✅ |
| 7 | `feat(game): descend the stairs to the next level (TKT-05)` | `descend()` on the stairs generates the level for depth + 1 from the same seed and puts the player at its start, keeping the inventory. Anywhere else, it's refused with a message. Tests: the depth goes up; the inventory is kept; a seed's level 2 is the same whatever happened on level 1; descending off the stairs is refused. | ✅ |
| 8 | `feat(game): track the explored tiles (TKT-05)` | Rogue-style exploration, as described under Decisions; a new level starts with nothing explored. Tests: the start room is explored at the start, walking a corridor reveals its neighbours, and unvisited rooms stay unexplored. | ✅ |
| 9 | `feat(render): draw the view around the player (TKT-05)` | A 31×15 view, centred on the player at full scale, showing explored tiles, items, stairs and `@`. Anything unexplored or off the level is blank. Tests compare exact strings drawn from a small hand-built level. | ✅ |
| 10 | `feat(render): draw the mini-map of explored tiles (TKT-05)` | The whole level at half scale, one character for every 2×2 block of tiles: `@` for the player, `>` for stairs once seen, an item's own glyph once seen (the person asked for items too; stairs win if they share a block), `.` for explored floor, `#` for explored walls, and blank for everything else. Tests compare exact strings. | ✅ |
| 11 | `feat(generate): keep items clear of the stairs (TKT-05)` | Items never land on the stairs or the eight tiles around them, so the stairs stand alone in the view and on the mini-map. Any two tiles in a 2×2 mini-map block touch, so this also keeps items out of the stairs' block, without tying the generator to the mini-map's scale. The person asked for this after seed 42 put a potion beside its stairs. Tests: no item within one tile of the stairs; no item on a door; seed 42's pinned items and the stairs test that walks to its potion are updated. | ✅ |
| 12 | `feat(commands): turn typed input into commands (TKT-05)` | The Command pattern: `Move(direction)` and `Descend`, each with `execute(game)`, and `parse_command(text)`, which maps `w` `a` `s` `d` and `>` to them and anything else to no command. Tests: each key gives the right command; running a command changes the game just as `move` or `descend` would; unknown input gives no command. | ✅ |
| 13 | `feat(states): add the playing, inventory and help screens (TKT-05)` | The State pattern: each state draws its screen and handles a line of input, returning the next state, or nothing to quit. Playing draws the view and mini-map from `render`, with the depth, the seed and the last message, and runs commands. From Playing, `i` opens the inventory, `?` the help, and `q` quits. Any input on the inventory or help screen goes back to playing. Tests: every transition, and what each screen draws. | ✅ |
| 14 | `feat(cli): run the game loop in the terminal (TKT-05)` | The Game Loop: draw the current state, read a line, hand it over, and stop when there's no next state. It's started with `dungeon-explorer --seed N`; without a seed it picks one and shows it. Adds a "How to play" section to the README. Tests drive the loop with scripted input and check what it prints. | ✅ |

### Stretch goals

Rows 15 to 28 are stretch goals, added once every acceptance criterion was met.

| # | Commit message | What it covers | Status |
| --- | --- | --- | --- |
| 15 | `feat(cli): read single keypresses in a terminal (TKT-05)` | In a terminal, each key acts as soon as it's pressed: `tty.setcbreak` on macOS and Linux, so Ctrl-C still quits, and `msvcrt.getwch` on Windows. When input is piped, the loop still reads lines, so scripted runs and check 3 keep working. "Press Enter" becomes "Press any key". Tests: piped input still drives the loop; the key reader only reads raw keys from a terminal. The raw path is checked by hand. | ✅ |
| 16 | `refactor(states): give each state the game it shows (TKT-05)` | States hold their own game instead of the loop passing one in, so a title screen can start new games and leave finished ones behind. No change in behaviour; the existing tests move to the new shape. | ✅ |
| 17 | `feat(states): add a header and legend to the playing screen (TKT-05)` | The game's title at the top of the playing screen, and a key to every symbol, all within 80 columns. The person chose the title and menu keys on the top line, the level and seed under them, and the legend as a column to the right of the map, which leaves room for monster kinds later. Tests: the exact header and legend lines, and the width. | ✅ |
| 18 | `feat(game): keep a log of messages, with a key to clear it (TKT-05)` | Messages stay in a log instead of each one replacing the last, and the playing screen shows the newest few under the map. The person chose three lines under the map, `c` to clear the log, an `l` screen that scrolls through every message of the game with `w` and `s`, and counting a repeated message, as in `(x3)`, rather than repeating it. The person asked for this while trying row 15. Tests: messages pile up in order, the screen shows the newest, and clearing empties the log. | ✅ |
| 19 | `feat(game): end the dungeon after its last floor (TKT-05)` | Each seed sets how many floors its dungeon has, between a minimum and a maximum (3 and 7 to start; both move to the TOML file in row 27), shown as `Level 2 of 5`. Arriving on the last floor logs that its stairs lead out, and going down them finishes the game instead of generating another level. The person chose seeded floor counts, and the same stairs with a message over a new exit symbol. Tests: floor counts stay in range and are the same for a seed, reaching the last floor, finishing from it, and the status line. | |
| 20 | `feat(states): show a win screen when the dungeon is finished (TKT-05)` | A win screen saying how deep the player went and what they carried out. Any key ends the game until row 21 sends it to the title screen. Tests: the transition and what it draws. | |
| 21 | `feat(states): add a title screen with new game and exit (TKT-05)` | The game opens on a title screen with New Game and Exit. New Game lets the player type their own seed, or take a random one, with `--seed` filling it in; the person asked for this when choosing seeded floor counts. Typing a seed needs a text entry on that screen, since other keys act on a single press. Finishing goes back to the title. The keys, and whether `q` while playing quits or goes to the title, are signed off at this commit. Tests: every transition, and the seed each new game gets. | |
| 22 | `feat(generate): place monsters and show the ones in sight (TKT-05)` | A few seeded monsters on each level, kept out of the start room, drawn only when the player has a clear line of sight to them. Monster kinds and how they're modelled are signed off at this commit. Tests: the placement rules, line of sight through floor and blocked by walls, the drawing, and seed 42's monsters pinned. | |
| 23 | `feat(game): monsters chase the player they can see (TKT-05)` | After each turn, each monster that can see the player steps one tile towards them, never into a wall, another monster or the player. Tests: chasing, staying put out of sight, and being blocked. | |
| 24 | `feat(game): attack a monster by walking into it (TKT-05)` | Walking into a monster hits it instead of moving. Monsters have hit points and are removed at zero, with messages. Whether damage is fixed or rolled from the seed is signed off at this commit. Tests: hitting, killing and the messages. | |
| 25 | `feat(game): monsters hit back and hit points run out (TKT-05)` | The player has hit points, shown on the status line, and a monster next to the player at the end of a turn hits them. Tests: taking damage, the status line, and hit points stopping at zero. | |
| 26 | `feat(states): show a game over screen at zero hit points (TKT-05)` | At zero hit points the game shows a game over screen, and any key goes back to the title. Tests: the transition and what it draws. | |
| 27 | `feat(settings): read the game's settings from a TOML file (TKT-05)` | The level size, rooms, items, monsters, the minimum and maximum number of floors, view size and number of log lines come from a TOML file read with `tomllib`, with today's values as the defaults. The format and the file's location are signed off at this commit. Tests: the defaults, overriding a setting, and rejecting bad values. | |
| 28 | `feat(settings): show which settings a seed was played with (TKT-05)` | A short fingerprint of the settings beside the seed, on screen and in the goodbye line, so a replay can tell it has the same settings. Tests: the same settings give the same fingerprint, and any change gives a different one. | |

## Post-commit testing

| # | Check | How | Status |
| --- | --- | --- | --- |
| 1 | The checks pass on the finished project | In `dungeon-explorer/`, run `uv run pytest`, `uv run ruff check` and `uv run ruff format --check`. All three pass. | ✅ |
| 2 | It runs from a fresh clone by following the README | Clone the branch into a temporary folder and follow the README's steps through to `uv run dungeon-explorer --seed 42`. The first screen draws with no errors. | ✅ |
| 3 | The same seed always draws the same dungeon | Run `printf 'q\n' \| uv run dungeon-explorer --seed 42` twice and diff the two outputs: they match. With `--seed 43`, the output differs. | ✅ |
| 4 | Walls block movement | Play with `--seed 42` and walk into a wall. The `@` doesn't move, and the message says a wall is in the way. | ✅ |
| 5 | Picked-up items appear in the inventory | Walk onto an item and see the pick-up message, then enter `i`: the inventory screen lists the item, and any input goes back to the game. | ✅ |
| 6 | The stairs lead down | `>` away from the stairs is refused. On the stairs, it draws level 2, the depth shows 2 and the inventory is unchanged. Replaying the same seed gives the same level 2. | ✅ |
| 7 | The mini-map shows only the explored parts | At the start, the mini-map shows only the start room. Walking a corridor fills it in behind the player, and the unexplored parts stay blank. | ✅ |

### Stretch goals

Checks 8 to 17 test the stretch goals, once rows 15 to 28 have landed.

| # | Check | How | Status |
| --- | --- | --- | --- |
| 8 | Keys act without Enter in a terminal | Run `uv run dungeon-explorer --seed 42` in a terminal. `w` `a` `s` `d` move straight away, `i` and `?` open their screens, any key goes back, and Ctrl-C quits cleanly. Piped input, as in check 3, still works. | |
| 9 | The playing screen has a header and legend | The title shows at the top, every symbol on screen is in the legend, and the screen fits an 80-column terminal. | |
| 10 | The message log keeps and clears messages | Walk into a wall, then pick something up: both messages stay on screen, newest last. The clear key empties the log. | |
| 11 | The title screen starts and exits games | The game opens on the title. New Game starts a game, and Exit quits. With `--seed 42`, the new game is seed 42, and typing a seed on New Game plays that seed instead. | |
| 12 | The dungeon can be finished | The status shows `Level 1 of N`, where N is between the minimum and maximum and is the same every time for a seed. Arriving on the last floor says its stairs lead out, and going down them shows the win screen, then the title. | |
| 13 | Monsters appear and chase | Monsters only show when they're in sight, and step towards the player when they can see them. Out of sight, they stay put. | |
| 14 | Monsters can be fought | Walking into a monster hits it, and enough hits kill it. | |
| 15 | Monsters hurt back, and the game can be lost | Standing next to a monster costs hit points, shown on the status line. At zero, the game over screen shows, then the title. | |
| 16 | Settings change the game | Changing a setting in the TOML file, such as fewer floors or a smaller level, changes the game, and the fingerprint beside the seed changes with it. | |
| 17 | The original checks still hold | Re-run checks 1 to 3 on the finished stretch goals, with input that starts a game from the title screen first. | |

## Acceptance criteria

- [x] The person signed off the language, the tooling and the folder name
- [x] The person signed off the commit plan
- [x] Each level is generated from a seed, with rooms joined by corridors, items to pick up, and stairs down to the next level
- [x] The same seed always generates the same dungeon
- [x] The player moves one step per command, and can't walk through walls
- [x] Items picked up go into an inventory, which the player can list
- [x] A mini-map shows the parts of the level the player has explored

## Stretch goals

Once every acceptance criterion is met, a team with time to spare can add these to the plan as new commits:

- Monsters that chase the player when they can see them
- Attacking a monster by walking into it
- Hit points, and game over when they reach zero
- Settings such as the level size, the rooms, the view size and the items, read from a TOML file with `tomllib`. A seed then only reproduces a dungeon with the same settings, so this also needs a way for a replay to know which settings were used.

The person added these after play-testing:

- Moving and acting on a single keypress, without pressing Enter. This reverses the line-based decision, so it needs raw terminal input (`termios` on macOS and Linux, `msvcrt` on Windows) and a new way to script input in tests.
- A header and a legend on the playing screen: the game's title at the top, and a key to the symbols beside the map.
- A title screen with New Game and Exit, as a new state that comes before playing.
- A fixed number of floors, with the total in the legend (`Level 2 of 5`) and a way to finish on the last one. At the moment the dungeon goes on forever, so there's nothing to complete.
- Saving and loading from a menu. Levels regenerate from the seed, so a save only needs the seed, the depth, the player's position and inventory, the explored tiles, and which items have been picked up on the current level.
- A log that keeps past messages instead of replacing them, with a key to clear it. The person added this while trying row 15.

The person chose every stretch goal except saving and loading, planned as rows 15 to 28, with checks 8 to 17.
