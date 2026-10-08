"""Builders for hand-made levels and games, shared by the tests."""

from dungeon_explorer.game import Game, Player
from dungeon_explorer.level import Item, Level, Point, Room, Tile


def level_from(
    *rows: str,
    rooms: list[Room] | None = None,
    items: dict[Point, Item] | None = None,
    stairs_down: Point = (0, 0),
) -> Level:
    """A hand-built level from rows of # and ., with only what's passed placed on it."""
    return Level(
        tiles=[[Tile(glyph) for glyph in row] for row in rows],
        rooms=list(rooms or []),
        player_start=(0, 0),
        stairs_down=stairs_down,
        items=dict(items or {}),
    )


def game_on(level: Level, position: Point) -> Game:
    """A game on `level`, with the player standing at `position`."""
    return Game(seed=0, level=level, player=Player(position))
