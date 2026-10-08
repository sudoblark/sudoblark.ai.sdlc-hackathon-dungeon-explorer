from itertools import combinations

import pytest

from dungeon_explorer.generate import generate_level
from dungeon_explorer.level import Room, Tile

SEEDS = range(20)


def _walls_between(a: Room, b: Room) -> int:
    """How many tiles separate two rooms, along whichever axis is further."""
    across = max(b.x - a.right, a.x - b.right)
    down = max(b.y - a.bottom, a.y - b.bottom)
    return max(across, down)


@pytest.mark.parametrize("seed", SEEDS)
def test_every_level_has_at_least_two_rooms(seed):
    assert len(generate_level(seed, depth=1).rooms) >= 2


@pytest.mark.parametrize("seed", SEEDS)
def test_rooms_stay_inside_the_level_wall(seed):
    level = generate_level(seed, depth=1)

    for room in level.rooms:
        assert room.x >= 1
        assert room.y >= 1
        assert room.right <= level.width - 1
        assert room.bottom <= level.height - 1


@pytest.mark.parametrize("seed", SEEDS)
def test_rooms_never_overlap_or_touch(seed):
    level = generate_level(seed, depth=1)

    for a, b in combinations(level.rooms, 2):
        assert _walls_between(a, b) >= 2, (a, b)


@pytest.mark.parametrize("seed", SEEDS)
def test_rooms_are_floor_inside_a_border_of_wall(seed):
    level = generate_level(seed, depth=1)

    for room in level.rooms:
        for x, y in room.tiles():
            assert level.tile(x, y) is Tile.FLOOR
    for x in range(level.width):
        assert level.tile(x, 0) is Tile.WALL
        assert level.tile(x, level.height - 1) is Tile.WALL
    for y in range(level.height):
        assert level.tile(0, y) is Tile.WALL
        assert level.tile(level.width - 1, y) is Tile.WALL


def test_the_same_seed_and_depth_give_the_same_level():
    assert generate_level(42, depth=1) == generate_level(42, depth=1)


def test_the_same_seed_gives_the_same_rooms_in_every_run():
    # Pinned, so a change to the seeding or the generator shows up here,
    # not as a different dungeon for someone replaying a seed.
    assert generate_level(42, depth=1).rooms == [
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


def test_different_seeds_give_different_levels():
    assert generate_level(1, depth=1) != generate_level(2, depth=1)


def test_different_depths_give_different_levels():
    assert generate_level(42, depth=1) != generate_level(42, depth=2)
