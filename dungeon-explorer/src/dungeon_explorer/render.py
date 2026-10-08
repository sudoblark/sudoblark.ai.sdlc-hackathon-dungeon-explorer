"""Draws the game as text: pure functions that turn the model into lines."""

from dungeon_explorer.game import Game
from dungeon_explorer.level import Point

VIEW_WIDTH = 31
VIEW_HEIGHT = 15
PLAYER = "@"
STAIRS_DOWN = ">"
UNSEEN = " "


def draw_view(
    game: Game, width: int = VIEW_WIDTH, height: int = VIEW_HEIGHT
) -> list[str]:
    """The tiles around the player at full scale, with the player in the middle.

    Only explored tiles are drawn. Anything unexplored, or past the edge of
    the level, is blank. Every line is exactly `width` characters long.
    """
    player_x, player_y = game.player.position
    left = player_x - width // 2
    top = player_y - height // 2
    return [
        "".join(_glyph(game, (x, y)) for x in range(left, left + width))
        for y in range(top, top + height)
    ]


def _glyph(game: Game, point: Point) -> str:
    """What to draw at `point`: the player, else what's on the floor, else the tile."""
    if point == game.player.position:
        return PLAYER
    level = game.level
    x, y = point
    on_level = 0 <= x < level.width and 0 <= y < level.height
    if not on_level or point not in game.explored:
        return UNSEEN
    if point in level.items:
        return level.items[point].glyph
    if point == level.stairs_down:
        return STAIRS_DOWN
    return level.tile(x, y)
