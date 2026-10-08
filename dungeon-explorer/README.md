# dungeon-explorer

A turn-based dungeon explorer drawn in ASCII in the terminal. Each level is generated from a seed, so the same seed always gives the same dungeon.

## Setting up

You need [uv](https://docs.astral.sh/uv/). It installs a suitable Python (3.12 or later) if you don't have one. From this folder:

```bash
uv sync
```

## How to play

Start a game from this folder. Pass a seed to play a particular dungeon, or leave it out for a random one. Either way, the seed is shown at the top of the screen, so you can play the same dungeon again.

```bash
uv run dungeon-explorer --seed 42
```

Press a key; there's no need to press Enter:

| Key | What it does |
| --- | --- |
| `w` `a` `s` `d` | Move one step north, west, south or east |
| `>` | Go down the stairs, when you're standing on them |
| `i` | Look at your inventory |
| `?` | Show the help |
| `q` | Quit |

The left panel shows the area around you, and the right panel is a mini-map of the whole level at half size. Both show only what you've explored: entering a room reveals all of it, and corridors are mapped as you walk them. Walk onto an item to pick it up.

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
