"""The screens of the game, each drawing itself and handling the player's input.

This is the State pattern from Game Programming Patterns: the game loop only
ever talks to the current state, which says what to draw and which state
comes next. Returning None ends the game.
"""

from abc import ABC, abstractmethod

from dungeon_explorer.commands import parse_command
from dungeon_explorer.game import Game
from dungeon_explorer.render import draw_mini_map, draw_view

BACK = "Press Enter to go back."


class State(ABC):
    """One screen of the game."""

    @abstractmethod
    def draw(self, game: Game) -> list[str]:
        """The screen's lines of text."""

    @abstractmethod
    def handle(self, game: Game, text: str) -> "State | None":
        """Act on a line of input, and return the next state, or None to quit."""


class PlayingState(State):
    """The dungeon: the view, the mini-map, and where the player is."""

    def draw(self, game: Game) -> list[str]:
        view = draw_view(game)
        mini_map = draw_mini_map(game)
        height = max(len(view), len(mini_map))
        panels = zip(_frame(view, height), _frame(mini_map, height), strict=True)
        return [
            f"Level {game.depth}   Seed {game.seed}   ? for help",
            *(f"{left} {right}" for left, right in panels),
            game.message,
        ]

    def handle(self, game: Game, text: str) -> State | None:
        key = text.strip().lower()
        if key == "q":
            return None
        if key == "i":
            return InventoryState()
        if key == "?":
            return HelpState()
        command = parse_command(key)
        if command is not None:
            command.execute(game)
        elif key:
            game.message = f"Unknown command {text.strip()!r}. Press ? for help."
        return self


class InventoryState(State):
    """What the player is carrying, in the order they picked it up."""

    def draw(self, game: Game) -> list[str]:
        items = [f"  {item.glyph} {item.name}" for item in game.player.inventory]
        return [
            "Inventory",
            "",
            *(items or ["  You aren't carrying anything yet."]),
            "",
            BACK,
        ]

    def handle(self, game: Game, text: str) -> State | None:
        return PlayingState()


class HelpState(State):
    """The keys, and what they do."""

    def draw(self, game: Game) -> list[str]:
        return [
            "How to play",
            "",
            "  w a s d   move north, west, south or east",
            "  >         go down the stairs, when you're on them",
            "  i         look at your inventory",
            "  ?         show this help",
            "  q         quit",
            "",
            "Type a key and press Enter. Walk onto an item to pick it up.",
            BACK,
        ]

    def handle(self, game: Game, text: str) -> State | None:
        return PlayingState()


def _frame(lines: list[str], height: int) -> list[str]:
    """Put a border round `lines`, first padding them with blank lines to `height`."""
    width = len(lines[0])
    padded = lines + [" " * width] * (height - len(lines))
    edge = "+" + "-" * width + "+"
    return [edge, *(f"|{line}|" for line in padded), edge]
