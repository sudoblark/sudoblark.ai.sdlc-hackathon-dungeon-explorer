"""The state of a game in play, and the rules for changing it."""

from dataclasses import dataclass, field
from typing import Self

from dungeon_explorer.generate import generate_level
from dungeon_explorer.level import Direction, Item, Level, Point, Tile


@dataclass
class Player:
    """The person exploring the dungeon.

    `inventory` holds what they've picked up, in the order they picked it up.
    """

    position: Point
    inventory: list[Item] = field(default_factory=list)


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
        """Step the player one tile, unless there's a wall in the way.

        Anything on the tile they step onto goes into their inventory.
        """
        target = direction.step_from(self.player.position)
        if not self._is_floor(target):
            self.message = "A wall is in the way."
            return
        self.player.position = target
        self.message = ""
        self._pick_up()

    def descend(self) -> None:
        """Go down to the next level, if the player is standing on the stairs.

        The new level comes from the same seed, so it's the same whatever
        happened on the levels above. The player keeps their inventory.
        """
        if self.player.position != self.level.stairs_down:
            self.message = "There are no stairs down here."
            return
        self.depth += 1
        self.level = generate_level(self.seed, self.depth)
        self.player.position = self.level.player_start
        self.message = f"You go down the stairs to level {self.depth}."

    def _pick_up(self) -> None:
        """Move any item under the player off the level and into their inventory."""
        item = self.level.items.pop(self.player.position, None)
        if item is None:
            return
        self.player.inventory.append(item)
        self.message = f"You pick up the {item.name}."

    def _is_floor(self, point: Point) -> bool:
        """Whether `point` is on the level and is floor, so it can be walked on."""
        x, y = point
        level = self.level
        on_level = 0 <= x < level.width and 0 <= y < level.height
        return on_level and level.tile(x, y) is Tile.FLOOR
