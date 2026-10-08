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
MENU = "i inventory  l log  c clear  ? help  q quit"
# How many of the newest messages show under the map.
LOG_LINES = 3
# How many messages the log screen shows at once.
LOG_PAGE = 20
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
    them, and the newest messages underneath."""

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
        # Blank lines above the newest messages keep the screen the same height.
        newest = [str(message) for message in game.log[-LOG_LINES:]]
        return [
            TITLE + MENU.rjust(width - len(TITLE)),
            f"Level {game.depth} of {game.floors}   Seed {game.seed}",
            *beside,
            *[""] * (LOG_LINES - len(newest)),
            *newest,
        ]

    def handle(self, text: str) -> State | None:
        key = text.strip().lower()
        if key == "q":
            return None
        if key == "i":
            return InventoryState(self.game)
        if key == "?":
            return HelpState(self.game)
        if key == "l":
            return LogState(self.game)
        if key == "c":
            # Clearing the log isn't a turn, so it's a screen key, not a command.
            self.game.clear_log()
            return self
        command = parse_command(key)
        if command is not None:
            command.execute(self.game)
        elif key:
            self.game.say(f"Unknown command {text.strip()!r}. Press ? for help.")
        if self.game.finished:
            return WinState(self.game)
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
            "  l         read every message so far",
            "  c         clear the messages",
            "  ?         show this help",
            "  q         quit",
            "",
            "Each key acts as soon as you press it. Walk onto an item to pick it up.",
            BACK,
        ]

    def handle(self, text: str) -> State | None:
        return PlayingState(self.game)


class WinState(_InGameState):
    """The player has found their way out of the dungeon."""

    def draw(self) -> list[str]:
        game = self.game
        inventory = game.player.inventory
        items = [f"  {item.glyph} {item.name}" for item in inventory]
        return [
            "You escaped the dungeon!",
            "",
            f"You made it through all {game.floors} floors of seed {game.seed},"
            " carrying:",
            *(items or ["  nothing at all."]),
            "",
            "Press any key to finish.",
        ]

    def handle(self, text: str) -> State | None:
        return None

    def goodbye(self) -> str:
        game = self.game
        return f"Goodbye! You escaped all {game.floors} floors of seed {game.seed}."


@dataclass
class LogState(_InGameState):
    """Every message of the game, a page at a time, scrolled with w and s.

    `scroll` is how many messages back from the newest the page ends.
    """

    scroll: int = 0

    def draw(self) -> list[str]:
        log = self.game.log
        if not log:
            return ["Message log", "", "  No messages yet.", "", BACK]
        end = len(log) - self.scroll
        start = max(0, end - LOG_PAGE)
        return [
            f"Message log   {start + 1}-{end} of {len(log)}",
            "",
            *(f"  {message}" for message in log[start:end]),
            "",
            "w older   s newer   any other key to go back",
        ]

    def handle(self, text: str) -> State | None:
        key = text.strip().lower()
        if key == "w":
            self.scroll = min(self.scroll + 1, max(0, len(self.game.log) - LOG_PAGE))
            return self
        if key == "s":
            self.scroll = max(self.scroll - 1, 0)
            return self
        return PlayingState(self.game)


def _frame(lines: list[str], height: int, label: str) -> list[str]:
    """Put a border round `lines`, with `label` in its top edge, first padding
    them with blank lines to `height`."""
    width = len(lines[0])
    padded = lines + [" " * width] * (height - len(lines))
    top = f"+- {label} ".ljust(width + 1, "-") + "+"
    bottom = "+" + "-" * width + "+"
    return [top, *(f"|{line}|" for line in padded), bottom]
