"""Draws the game as text: pure functions that turn the model into lines."""

from dungeon_explorer.game import Game
from dungeon_explorer.level import Monster, Point, Tile

# Each side of the square of tiles one mini-map character stands for.
MINI_MAP_SCALE = 2
PLAYER = "@"
STAIRS_DOWN = ">"
UNSEEN = " "


def draw_view(
    game: Game, width: int | None = None, height: int | None = None
) -> list[str]:
    """The tiles around the player at full scale, with the player in the middle.

    Only explored tiles, and monsters in sight, are drawn. Anything else, or
    anything past the edge of the level, is blank. Every line is exactly
    `width` characters long. The size comes from the game's settings unless
    it's given.
    """
    width = width or game.settings.view_width
    height = height or game.settings.view_height
    player_x, player_y = game.player.position
    left = player_x - width // 2
    top = player_y - height // 2
    in_sight = _in_sight(game)
    return [
        "".join(_glyph(game, (x, y), in_sight) for x in range(left, left + width))
        for y in range(top, top + height)
    ]


def draw_mini_map(game: Game) -> list[str]:
    """The whole level at half scale, one character for each 2x2 block of tiles.

    Only explored tiles count, so the map fills in as the player explores.
    Every line is the same length.
    """
    level = game.level
    in_sight = _in_sight(game)
    return [
        "".join(
            _block_glyph(game, (x, y), in_sight)
            for x in range(0, level.width, MINI_MAP_SCALE)
        )
        for y in range(0, level.height, MINI_MAP_SCALE)
    ]


def _in_sight(game: Game) -> dict[Point, Monster]:
    """The monsters the player can see, by where they are. Only these are drawn."""
    return {monster.position: monster for monster in game.monsters_in_sight()}


def _glyph(game: Game, point: Point, in_sight: dict[Point, Monster]) -> str:
    """What to draw at `point`: the player, else a monster in sight, else
    what's on the floor, else the tile."""
    if point == game.player.position:
        return PLAYER
    if point in in_sight:
        return in_sight[point].glyph
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


def _block_glyph(game: Game, corner: Point, in_sight: dict[Point, Monster]) -> str:
    """What the mini-map shows for the block of tiles with `corner` at its top left.

    The player, else a monster in sight, else the stairs if they've been
    seen, else the first item seen, else floor if any explored tile is floor,
    else wall if any tile is explored, else blank.
    """
    level = game.level
    left, top = corner
    block = [
        (x, y)
        for y in range(top, min(top + MINI_MAP_SCALE, level.height))
        for x in range(left, min(left + MINI_MAP_SCALE, level.width))
    ]
    if game.player.position in block:
        return PLAYER
    for point in block:
        if point in in_sight:
            return in_sight[point].glyph
    seen = [point for point in block if point in game.explored]
    if level.stairs_down in seen:
        return STAIRS_DOWN
    for point in seen:
        if point in level.items:
            return level.items[point].glyph
    if any(level.tile(*point) is Tile.FLOOR for point in seen):
        return Tile.FLOOR
    if seen:
        return Tile.WALL
    return UNSEEN
