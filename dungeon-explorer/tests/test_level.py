import pytest

from dungeon_explorer.level import Level, Room, Tile


def test_room_right_and_bottom_are_just_past_its_floor():
    room = Room(x=2, y=3, width=4, height=5)

    assert room.right == 6
    assert room.bottom == 8


def test_room_tiles_cover_its_floor_row_by_row():
    room = Room(x=1, y=2, width=3, height=2)

    assert room.tiles() == [(1, 2), (2, 2), (3, 2), (1, 3), (2, 3), (3, 3)]


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
    )

    assert level.width == 3
    assert level.height == 2
    assert level.tile(1, 1) is Tile.FLOOR
    assert level.tile(2, 0) is Tile.WALL
