# dungeon-explorer

A turn-based dungeon explorer drawn in ASCII in the terminal. Each level is generated from a seed, so the same seed always gives the same dungeon.

## Setting up

You need [uv](https://docs.astral.sh/uv/). It installs a suitable Python (3.12 or later) if you don't have one. From this folder:

```bash
uv sync
```

## Running the checks

```bash
uv run pytest
uv run ruff check
uv run ruff format --check
```
