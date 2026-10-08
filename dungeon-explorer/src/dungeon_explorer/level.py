"""The tiles and rooms a dungeon level is made of."""

from dataclasses import dataclass
from enum import StrEnum


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


@dataclass
class Level:
    """A grid of tiles, indexed tiles[y][x], and the rooms carved into it."""

    tiles: list[list[Tile]]
    rooms: list[Room]

    @property
    def width(self) -> int:
        return len(self.tiles[0])

    @property
    def height(self) -> int:
        return len(self.tiles)

    def tile(self, x: int, y: int) -> Tile:
        return self.tiles[y][x]
