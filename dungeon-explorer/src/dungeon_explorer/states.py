"""The screens of the game, each drawing itself and handling the player's input.

This is the State pattern from Game Programming Patterns: the game loop only
ever talks to the current state, which says what to draw and which state
comes next. Returning None ends the game. Each state holds whatever it shows,
so a state can start a new game or leave a finished one behind.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from dungeon_explorer.commands import parse_command
from dungeon_explorer.game import Game
from dungeon_explorer.generate import ITEMS
from dungeon_explorer.level import Tile
from dungeon_explorer.render import PLAYER, STAIRS_DOWN, draw_mini_map, draw_view

BACK = "Press any key to go back."
TITLE = "DUNGEON EXPLORER"
MENU = "i inventory   ? help   q quit"
# Every symbol the playing screen can show, and what it means.
LEGEND = [
    (PLAYER, "you"),
    (Tile.WALL, "wall"),
    (Tile.FLOOR, "floor"),
    (STAIRS_DOWN, "stairs"),
    *((item.glyph, item.name) for item in ITEMS),
]


class State(ABC):
    """One screen of the game."""

    @abstractmethod
    def draw(self) -> list[str]:
        """The screen's lines of text."""

    @abstractmethod
    def handle(self, text: str) -> "State | None":
        """Act on a line of input, and return the next state, or None to quit."""

    @abstractmethod
    def goodbye(self) -> str:
        """What to say if the game ends on this screen."""


@dataclass
class _InGameState(State):
    """A screen of a game in play, which it holds."""

    game: Game

    def goodbye(self) -> str:
        game = self.game
        return f"Goodbye! You reached level {game.depth} of seed {game.seed}."


class PlayingState(_InGameState):
    """The dungeon: a header, the view and mini-map with a legend beside
    them, and the last message underneath."""

    def draw(self) -> list[str]:
        game = self.game
        view = draw_view(game)
        mini_map = draw_mini_map(game)
        height = max(len(view), len(mini_map))
        left = _frame(view, height, "View")
        right = _frame(mini_map, height, "Map")
        panels = [f"{a} {b}" for a, b in zip(left, right, strict=True)]
        width = len(panels[0])
        # The legend starts level with the top of the panels' contents.
        key = ["", "Key", *(f"{glyph} {name}" for glyph, name in LEGEND)]
        beside = [
            f"{panel}  {key[row]}" if row < len(key) and key[row] else panel
            for row, panel in enumerate(panels)
        ]
        return [
            TITLE + MENU.rjust(width - len(TITLE)),
            f"Level {game.depth}   Seed {game.seed}",
            *beside,
            game.message,
        ]

    def handle(self, text: str) -> State | None:
        key = text.strip().lower()
        if key == "q":
            return None
        if key == "i":
            return InventoryState(self.game)
        if key == "?":
            return HelpState(self.game)
        command = parse_command(key)
        if command is not None:
            command.execute(self.game)
        elif key:
            self.game.message = f"Unknown command {text.strip()!r}. Press ? for help."
        return self


class InventoryState(_InGameState):
    """What the player is carrying, in the order they picked it up."""

    def draw(self) -> list[str]:
        inventory = self.game.player.inventory
        items = [f"  {item.glyph} {item.name}" for item in inventory]
        return [
            "Inventory",
            "",
            *(items or ["  You aren't carrying anything yet."]),
            "",
            BACK,
        ]

    def handle(self, text: str) -> State | None:
        return PlayingState(self.game)


class HelpState(_InGameState):
    """The keys, and what they do."""

    def draw(self) -> list[str]:
        return [
            "How to play",
            "",
            "  w a s d   move north, west, south or east",
            "  >         go down the stairs, when you're on them",
            "  i         look at your inventory",
            "  ?         show this help",
            "  q         quit",
            "",
            "Each key acts as soon as you press it. Walk onto an item to pick it up.",
            BACK,
        ]

    def handle(self, text: str) -> State | None:
        return PlayingState(self.game)


def _frame(lines: list[str], height: int, label: str) -> list[str]:
    """Put a border round `lines`, with `label` in its top edge, first padding
    them with blank lines to `height`."""
    width = len(lines[0])
    padded = lines + [" " * width] * (height - len(lines))
    top = f"+- {label} ".ljust(width + 1, "-") + "+"
    bottom = "+" + "-" * width + "+"
    return [top, *(f"|{line}|" for line in padded), bottom]
