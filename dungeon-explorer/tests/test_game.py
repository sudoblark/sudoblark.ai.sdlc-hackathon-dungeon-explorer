import pytest
from helpers import game_on, level_from

from dungeon_explorer.game import Game
from dungeon_explorer.generate import generate_level
from dungeon_explorer.level import Direction, Item, Point, Room

POTION = Item("potion", "!")
GOLD = Item("gold", "$")


ROOM = level_from(
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
    game = game_on(ROOM, position=(2, 2))

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
    game = game_on(ROOM, position=start)

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
    open_ground = level_from(
        "...",
        "...",
        "...",
    )
    game = game_on(open_ground, position=start)

    game.move(direction)

    assert game.player.position == start
    assert game.message == "A wall is in the way."


def test_a_step_clears_the_last_message():
    game = game_on(ROOM, position=(1, 1))
    game.move(Direction.NORTH)

    game.move(Direction.SOUTH)

    assert game.player.position == (1, 2)
    assert game.message == ""


def test_stepping_onto_an_item_picks_it_up():
    level = level_from("#####", "#...#", "#####", items={(2, 1): POTION})
    game = game_on(level, position=(1, 1))

    game.move(Direction.EAST)

    assert game.player.inventory == [POTION]
    assert (2, 1) not in game.level.items
    assert game.message == "You pick up the potion."


def test_the_inventory_lists_items_in_the_order_they_were_picked_up():
    level = level_from("#####", "#...#", "#####", items={(2, 1): GOLD, (3, 1): POTION})
    game = game_on(level, position=(1, 1))

    game.move(Direction.EAST)
    game.move(Direction.EAST)

    assert game.player.inventory == [GOLD, POTION]
    assert game.level.items == {}


def test_stepping_back_onto_an_emptied_tile_picks_up_nothing_more():
    level = level_from("#####", "#...#", "#####", items={(2, 1): POTION})
    game = game_on(level, position=(1, 1))
    game.move(Direction.EAST)
    game.move(Direction.WEST)

    game.move(Direction.EAST)

    assert game.player.inventory == [POTION]
    assert game.message == ""


def _on_the_stairs(seed: int) -> Game:
    """A new game for `seed`, with the player moved onto the stairs down."""
    game = Game.new(seed)
    game.player.position = game.level.stairs_down
    return game


def test_going_down_the_stairs_starts_the_next_level():
    game = _on_the_stairs(seed=42)

    game.descend()

    assert game.depth == 2
    assert game.level == generate_level(42, depth=2)
    assert game.player.position == game.level.player_start
    assert game.message == "You go down the stairs to level 2."


def test_each_flight_of_stairs_goes_one_level_deeper():
    game = _on_the_stairs(seed=42)
    game.descend()
    game.player.position = game.level.stairs_down

    game.descend()

    assert game.depth == 3
    assert game.level == generate_level(42, depth=3)


def test_going_down_the_stairs_keeps_the_inventory():
    game = _on_the_stairs(seed=42)
    game.player.inventory = [POTION, GOLD]

    game.descend()

    assert game.player.inventory == [POTION, GOLD]


def test_the_next_level_is_the_same_whatever_happened_on_this_one():
    straight_down = _on_the_stairs(seed=42)
    wandered = Game.new(seed=42)
    # Seed 42 has a potion at (40, 13): walk around, then step onto it.
    for direction in Direction:
        wandered.move(direction)
    wandered.player.position = (41, 13)
    wandered.move(Direction.WEST)
    assert wandered.player.inventory == [POTION]
    wandered.player.position = wandered.level.stairs_down

    straight_down.descend()
    wandered.descend()

    assert wandered.level == straight_down.level


def test_going_down_is_refused_away_from_the_stairs():
    game = Game.new(seed=42)
    level = game.level
    start = game.player.position
    assert start != level.stairs_down

    game.descend()

    assert game.depth == 1
    assert game.level is level
    assert game.player.position == start
    assert game.message == "There are no stairs down here."


# Two rooms joined by a corridor through doors at (4, 2) and (6, 2).
WEST_ROOM = Room(x=1, y=1, width=3, height=3)
EAST_ROOM = Room(x=7, y=1, width=3, height=3)
TWO_ROOMS = level_from(
    "###########",
    "#...###...#",
    "#.........#",
    "#...###...#",
    "###########",
    rooms=[WEST_ROOM, EAST_ROOM],
)


def _seen(room: Room) -> set[Point]:
    return set(room.tiles()) | set(room.walls())


def test_the_room_the_player_starts_in_is_explored_walls_and_all():
    game = game_on(TWO_ROOMS, position=(2, 2))

    assert _seen(WEST_ROOM) <= game.explored
    assert not set(EAST_ROOM.tiles()) & game.explored


def test_walking_a_corridor_reveals_the_tiles_around_each_step():
    game = game_on(TWO_ROOMS, position=(2, 2))

    for _ in range(3):
        game.move(Direction.EAST)

    assert game.player.position == (5, 2)
    assert {(6, 1), (6, 2), (6, 3)} <= game.explored
    assert not set(EAST_ROOM.tiles()) & game.explored


def test_stepping_into_a_room_reveals_all_of_it():
    game = game_on(TWO_ROOMS, position=(2, 2))

    for _ in range(5):
        game.move(Direction.EAST)

    assert game.player.position == (7, 2)
    assert _seen(EAST_ROOM) <= game.explored


def test_rooms_the_player_hasnt_visited_stay_unexplored():
    game = Game.new(seed=42)

    start_room, *other_rooms = game.level.rooms
    assert _seen(start_room) <= game.explored
    for room in other_rooms:
        assert not set(room.tiles()) & game.explored, room


def test_a_new_level_starts_with_only_its_first_room_explored():
    game = _on_the_stairs(seed=42)

    game.descend()

    assert game.explored == _seen(game.level.rooms[0])


def test_exploring_stops_at_the_edge_of_the_level():
    open_ground = level_from(
        "...",
        "...",
    )

    game = game_on(open_ground, position=(0, 0))

    assert game.explored == {(0, 0), (1, 0), (0, 1), (1, 1)}
