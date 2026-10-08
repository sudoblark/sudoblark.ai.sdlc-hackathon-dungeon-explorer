from functools import cache
from itertools import combinations, pairwise

import pytest

from dungeon_explorer.generate import (
    ITEMS,
    ITEMS_PER_LEVEL,
    MAX_FLOORS,
    MIN_FLOORS,
    MONSTERS,
    MONSTERS_PER_FLOOR,
    _join_rooms,
    floor_count,
    generate_level,
)
from dungeon_explorer.level import Item, Level, Monster, Point, Room, Tile

SEEDS = range(20)
# Fewer seeds for tests that look at several floors of each.
DEPTH_SEEDS = range(10)


@cache
def _level(seed: int, depth: int = 1) -> Level:
    """A seed's level, generated once and shared, since most tests only read it."""
    return generate_level(seed, depth)


def _walls_between(a: Room, b: Room) -> int:
    """How many tiles separate two rooms, along whichever axis is further."""
    across = max(b.x - a.right, a.x - b.right)
    down = max(b.y - a.bottom, a.y - b.bottom)
    return max(across, down)


def _reachable(tiles: list[list[Tile]], start: Point) -> set[Point]:
    """Every floor tile a player could walk to from `start`, one step at a time."""
    seen = {start}
    frontier = [start]
    while frontier:
        x, y = frontier.pop()
        for step_x, step_y in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            tile = (x + step_x, y + step_y)
            if tile not in seen and tiles[tile[1]][tile[0]] is Tile.FLOOR:
                seen.add(tile)
                frontier.append(tile)
    return seen


def _floor(tiles: list[list[Tile]]) -> set[Point]:
    return {
        (x, y)
        for y, row in enumerate(tiles)
        for x, tile in enumerate(row)
        if tile is Tile.FLOOR
    }


def _room_floor(level: Level) -> set[Point]:
    return {tile for room in level.rooms for tile in room.tiles()}


def _sides(room: Room) -> list[list[tuple[int, int]]]:
    """The wall tiles along the room's top, bottom, left and right, without corners."""
    return [
        [(x, room.y - 1) for x in range(room.x, room.right)],
        [(x, room.bottom) for x in range(room.x, room.right)],
        [(room.x - 1, y) for y in range(room.y, room.bottom)],
        [(room.right, y) for y in range(room.y, room.bottom)],
    ]


@pytest.mark.parametrize("seed", SEEDS)
def test_every_level_has_at_least_two_rooms(seed):
    assert len(_level(seed).rooms) >= 2


@pytest.mark.parametrize("seed", SEEDS)
def test_rooms_stay_inside_the_level_wall(seed):
    level = _level(seed)

    for room in level.rooms:
        assert room.x >= 1
        assert room.y >= 1
        assert room.right <= level.width - 1
        assert room.bottom <= level.height - 1


@pytest.mark.parametrize("seed", SEEDS)
def test_rooms_never_overlap_or_touch(seed):
    level = _level(seed)

    for a, b in combinations(level.rooms, 2):
        assert _walls_between(a, b) >= 2, (a, b)


@pytest.mark.parametrize("seed", SEEDS)
def test_rooms_are_floor_inside_a_border_of_wall(seed):
    level = _level(seed)

    for room in level.rooms:
        for x, y in room.tiles():
            assert level.tile(x, y) is Tile.FLOOR
    for x in range(level.width):
        assert level.tile(x, 0) is Tile.WALL
        assert level.tile(x, level.height - 1) is Tile.WALL
    for y in range(level.height):
        assert level.tile(0, y) is Tile.WALL
        assert level.tile(level.width - 1, y) is Tile.WALL


@pytest.mark.parametrize("seed", SEEDS)
def test_every_floor_tile_can_be_walked_to_from_the_first_room(seed):
    level = _level(seed)

    start = level.rooms[0].centre
    assert _reachable(level.tiles, start) == _floor(level.tiles)


@pytest.mark.parametrize("seed", SEEDS)
def test_corridors_join_rooms_only_through_single_doors_in_a_side(seed):
    level = _level(seed)

    for room in level.rooms:
        corners = [
            (room.x - 1, room.y - 1),
            (room.right, room.y - 1),
            (room.x - 1, room.bottom),
            (room.right, room.bottom),
        ]
        assert all(level.tile(x, y) is Tile.WALL for x, y in corners), room
        for side in _sides(room):
            doors = [level.tile(x, y) is Tile.FLOOR for x, y in side]
            # Two doors side by side would be a corridor running along the wall.
            assert not any(a and b for a, b in pairwise(doors)), (room, side)


def test_a_room_no_corridor_can_reach_is_filled_in_and_dropped():
    # The boxed-in room's doors would all open onto the level's border or
    # another room's wall, so no corridor can reach it:
    #
    #   ##############################
    #   #..###########################   start
    #   #..###########################
    #   ##############################
    #   ##############################
    #   #....................#########   above
    #   #....................#########
    #   ##############################
    #   ##############################
    #   #....##...####################   boxed in, then beside
    #   #....##...####################
    #   #....##...####################
    #   #....##...####################
    #   ##############################
    start = Room(x=1, y=1, width=2, height=2)
    above = Room(x=1, y=5, width=20, height=2)
    boxed_in = Room(x=1, y=9, width=4, height=4)
    beside = Room(x=7, y=9, width=3, height=4)
    rooms = [start, above, boxed_in, beside]
    tiles = [[Tile.WALL] * 30 for _ in range(14)]
    for room in rooms:
        for x, y in room.tiles():
            tiles[y][x] = Tile.FLOOR

    joined = _join_rooms(tiles, rooms)

    assert joined == [start, above, beside]
    assert all(tiles[y][x] is Tile.WALL for x, y in boxed_in.tiles())
    assert _reachable(tiles, start.centre) == _floor(tiles)


@pytest.mark.parametrize("seed", SEEDS)
def test_the_player_starts_in_the_middle_of_the_first_room(seed):
    level = _level(seed)

    assert level.player_start == level.rooms[0].centre


@pytest.mark.parametrize("seed", SEEDS)
def test_the_stairs_down_are_on_the_floor_of_another_room(seed):
    level = _level(seed)

    other_rooms = level.rooms[1:]
    assert any(level.stairs_down in room.tiles() for room in other_rooms)


@pytest.mark.parametrize("seed", SEEDS)
def test_a_few_items_lie_on_room_floors(seed):
    level = _level(seed)

    low, high = ITEMS_PER_LEVEL
    assert low <= len(level.items) <= high
    assert set(level.items) <= _room_floor(level)
    kinds = [kind for kind, _ in ITEMS]
    assert all(item in kinds for item in level.items.values())


@pytest.mark.parametrize("seed", SEEDS)
def test_no_item_shares_a_tile_with_the_start_or_the_stairs(seed):
    level = _level(seed)

    # Items are keyed by tile, so no two items can share one.
    assert level.player_start not in level.items
    assert level.stairs_down not in level.items


@pytest.mark.parametrize("seed", SEEDS)
def test_no_item_lies_within_one_tile_of_the_stairs(seed):
    level = _level(seed)

    stairs_x, stairs_y = level.stairs_down
    for x, y in level.items:
        assert max(abs(x - stairs_x), abs(y - stairs_y)) > 1, (x, y)


@pytest.mark.parametrize("seed", SEEDS)
def test_no_item_lies_in_a_doorway(seed):
    level = _level(seed)

    doors = {
        (x, y)
        for room in level.rooms
        for x, y in room.walls()
        if level.tile(x, y) is Tile.FLOOR
    }
    assert doors
    assert not set(level.items) & doors


def test_the_same_seed_and_depth_give_the_same_level():
    assert generate_level(42, depth=1) == generate_level(42, depth=1)


def test_the_same_seed_gives_the_same_rooms_in_every_run():
    # Pinned, so a change to the seeding or the generator shows up here,
    # not as a different dungeon for someone replaying a seed.
    assert _level(42).rooms == [
        Room(x=29, y=22, width=6, height=7),
        Room(x=39, y=21, width=12, height=7),
        Room(x=38, y=11, width=12, height=5),
        Room(x=4, y=5, width=7, height=3),
        Room(x=27, y=9, width=7, height=7),
        Room(x=52, y=14, width=5, height=4),
        Room(x=12, y=15, width=7, height=5),
        Room(x=11, y=24, width=12, height=3),
        Room(x=57, y=27, width=5, height=4),
    ]


def test_the_same_seed_gives_the_same_map_in_every_run():
    # Pinned like the rooms above, so the corridors can't change unnoticed.
    assert ["".join(row) for row in _level(42).tiles] == [
        "################################################################",
        "################################################################",
        "################################################################",
        "################################################################",
        "################################################################",
        "####.......#####################################################",
        "####.......#####################################################",
        "####.......#####################################################",
        "##########.#####################################################",
        "##########.################.......##############################",
        "##########.################.......##############################",
        "##########.################.......................##############",
        "##########.################.......####............##############",
        "##########.################.......####............##############",
        "##########.################.......####...................#######",
        "##########........................####............##.....#######",
        "############.......#################################.....#######",
        "############.......#################################.....#######",
        "############.......#############################################",
        "############.......#############################################",
        "############.###################################################",
        "############.##########################............#############",
        "############.################......................#############",
        "############.################......####............#############",
        "###########........................####............#############",
        "###########............######......####............#############",
        "###########............######......####............#############",
        "#############################......####.......................##",
        "#############################......######################.....##",
        "#########################################################.....##",
        "#########################################################.....##",
        "################################################################",
    ]


def test_the_same_seed_gives_the_same_start_stairs_and_items_in_every_run():
    level = _level(42)

    assert level.player_start == (32, 25)
    assert level.stairs_down == (47, 13)
    assert level.items == {
        (43, 13): Item("potion", "!", healing=5),
        (48, 15): Item("potion", "!", healing=5),
        (15, 16): Item("dagger", ")", damage=2),
        (41, 14): Item("potion", "!", healing=5),
        (44, 24): Item("scroll", "?"),
        (46, 26): Item("potion", "!", healing=5),
    }


def test_different_seeds_give_different_levels():
    assert _level(1) != _level(2)


def test_different_depths_give_different_levels():
    assert generate_level(42, depth=1) != generate_level(42, depth=2)


def test_each_dungeon_has_between_the_fewest_and_most_floors():
    counts = {floor_count(seed) for seed in range(200)}

    assert counts <= set(range(MIN_FLOORS, MAX_FLOORS + 1))
    # Seeds vary the count, rather than all getting the same number.
    assert len(counts) > 1


def test_the_same_seed_always_has_the_same_number_of_floors():
    assert floor_count(42) == floor_count(42) == 7
    assert floor_count(1) == 3


@pytest.mark.parametrize("seed", SEEDS)
def test_monsters_stand_on_the_floor_of_any_room_but_the_first(seed):
    level = _level(seed)

    first_room = set(level.rooms[0].tiles())
    other_rooms = _room_floor(level) - first_room
    positions = [monster.position for monster in level.monsters]
    assert set(positions) <= other_rooms
    assert len(set(positions)) == len(positions)


@pytest.mark.parametrize("seed", SEEDS)
def test_monsters_keep_off_the_stairs_and_the_items(seed):
    level = _level(seed)

    for monster in level.monsters:
        assert monster.position != level.stairs_down
        assert monster.position not in level.items


@pytest.mark.parametrize("depth", [1, 2, 3, 4, 5])
def test_each_floor_deeper_has_more_monsters(depth):
    fewest, most = (count + depth - 1 for count in MONSTERS_PER_FLOOR)

    for seed in DEPTH_SEEDS:
        assert fewest <= len(_level(seed, depth).monsters) <= most


@pytest.mark.parametrize("depth", [1, 2, 3, 4, 5])
def test_tougher_monsters_only_turn_up_deeper(depth):
    allowed = {kind.name for kind, first_floor in MONSTERS if first_floor <= depth}

    found = {m.name for seed in DEPTH_SEEDS for m in _level(seed, depth).monsters}

    assert found <= allowed
    # Over ten seeds, every kind the floor allows turns up.
    assert found == allowed


def test_each_monster_placed_is_its_own_copy():
    level = generate_level(42, depth=1)
    first, second = level.monsters[:2]

    first.hit_points = 0

    assert second.hit_points == 2
    assert all(kind.hit_points > 0 for kind, _ in MONSTERS)


def test_the_same_seed_gives_the_same_monsters_in_every_run():
    assert _level(42).monsters == [
        Monster("rat", "r", hit_points=2, damage=1, position=(7, 7)),
        Monster("rat", "r", hit_points=2, damage=1, position=(49, 15)),
        Monster("rat", "r", hit_points=2, damage=1, position=(18, 18)),
    ]


@pytest.mark.parametrize("depth", [1, 2, 3, 4, 5])
def test_stronger_weapons_only_turn_up_deeper(depth):
    allowed = {kind.name for kind, first_floor in ITEMS if first_floor <= depth}

    found = {i.name for seed in DEPTH_SEEDS for i in _level(seed, depth).items.values()}

    assert found <= allowed


def test_every_kind_of_item_turns_up_somewhere_deep_enough():
    deepest = max(first_floor for _, first_floor in ITEMS)

    found = {
        item.name for seed in range(30) for item in _level(seed, deepest).items.values()
    }

    assert found == {kind.name for kind, _ in ITEMS}


def test_only_weapons_do_damage():
    weapons = {kind.name: kind.damage for kind, _ in ITEMS if kind.damage}

    assert weapons == {"dagger": 2, "sword": 3, "axe": 4}


def test_only_potions_heal():
    healers = {kind.name: kind.healing for kind, _ in ITEMS if kind.healing}

    assert healers == {"potion": 5}
