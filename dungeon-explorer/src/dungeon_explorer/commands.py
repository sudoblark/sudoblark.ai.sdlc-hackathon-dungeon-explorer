"""Turns typed input into commands that act on the game.

This is the Command pattern from Game Programming Patterns: each action the
player can take is an object, so input handling only has to pick one, and
the game rules stay in Game.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from dungeon_explorer.game import Game
from dungeon_explorer.level import Direction


class Command(ABC):
    """Something the player can do on their turn."""

    @abstractmethod
    def execute(self, game: Game) -> None: ...


@dataclass(frozen=True)
class Move(Command):
    """Step one tile in a direction."""

    direction: Direction

    def execute(self, game: Game) -> None:
        game.move(self.direction)


@dataclass(frozen=True)
class Descend(Command):
    """Go down the stairs."""

    def execute(self, game: Game) -> None:
        game.descend()


@dataclass(frozen=True)
class Drink(Command):
    """Drink a potion to heal."""

    def execute(self, game: Game) -> None:
        game.drink()


# Commands hold no state, so each key can share one instance.
KEYS: dict[str, Command] = {
    "w": Move(Direction.NORTH),
    "a": Move(Direction.WEST),
    "s": Move(Direction.SOUTH),
    "d": Move(Direction.EAST),
    ">": Descend(),
    "p": Drink(),
}


def parse_command(text: str) -> Command | None:
    """The command for a line of input, or None if it isn't one.

    Case and surrounding spaces don't matter. Screen keys such as `i` for the
    inventory aren't commands, because they don't change the game.
    """
    return KEYS.get(text.strip().lower())
