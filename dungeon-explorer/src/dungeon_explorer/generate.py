"""Generates dungeon levels from a seed."""

import heapq
import random
from dataclasses import replace

from dungeon_explorer.level import Item, Level, Monster, Point, Room, Tile
from dungeon_explorer.settings import DEFAULT_SETTINGS, Settings

# How generation works rather than what it makes, so these aren't settings.
ROOM_ATTEMPTS = 200
# The fewest wall tiles between two rooms, so each room has its own walls.
ROOM_GAP = 2
# A bend in a corridor costs as much as this many steps, so corridors take a
# short detour rather than zigzag.
BEND_COST = 4

# One tile north, east, south and west.
STEPS: tuple[Point, ...] = ((0, -1), (1, 0), (0, 1), (-1, 0))


def floor_count(seed: int, settings: Settings = DEFAULT_SETTINGS) -> int:
    """How many floors the dungeon for `seed` has. The same seed always gives
    the same number."""
    # Its own seed string, so the count doesn't depend on any level.
    rng = random.Random(f"{seed}:floors")
    return rng.randint(settings.min_floors, settings.max_floors)


def generate_level(
    seed: int, depth: int, settings: Settings = DEFAULT_SETTINGS
) -> Level:
    """Generate level `depth` of the dungeon for `seed`.

    The same seed, depth and settings always give the same level.
    """
    # random hashes a string seed with SHA-512, so this is the same in every
    # run, unlike hash(), which changes from one process to the next.
    rng = random.Random(f"{seed}:{depth}")
    rooms = _place_rooms(rng, settings)
    tiles = [[Tile.WALL] * settings.level_width for _ in range(settings.level_height)]
    for room in rooms:
        for x, y in room.tiles():
            tiles[y][x] = Tile.FLOOR
    rooms = _join_rooms(tiles, rooms)
    player_start = rooms[0].centre
    stairs_down = _place_stairs_down(rng, rooms)
    # Nothing goes on the eight tiles around the stairs, so they stand alone
    # in the view and never share a block on the mini-map.
    taken = {player_start, *_around(stairs_down)}
    items = _place_items(rng, rooms, depth, taken, settings)
    monsters = _place_monsters(rng, rooms, depth, {stairs_down, *items}, settings)
    return Level(
        tiles=tiles,
        rooms=rooms,
        player_start=player_start,
        stairs_down=stairs_down,
        items=items,
        monsters=monsters,
    )


def _place_rooms(rng: random.Random, settings: Settings) -> list[Room]:
    """Try rooms of random sizes and places, keeping each one with space around it."""
    rooms: list[Room] = []
    for _ in range(ROOM_ATTEMPTS):
        width = rng.randint(*settings.room_widths)
        height = rng.randint(*settings.room_heights)
        # Leave a wall between every room and the edge of the level.
        x = rng.randint(1, settings.level_width - width - 1)
        y = rng.randint(1, settings.level_height - height - 1)
        room = Room(x, y, width, height)
        if not any(room.is_near(other, ROOM_GAP) for other in rooms):
            rooms.append(room)
            if len(rooms) == settings.max_rooms:
                break
    return rooms


def _place_stairs_down(rng: random.Random, rooms: list[Room]) -> Point:
    """A random floor tile in any room but the first, where the player starts.

    If settings leave only one room, the stairs go there, away from the start.
    """
    if len(rooms) > 1:
        return rng.choice(rng.choice(rooms[1:]).tiles())
    start = rooms[0].centre
    return rng.choice([tile for tile in rooms[0].tiles() if tile != start])


def _place_items(
    rng: random.Random,
    rooms: list[Room],
    depth: int,
    taken: set[Point],
    settings: Settings,
) -> dict[Point, Item]:
    """Scatter a few random items on room floors, one to a tile, off `taken`
    tiles, from the kinds that can turn up this deep."""
    floor = [tile for room in rooms for tile in room.tiles() if tile not in taken]
    count = min(rng.randint(*settings.items_per_level), len(floor))
    kinds = [kind for kind, first_floor in settings.items if first_floor <= depth]
    if not kinds:
        return {}
    return {tile: rng.choice(kinds) for tile in rng.sample(floor, count)}


def _place_monsters(
    rng: random.Random,
    rooms: list[Room],
    depth: int,
    taken: set[Point],
    settings: Settings,
) -> list[Monster]:
    """Place monsters on the floors of every room but the first, where the
    player starts. Deeper floors get more of them, and tougher kinds."""
    floor = [tile for room in rooms[1:] for tile in room.tiles() if tile not in taken]
    fewest, most = (count + depth - 1 for count in settings.monsters_per_floor)
    count = min(rng.randint(fewest, most), len(floor))
    kinds = [kind for kind, first_floor in settings.monsters if first_floor <= depth]
    if not kinds:
        return []
    return [
        replace(rng.choice(kinds), position=tile) for tile in rng.sample(floor, count)
    ]


def _around(point: Point) -> set[Point]:
    """`point` and the eight tiles around it."""
    x, y = point
    return {(x + dx, y + dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1)}


def _join_rooms(tiles: list[list[Tile]], rooms: list[Room]) -> list[Room]:
    """Carve corridors joining every room, working left to right.

    Each room is joined to whichever room already joined is cheapest to
    reach. A room no corridor can reach is filled back in with wall, and
    left out of the rooms returned, which otherwise keep their order.
    """
    across = sorted(rooms, key=lambda room: room.centre[0])
    joined = across[:1]
    unreachable: list[Room] = []
    for room in across[1:]:
        remaining = [other for other in rooms if other not in unreachable]
        corridor = _route(tiles, remaining, joined, room)
        if corridor is None:
            unreachable.append(room)
            for x, y in room.tiles():
                tiles[y][x] = Tile.WALL
            continue
        for x, y in corridor:
            tiles[y][x] = Tile.FLOOR
        joined.append(room)
    return [room for room in rooms if room not in unreachable]


def _route(
    tiles: list[list[Tile]], rooms: list[Room], joined: list[Room], room: Room
) -> list[Point] | None:
    """The cheapest corridor from a door of any joined room to a door of `room`.

    The corridor keeps off every room's floor and walls apart from its two
    doors, so it can't run along a wall or cut through a room. This is
    Dijkstra's algorithm, tracking which way the corridor is heading so a
    bend can cost extra.
    """
    blocked = {tile for other in rooms for tile in other.tiles() + other.walls()}
    goals = {door for door, _ in _doors(tiles, room)}
    queue = [(0, door, step) for other in joined for door, step in _doors(tiles, other)]
    heapq.heapify(queue)
    came_from: dict[tuple[Point, Point], tuple[Point, Point] | None] = {
        (door, step): None for _, door, step in queue
    }
    cheapest = {(door, step): 0 for _, door, step in queue}
    while queue:
        cost, tile, step = heapq.heappop(queue)
        if cost > cheapest[(tile, step)]:
            continue
        if tile in goals:
            return _walk_back((tile, step), came_from)
        for next_step in STEPS:
            next_tile = (tile[0] + next_step[0], tile[1] + next_step[1])
            if _on_border(tiles, next_tile):
                continue
            if next_tile in blocked and next_tile not in goals:
                continue
            next_cost = cost + 1 + (BEND_COST if next_step != step else 0)
            state = (next_tile, next_step)
            if next_cost < cheapest.get(state, next_cost + 1):
                cheapest[state] = next_cost
                came_from[state] = (tile, step)
                heapq.heappush(queue, (next_cost, next_tile, next_step))
    return None


def _doors(tiles: list[list[Tile]], room: Room) -> list[tuple[Point, Point]]:
    """Each wall tile a corridor could leave `room` through, with the step out.

    Doors sit along the top, bottom, left or right side, never on a corner or
    the level's border, and never beside an existing door, so no wall has a
    gap two tiles wide.
    """
    sides = (
        ((0, -1), [(x, room.y - 1) for x in range(room.x, room.right)]),
        ((0, 1), [(x, room.bottom) for x in range(room.x, room.right)]),
        ((-1, 0), [(room.x - 1, y) for y in range(room.y, room.bottom)]),
        ((1, 0), [(room.right, y) for y in range(room.y, room.bottom)]),
    )
    doors = []
    for step, side in sides:
        along = (step[1], step[0])
        for x, y in side:
            beside = ((x + along[0], y + along[1]), (x - along[0], y - along[1]))
            if _on_border(tiles, (x, y)):
                continue
            if any(tiles[by][bx] is Tile.FLOOR for bx, by in beside):
                continue
            doors.append(((x, y), step))
    return doors


def _on_border(tiles: list[list[Tile]], tile: Point) -> bool:
    x, y = tile
    return x in (0, len(tiles[0]) - 1) or y in (0, len(tiles) - 1)


def _walk_back(
    state: tuple[Point, Point],
    came_from: dict[tuple[Point, Point], tuple[Point, Point] | None],
) -> list[Point]:
    """The tiles of the corridor that ends at `state`."""
    tiles = []
    current: tuple[Point, Point] | None = state
    while current is not None:
        tiles.append(current[0])
        current = came_from[current]
    return tiles
