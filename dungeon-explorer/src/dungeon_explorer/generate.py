"""Generates dungeon levels from a seed."""

import random

from dungeon_explorer.level import Level, Room, Tile

LEVEL_WIDTH = 64
LEVEL_HEIGHT = 32
MAX_ROOMS = 9
ROOM_ATTEMPTS = 200
ROOM_WIDTHS = (4, 12)
ROOM_HEIGHTS = (3, 7)
# The fewest wall tiles between two rooms, so each room has its own walls.
ROOM_GAP = 2


def generate_level(seed: int, depth: int) -> Level:
    """Generate level `depth` of the dungeon for `seed`.

    The same seed and depth always give the same level.
    """
    # random hashes a string seed with SHA-512, so this is the same in every
    # run, unlike hash(), which changes from one process to the next.
    rng = random.Random(f"{seed}:{depth}")
    rooms = _place_rooms(rng)
    tiles = [[Tile.WALL] * LEVEL_WIDTH for _ in range(LEVEL_HEIGHT)]
    for room in rooms:
        for x, y in room.tiles():
            tiles[y][x] = Tile.FLOOR
    return Level(tiles=tiles, rooms=rooms)


def _place_rooms(rng: random.Random) -> list[Room]:
    """Try rooms of random sizes and places, keeping each one with space around it."""
    rooms: list[Room] = []
    for _ in range(ROOM_ATTEMPTS):
        width = rng.randint(*ROOM_WIDTHS)
        height = rng.randint(*ROOM_HEIGHTS)
        # Leave a wall between every room and the edge of the level.
        x = rng.randint(1, LEVEL_WIDTH - width - 1)
        y = rng.randint(1, LEVEL_HEIGHT - height - 1)
        room = Room(x, y, width, height)
        if not any(room.is_near(other, ROOM_GAP) for other in rooms):
            rooms.append(room)
            if len(rooms) == MAX_ROOMS:
                break
    return rooms
