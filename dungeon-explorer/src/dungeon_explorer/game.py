"""The state of a game in play, and the rules for changing it."""

from dataclasses import dataclass, field
from typing import Self

from dungeon_explorer.generate import floor_count, generate_level
from dungeon_explorer.level import Direction, Item, Level, Monster, Point, Tile


@dataclass
class Player:
    """The person exploring the dungeon.

    `inventory` holds what they've picked up, in the order they picked it up.
    """

    position: Point
    inventory: list[Item] = field(default_factory=list)


@dataclass
class Message:
    """Something that happened, and how many times in a row it happened."""

    text: str
    count: int = 1

    def __str__(self) -> str:
        return self.text if self.count == 1 else f"{self.text} (x{self.count})"


@dataclass
class Game:
    """Everything about a game in play.

    `explored` holds every tile of this level the player has seen, and `log`
    holds every message of the game, oldest first, for showing to the player.
    `finished` turns true when the player goes down the last floor's stairs.
    """

    seed: int
    level: Level
    player: Player
    depth: int = 1
    explored: set[Point] = field(default_factory=set)
    log: list[Message] = field(default_factory=list)
    finished: bool = False

    def __post_init__(self) -> None:
        self._explore()

    @property
    def floors(self) -> int:
        """How many floors this game's dungeon has, set by its seed."""
        return floor_count(self.seed)

    @classmethod
    def new(cls, seed: int) -> Self:
        """Start a game at the top of the dungeon for `seed`."""
        level = generate_level(seed, depth=1)
        return cls(seed=seed, level=level, player=Player(level.player_start))

    def move(self, direction: Direction) -> None:
        """Step the player one tile, unless a wall or a monster is in the way.

        Anything on the tile they step onto goes into their inventory.
        """
        target = direction.step_from(self.player.position)
        if not self._is_floor(target):
            self.say("A wall is in the way.")
            return
        monster = self.level.monster_at(target)
        if monster is not None:
            self.say(f"A {monster.name} is in the way.")
            return
        self.player.position = target
        self._pick_up()
        self._explore()

    def descend(self) -> None:
        """Go down to the next level, if the player is standing on the stairs.

        The new level comes from the same seed, so it's the same whatever
        happened on the levels above. The player keeps their inventory. The
        last floor's stairs lead out of the dungeon, which finishes the game.
        """
        if self.player.position != self.level.stairs_down:
            self.say("There are no stairs down here.")
            return
        if self.depth == self.floors:
            self.finished = True
            self.say("You go down the last stairs and out of the dungeon.")
            return
        self.depth += 1
        self.level = generate_level(self.seed, self.depth)
        self.player.position = self.level.player_start
        self.explored = set()
        self._explore()
        self.say(f"You go down the stairs to level {self.depth}.")
        if self.depth == self.floors:
            self.say("This is the last floor: its stairs lead out of the dungeon.")

    def monsters_in_sight(self) -> list[Monster]:
        """The monsters the player can see from where they stand."""
        position = self.player.position
        return [
            m for m in self.level.monsters if self.level.can_see(position, m.position)
        ]

    def say(self, text: str) -> None:
        """Add `text` to the log, counting it again if it's the same as the last."""
        if self.log and self.log[-1].text == text:
            self.log[-1].count += 1
        else:
            self.log.append(Message(text))

    def clear_log(self) -> None:
        self.log.clear()

    def _pick_up(self) -> None:
        """Move any item under the player off the level and into their inventory."""
        item = self.level.items.pop(self.player.position, None)
        if item is None:
            return
        self.player.inventory.append(item)
        self.say(f"You pick up the {item.name}.")

    def _explore(self) -> None:
        """Reveal what the player can see from where they stand.

        That's the whole of the room they're in, walls and all, and the eight
        tiles around them, which maps corridors as they're walked.
        """
        position = self.player.position
        for room in self.level.rooms:
            if position in room.tiles():
                self.explored.update(room.tiles())
                self.explored.update(room.walls())
        x, y = position
        around = [(x + dx, y + dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
        self.explored.update(tile for tile in around if self._on_level(tile))

    def _is_floor(self, point: Point) -> bool:
        """Whether `point` is on the level and is floor, so it can be walked on."""
        return self._on_level(point) and self.level.tile(*point) is Tile.FLOOR

    def _on_level(self, point: Point) -> bool:
        x, y = point
        return 0 <= x < self.level.width and 0 <= y < self.level.height
