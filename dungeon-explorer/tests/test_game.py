import pytest

from dungeon_explorer.game import Game, Player
from dungeon_explorer.generate import generate_level
from dungeon_explorer.level import Direction, Item, Level, Point, Tile

POTION = Item("potion", "!")
GOLD = Item("gold", "$")


def _level(*rows: str, items: dict[Point, Item] | None = None) -> Level:
    """A hand-built level from rows of # and ., with only `items` placed on it."""
    return Level(
        tiles=[[Tile(glyph) for glyph in row] for row in rows],
        rooms=[],
        player_start=(0, 0),
        stairs_down=(0, 0),
        items=dict(items or {}),
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
    assert game.player.inventory == []
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


def test_stepping_onto_an_item_picks_it_up():
    level = _level("#####", "#...#", "#####", items={(2, 1): POTION})
    game = _game(level, position=(1, 1))

    game.move(Direction.EAST)

    assert game.player.inventory == [POTION]
    assert (2, 1) not in game.level.items
    assert game.message == "You pick up the potion."


def test_the_inventory_lists_items_in_the_order_they_were_picked_up():
    level = _level("#####", "#...#", "#####", items={(2, 1): GOLD, (3, 1): POTION})
    game = _game(level, position=(1, 1))

    game.move(Direction.EAST)
    game.move(Direction.EAST)

    assert game.player.inventory == [GOLD, POTION]
    assert game.level.items == {}


def test_stepping_back_onto_an_emptied_tile_picks_up_nothing_more():
    level = _level("#####", "#...#", "#####", items={(2, 1): POTION})
    game = _game(level, position=(1, 1))
    game.move(Direction.EAST)
    game.move(Direction.WEST)

    game.move(Direction.EAST)

    assert game.player.inventory == [POTION]
    assert game.message == ""
