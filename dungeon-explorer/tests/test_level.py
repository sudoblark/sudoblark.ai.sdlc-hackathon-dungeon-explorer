import pytest
from helpers import level_from

from dungeon_explorer.level import Direction, Level, Monster, Room, Tile


@pytest.mark.parametrize(
    ("direction", "point"),
    [
        (Direction.NORTH, (3, 2)),
        (Direction.EAST, (4, 3)),
        (Direction.SOUTH, (3, 4)),
        (Direction.WEST, (2, 3)),
    ],
)
def test_a_direction_steps_one_tile_from_a_point(direction, point):
    assert direction.step_from((3, 3)) == point


def test_room_right_and_bottom_are_just_past_its_floor():
    room = Room(x=2, y=3, width=4, height=5)

    assert room.right == 6
    assert room.bottom == 8


@pytest.mark.parametrize(
    ("room", "centre"),
    [
        (Room(x=2, y=3, width=5, height=3), (4, 4)),  # odd sizes: the middle
        (Room(x=2, y=3, width=4, height=2), (4, 4)),  # even sizes: right and down
    ],
)
def test_room_centre_is_its_middle_tile(room, centre):
    assert room.centre == centre


def test_room_tiles_cover_its_floor_row_by_row():
    room = Room(x=1, y=2, width=3, height=2)

    assert room.tiles() == [(1, 2), (2, 2), (3, 2), (1, 3), (2, 3), (3, 3)]


def test_room_walls_ring_its_floor_including_corners():
    room = Room(x=1, y=1, width=2, height=1)

    assert room.walls() == [
        (0, 0), (1, 0), (2, 0), (3, 0),
        (0, 1),                 (3, 1),
        (0, 2), (1, 2), (2, 2), (3, 2),
    ]  # fmt: skip


@pytest.mark.parametrize(
    ("other", "near"),
    [
        (Room(x=3, y=3, width=4, height=4), True),  # overlapping
        (Room(x=5, y=0, width=4, height=4), True),  # sharing an edge
        (Room(x=6, y=0, width=4, height=4), True),  # one wall between
        (Room(x=7, y=0, width=4, height=4), False),  # two walls between
        (Room(x=6, y=6, width=4, height=4), True),  # one wall away diagonally
        (Room(x=7, y=7, width=4, height=4), False),  # two walls away diagonally
        (Room(x=6, y=20, width=4, height=4), False),  # close across, far down
    ],
)
def test_room_is_near_another_with_fewer_than_gap_tiles_between(other, near):
    room = Room(x=0, y=0, width=5, height=5)

    assert room.is_near(other, gap=2) is near
    assert other.is_near(room, gap=2) is near


def test_level_size_and_tiles_come_from_its_grid():
    level = Level(
        tiles=[
            [Tile.WALL, Tile.WALL, Tile.WALL],
            [Tile.WALL, Tile.FLOOR, Tile.WALL],
        ],
        rooms=[Room(x=1, y=1, width=1, height=1)],
        player_start=(1, 1),
        stairs_down=(1, 1),
        items={},
    )

    assert level.width == 3
    assert level.height == 2
    assert level.tile(1, 1) is Tile.FLOOR
    assert level.tile(2, 0) is Tile.WALL


# A loop of floor round a block of wall.
LOOP = level_from(
    "#######",
    "#.....#",
    "#.###.#",
    "#.....#",
    "#######",
)


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ((1, 1), (5, 1)),  # along a row of floor
        ((1, 1), (1, 3)),  # down a column of floor
        ((1, 1), (2, 1)),  # next to each other
        ((1, 1), (1, 1)),  # the same tile
    ],
)
def test_a_clear_line_of_floor_can_be_seen_along_both_ways(a, b):
    assert LOOP.can_see(a, b)
    assert LOOP.can_see(b, a)


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ((3, 1), (3, 3)),  # straight through the block of wall
        ((1, 1), (5, 3)),  # a slanting line that clips the wall
    ],
)
def test_walls_block_sight_both_ways(a, b):
    assert not LOOP.can_see(a, b)
    assert not LOOP.can_see(b, a)


def test_monster_at_finds_the_monster_on_a_tile():
    rat = Monster("rat", "r", hit_points=2, damage=1, position=(2, 1))
    level = level_from("#####", "#...#", "#####", monsters=[rat])

    assert level.monster_at((2, 1)) is rat
    assert level.monster_at((1, 1)) is None
