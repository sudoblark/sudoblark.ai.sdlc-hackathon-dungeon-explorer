"""The state of a game in play, and the rules for changing it."""

from dataclasses import dataclass
from typing import Self

from dungeon_explorer.generate import generate_level
from dungeon_explorer.level import Direction, Level, Point, Tile


@dataclass
class Player:
    """The person exploring the dungeon."""

    position: Point


@dataclass
class Game:
    """Everything about a game in play.

    `message` says what happened on the last turn, for showing to the player.
    """

    seed: int
    level: Level
    player: Player
    depth: int = 1
    message: str = ""

    @classmethod
    def new(cls, seed: int) -> Self:
        """Start a game at the top of the dungeon for `seed`."""
        level = generate_level(seed, depth=1)
        return cls(seed=seed, level=level, player=Player(level.player_start))

    def move(self, direction: Direction) -> None:
        """Step the player one tile, unless there's a wall in the way."""
        target = direction.step_from(self.player.position)
        if not self._is_floor(target):
            self.message = "A wall is in the way."
            return
        self.player.position = target
        self.message = ""

    def _is_floor(self, point: Point) -> bool:
        """Whether `point` is on the level and is floor, so it can be walked on."""
        x, y = point
        level = self.level
        on_level = 0 <= x < level.width and 0 <= y < level.height
        return on_level and level.tile(x, y) is Tile.FLOOR
