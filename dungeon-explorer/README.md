# dungeon-explorer

A turn-based dungeon explorer drawn in ASCII in the terminal. Each level is generated from a seed, so the same seed always gives the same dungeon.

## Setting up

You need [uv](https://docs.astral.sh/uv/). It installs a suitable Python (3.12 or later) if you don't have one. From this folder:

```bash
uv sync
```

## How to play

Start the game from this folder:

```bash
uv run dungeon-explorer
```

It opens on a title screen: `w` and `s` move between New game and Exit, and Enter picks one. New game asks for a seed. Type one and press Enter to play that dungeon, or leave it blank for a random one. Either way, the seed is shown at the top of the screen, so you can play the same dungeon again. To have a seed filled in for you, start with one:

```bash
uv run dungeon-explorer --seed 42
```

Each dungeon has between 3 and 7 floors, depending on its seed, and the top of the screen shows which one you're on, such as `Level 2 of 5`. Find the stairs on every floor to go deeper: the last floor's stairs lead out of the dungeon, and out is how you win.

In a game, press a key; there's no need to press Enter:

| Key | What it does |
| --- | --- |
| `w` `a` `s` `d` | Move one step north, west, south or east |
| `>` | Go down the stairs, when you're standing on them |
| `i` | Look at your inventory |
| `l` | Read every message so far, scrolling with `w` and `s` |
| `c` | Clear the messages |
| `?` | Show the help |
| `q` | Leave the game for the title screen, after asking you to press `y` |

The left panel shows the area around you, and the right panel is a mini-map of the whole level at half size, with a key to the symbols beside it. Both show only what you've explored: entering a room reveals all of it, and corridors are mapped as you walk them. Walk onto an item to pick it up. The newest three messages show under the map, and a message that repeats is counted rather than repeated.

| Symbol | What it is |
| --- | --- |
| `@` | You |
| `#` | Wall |
| `.` | Floor |
| `>` | Stairs down |
| `!` `$` `?` `)` | A potion, gold, a scroll or a dagger |

## Running the checks

```bash
uv run pytest
uv run ruff check
uv run ruff format --check
```
