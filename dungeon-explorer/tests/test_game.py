import pytest

from dungeon_explorer.game import Game, Player
from dungeon_explorer.generate import generate_level
from dungeon_explorer.level import Direction, Level, Point, Tile


def _level(*rows: str) -> Level:
    """A hand-built level from rows of # and ., with nothing placed on it."""
    return Level(
        tiles=[[Tile(glyph) for glyph in row] for row in rows],
        rooms=[],
        player_start=(0, 0),
        stairs_down=(0, 0),
        items={},
    )


def _game(level: Level, position: Point) -> Game:
    return Game(seed=0, level=level, player=Player(position))


ROOM = _level(
    "#####",
    "#...#",
    "#...#",
    "#...#",
    "#####",
)


def test_a_new_game_starts_at_the_start_of_level_one():
    game = Game.new(seed=42)

    assert game.seed == 42
    assert game.depth == 1
    assert game.level == generate_level(42, depth=1)
    assert game.player.position == game.level.player_start
    assert game.message == ""


@pytest.mark.parametrize(
    ("direction", "position"),
    [
        (Direction.NORTH, (2, 1)),
        (Direction.EAST, (3, 2)),
        (Direction.SOUTH, (2, 3)),
        (Direction.WEST, (1, 2)),
    ],
)
def test_moving_steps_one_tile_in_that_direction(direction, position):
    game = _game(ROOM, position=(2, 2))

    game.move(direction)

    assert game.player.position == position


@pytest.mark.parametrize(
    ("start", "direction"),
    [
        ((2, 1), Direction.NORTH),
        ((3, 2), Direction.EAST),
        ((2, 3), Direction.SOUTH),
        ((1, 2), Direction.WEST),
    ],
)
def test_walls_block_the_player(start, direction):
    game = _game(ROOM, position=start)

    game.move(direction)

    assert game.player.position == start
    assert game.message == "A wall is in the way."


@pytest.mark.parametrize(
    ("start", "direction"),
    [
        ((1, 0), Direction.NORTH),
        ((2, 1), Direction.EAST),
        ((1, 2), Direction.SOUTH),
        ((0, 1), Direction.WEST),
    ],
)
def test_the_edge_of_the_level_blocks_the_player(start, direction):
    # No border of wall, so only the edge stops the player walking off.
    open_ground = _level(
        "...",
        "...",
        "...",
    )
    game = _game(open_ground, position=start)

    game.move(direction)

    assert game.player.position == start
    assert game.message == "A wall is in the way."


def test_a_step_clears_the_last_message():
    game = _game(ROOM, position=(1, 1))
    game.move(Direction.NORTH)

    game.move(Direction.SOUTH)

    assert game.player.position == (1, 2)
    assert game.message == ""
