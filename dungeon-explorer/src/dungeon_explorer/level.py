"""The tiles, rooms, items and monsters a dungeon level is made of."""

from dataclasses import dataclass, field
from enum import Enum, StrEnum

# A tile's position, as (x, y).
Point = tuple[int, int]


class Direction(Enum):
    """A step of one tile. Its value is (dx, dy), and y grows downwards."""

    NORTH = (0, -1)
    EAST = (1, 0)
    SOUTH = (0, 1)
    WEST = (-1, 0)

    def step_from(self, point: Point) -> Point:
        """The tile one step from `point` in this direction."""
        dx, dy = self.value
        return (point[0] + dx, point[1] + dy)


class Tile(StrEnum):
    """One square of a level. Its value is how it's drawn."""

    WALL = "#"
    FLOOR = "."


@dataclass(frozen=True)
class Room:
    """A rectangle of floor, with (x, y) as its top-left tile."""

    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        """The first column past the room's floor."""
        return self.x + self.width

    @property
    def bottom(self) -> int:
        """The first row past the room's floor."""
        return self.y + self.height

    @property
    def centre(self) -> tuple[int, int]:
        """The middle floor tile, rounding right and down for even sizes."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def tiles(self) -> list[tuple[int, int]]:
        """Every floor tile in the room, as (x, y), row by row."""
        return [
            (x, y)
            for y in range(self.y, self.bottom)
            for x in range(self.x, self.right)
        ]

    def walls(self) -> list[tuple[int, int]]:
        """Every tile in the ring of wall around the room, corners included."""
        return [
            (x, y)
            for y in range(self.y - 1, self.bottom + 1)
            for x in range(self.x - 1, self.right + 1)
            if not (self.x <= x < self.right and self.y <= y < self.bottom)
        ]

    def is_near(self, other: "Room", gap: int) -> bool:
        """Whether fewer than `gap` tiles separate this room from `other`.

        Overlapping rooms are always near. Rooms are only near if they're
        close along both axes, so rooms side by side but far apart
        vertically aren't.
        """
        return (
            self.x < other.right + gap
            and other.x < self.right + gap
            and self.y < other.bottom + gap
            and other.y < self.bottom + gap
        )


@dataclass(frozen=True)
class Item:
    """Something the player can pick up. Its glyph is how it's drawn."""

    name: str
    glyph: str


@dataclass
class Monster:
    """Something in the dungeon that fights back. Its glyph is how it's drawn.

    The kinds of monster are templates without a position. Each monster
    placed on a level is a copy with its own position and hit points.
    """

    name: str
    glyph: str
    hit_points: int
    damage: int
    position: Point = (0, 0)


@dataclass
class Level:
    """A grid of tiles, indexed tiles[y][x], and what's been put on it.

    `items` maps each tile with an item on it to that item.
    """

    tiles: list[list[Tile]]
    rooms: list[Room]
    player_start: Point
    stairs_down: Point
    items: dict[Point, Item]
    monsters: list[Monster] = field(default_factory=list)

    @property
    def width(self) -> int:
        return len(self.tiles[0])

    @property
    def height(self) -> int:
        return len(self.tiles)

    def tile(self, x: int, y: int) -> Tile:
        return self.tiles[y][x]

    def monster_at(self, point: Point) -> Monster | None:
        return next((m for m in self.monsters if m.position == point), None)

    def can_see(self, a: Point, b: Point) -> bool:
        """Whether a straight line from `a` to `b` crosses only floor.

        The line is always drawn from the lower point to the higher, so
        seeing works both ways: if a can see b, b can see a.
        """
        start, end = sorted((a, b))
        between = _line(start, end)[1:-1]
        return all(self.tile(x, y) is Tile.FLOOR for x, y in between)


def _line(a: Point, b: Point) -> list[Point]:
    """The tiles on a straight line from `a` to `b`, both included.

    This is Bresenham's line algorithm, which steps one tile at a time along
    the longer axis and tracks how far the line has drifted on the other.
    """
    (x, y), (end_x, end_y) = a, b
    dx, dy = abs(end_x - x), -abs(end_y - y)
    step_x = 1 if x < end_x else -1
    step_y = 1 if y < end_y else -1
    error = dx + dy
    tiles = [(x, y)]
    while (x, y) != (end_x, end_y):
        twice = 2 * error
        if twice >= dy:
            error += dy
            x += step_x
        if twice <= dx:
            error += dx
            y += step_y
        tiles.append((x, y))
    return tiles
