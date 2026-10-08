import pytest
from helpers import game_on, level_from

from dungeon_explorer.game import Game, Message
from dungeon_explorer.generate import floor_count, generate_level
from dungeon_explorer.level import Direction, Item, Monster, Point, Room

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
    assert game.log == []


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
    assert str(game.log[-1]) == "A wall is in the way."


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
    assert str(game.log[-1]) == "A wall is in the way."


def test_a_plain_step_adds_nothing_to_the_log():
    game = game_on(ROOM, position=(1, 1))
    game.move(Direction.NORTH)

    game.move(Direction.SOUTH)

    assert game.player.position == (1, 2)
    assert game.log == [Message("A wall is in the way.")]


def test_stepping_onto_an_item_picks_it_up():
    level = level_from("#####", "#...#", "#####", items={(2, 1): POTION})
    game = game_on(level, position=(1, 1))

    game.move(Direction.EAST)

    assert game.player.inventory == [POTION]
    assert (2, 1) not in game.level.items
    assert str(game.log[-1]) == "You pick up the potion."


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
    assert game.log == [Message("You pick up the potion.")]


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
    assert str(game.log[-1]) == "You go down the stairs to level 2."


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
    # Seed 42 has a potion at (43, 13): walk around, then step onto it.
    for direction in Direction:
        wandered.move(direction)
    wandered.player.position = (44, 13)
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
    assert str(game.log[-1]) == "There are no stairs down here."


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


def test_messages_pile_up_in_the_log_oldest_first():
    level = level_from("#####", "#...#", "#####", items={(2, 1): POTION})
    game = game_on(level, position=(1, 1))

    game.move(Direction.NORTH)
    game.move(Direction.EAST)
    game.descend()

    assert [str(message) for message in game.log] == [
        "A wall is in the way.",
        "You pick up the potion.",
        "There are no stairs down here.",
    ]


def test_the_same_message_in_a_row_is_counted_not_repeated():
    game = game_on(ROOM, position=(1, 1))

    for _ in range(3):
        game.move(Direction.NORTH)
    game.move(Direction.WEST)

    assert game.log == [Message("A wall is in the way.", count=4)]
    assert str(game.log[-1]) == "A wall is in the way. (x4)"


def test_a_different_message_starts_a_new_count():
    game = game_on(ROOM, position=(1, 1))

    game.move(Direction.NORTH)
    game.descend()
    game.move(Direction.NORTH)

    assert [str(message) for message in game.log] == [
        "A wall is in the way.",
        "There are no stairs down here.",
        "A wall is in the way.",
    ]


def test_clearing_the_log_empties_it():
    game = game_on(ROOM, position=(1, 1))
    game.move(Direction.NORTH)

    game.clear_log()

    assert game.log == []


def test_the_log_carries_on_down_the_stairs():
    game = Game.new(seed=42)
    game.move(Direction.NORTH)
    game.move(Direction.NORTH)
    game.move(Direction.NORTH)
    game.move(Direction.NORTH)
    game.player.position = game.level.stairs_down

    game.descend()

    assert [str(message) for message in game.log] == [
        "A wall is in the way.",
        "You go down the stairs to level 2.",
    ]


def _down_to(depth: int, seed: int) -> Game:
    """A new game for `seed`, taken down the stairs to `depth`."""
    game = Game.new(seed)
    while game.depth < depth:
        game.player.position = game.level.stairs_down
        game.descend()
    return game


def test_a_game_has_as_many_floors_as_its_seed_gives():
    assert Game.new(seed=42).floors == floor_count(42)


def test_arriving_on_the_last_floor_says_its_stairs_lead_out():
    # Seed 1's dungeon has three floors.
    game = _down_to(3, seed=1)

    assert [str(message) for message in game.log] == [
        "You go down the stairs to level 2.",
        "You go down the stairs to level 3.",
        "This is the last floor: its stairs lead out of the dungeon.",
    ]
    assert not game.finished


def test_going_down_the_last_floors_stairs_finishes_the_game():
    game = _down_to(3, seed=1)
    level = game.level
    game.player.position = level.stairs_down

    game.descend()

    assert game.finished
    assert game.depth == 3
    assert game.level is level
    assert str(game.log[-1]) == "You go down the last stairs and out of the dungeon."


def test_the_game_isnt_finished_until_the_last_floor():
    game = _down_to(2, seed=1)

    assert not game.finished
    assert "This is the last floor" not in str(game.log[-1])


def _rat(position: Point) -> Monster:
    return Monster("rat", "r", hit_points=2, damage=1, position=position)


def test_a_monster_in_the_way_stops_the_player():
    level = level_from("#####", "#...#", "#####", monsters=[_rat((2, 1))])
    game = game_on(level, position=(1, 1))

    game.move(Direction.EAST)

    assert game.player.position == (1, 1)
    assert str(game.log[-1]) == "A rat is in the way."


def test_only_monsters_with_a_clear_line_to_the_player_are_in_sight():
    seen, hidden = _rat((5, 1)), _rat((3, 3))
    level = level_from(
        "#######",
        "#.....#",
        "#.###.#",
        "#.....#",
        "#######",
        monsters=[seen, hidden],
    )

    game = game_on(level, position=(3, 1))

    assert game.monsters_in_sight() == [seen]


def _goblin(position: Point) -> Monster:
    return Monster("goblin", "g", hit_points=4, damage=2, position=position)


OPEN_ROOM = (
    "#########",
    "#.......#",
    "#.......#",
    "#.......#",
    "#########",
)


def test_a_monster_in_sight_steps_towards_the_player_after_each_step():
    rat = _rat((6, 2))
    game = game_on(level_from(*OPEN_ROOM, monsters=[rat]), position=(1, 2))

    game.move(Direction.NORTH)
    assert rat.position == (5, 2)
    game.move(Direction.SOUTH)
    assert rat.position == (4, 2)


def test_a_monster_closes_in_along_the_axis_the_player_is_furthest_on():
    rat = _rat((4, 1))
    game = game_on(level_from(*OPEN_ROOM, monsters=[rat]), position=(2, 3))

    # The player steps to (3, 3): one across from the rat but two down, so the
    # rat steps down, not across.
    game.move(Direction.EAST)

    assert rat.position == (4, 2)


def test_a_monster_out_of_sight_stays_where_it_is():
    hidden = _rat((3, 3))
    loop = level_from(
        "#######",
        "#.....#",
        "#.###.#",
        "#.....#",
        "#######",
        monsters=[hidden],
    )
    game = game_on(loop, position=(3, 1))

    game.move(Direction.EAST)

    assert hidden.position == (3, 3)


def test_a_monster_next_to_the_player_stays_put():
    rat = _rat((3, 1))
    game = game_on(level_from(*OPEN_ROOM, monsters=[rat]), position=(1, 1))

    game.move(Direction.EAST)

    assert rat.position == (3, 1)


def test_a_wall_in_the_way_sends_a_monster_along_the_other_axis():
    # The rat at (3, 1) can see the player at (1, 3) past the wall at (2, 1),
    # but can't step through it, so it steps down instead.
    rat = _rat((3, 1))
    level = level_from(
        "#####",
        "#.#.#",
        "#...#",
        "#...#",
        "#####",
        monsters=[rat],
    )
    game = game_on(level, position=(2, 3))

    game.move(Direction.WEST)

    assert rat.position == (3, 2)


def test_monsters_take_turns_and_never_share_a_tile():
    # The rat goes first, finds the goblin in its way, and steps up instead.
    rat, goblin = _rat((5, 2)), _goblin((4, 2))
    game = game_on(level_from(*OPEN_ROOM, monsters=[rat, goblin]), position=(1, 2))

    game.move(Direction.NORTH)

    assert rat.position == (5, 1)
    assert goblin.position == (3, 2)


def test_bumping_into_a_wall_doesnt_give_the_monsters_a_turn():
    rat = _rat((6, 2))
    game = game_on(level_from(*OPEN_ROOM, monsters=[rat]), position=(1, 1))

    game.move(Direction.NORTH)

    assert rat.position == (6, 2)
