"""The screens of the game, each drawing itself and handling the player's input.

This is the State pattern from Game Programming Patterns: the game loop only
ever talks to the current state, which says what to draw and which state
comes next. Returning None ends the game. Each state holds whatever it shows,
so a state can start a new game or leave a finished one behind.

The game opens on the title screen. The screens of a game in play hold the
title screen too, so they can go back to it when the game ends.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

from dungeon_explorer.commands import parse_command
from dungeon_explorer.game import PLAYER_HIT_POINTS, Game
from dungeon_explorer.generate import ITEMS, MONSTERS
from dungeon_explorer.level import Tile
from dungeon_explorer.render import PLAYER, STAIRS_DOWN, draw_mini_map, draw_view

BACK = "Press any key to go back."
TO_TITLE = "Press any key to go back to the title."
TITLE = "DUNGEON EXPLORER"
MENU = "i items  p drink  l log  c clear  ? help  q leave"
# The keys that mean Enter: a terminal sends "\n" or "\r", and piped input
# reads an empty line.
ENTER = ("", "\n", "\r")
# Backspace sends DEL on macOS and Linux terminals, and BS on Windows.
BACKSPACE = ("\x7f", "\b")
# Long enough for any seed you'd want to type, short enough to show.
SEED_DIGITS = 9
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
    *((item.glyph, item.name) for item, _ in ITEMS),
    *((monster.glyph, monster.name) for monster, _ in MONSTERS),
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
class TitleState(State):
    """The title screen: New Game and Exit, chosen with w, s and Enter.

    `seed` is the one given on the command line, if any, which fills in the
    seed screen. `random_seed` picks a seed when the player leaves it blank.
    """

    seed: int | None
    random_seed: Callable[[], int]
    choice: int = 0

    OPTIONS = ("New game", "Exit")

    def draw(self) -> list[str]:
        options = [
            f"  > {option} <" if row == self.choice else f"    {option}"
            for row, option in enumerate(self.OPTIONS)
        ]
        return [
            "+" + "-" * 30 + "+",
            "|" + TITLE.center(30) + "|",
            "+" + "-" * 30 + "+",
            "",
            *options,
            "",
            "w/s to choose, Enter to pick",
        ]

    def handle(self, text: str) -> State | None:
        key = text.strip().lower()
        if key == "w":
            self.choice = max(self.choice - 1, 0)
        elif key == "s":
            self.choice = min(self.choice + 1, len(self.OPTIONS) - 1)
        elif text in ENTER:
            if self.OPTIONS[self.choice] == "Exit":
                return None
            digits = "" if self.seed is None else str(self.seed)
            return SeedState(title=self, digits=digits)
        return self

    def goodbye(self) -> str:
        return "Goodbye!"


@dataclass
class SeedState(State):
    """Typing the seed for a new game, or leaving it blank for a random one."""

    title: TitleState
    digits: str = ""

    def draw(self) -> list[str]:
        return [
            "New game",
            "",
            "Type a seed and press Enter, or leave it blank for a random one.",
            "",
            f"  Seed: {self.digits}_",
            "",
            "q to go back",
        ]

    def handle(self, text: str) -> State | None:
        if text in ENTER:
            seed = int(self.digits) if self.digits else self.title.random_seed()
            return PlayingState(Game.new(seed), self.title)
        if text in BACKSPACE:
            self.digits = self.digits[:-1]
        elif text.isdigit():
            self.digits = (self.digits + text)[:SEED_DIGITS]
        elif text.strip().lower() == "q":
            return self.title
        return self

    def goodbye(self) -> str:
        return "Goodbye!"


@dataclass
class _InGameState(State):
    """A screen of a game in play, which it holds, along with the title screen
    to go back to when the game ends. Without a title screen, as in tests, the
    end of the game ends everything."""

    game: Game
    title: TitleState | None = None

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
            f"Level {game.depth} of {game.floors}   Seed {game.seed}"
            f"   HP {game.player.hit_points}/{PLAYER_HIT_POINTS}",
            *beside,
            *[""] * (LOG_LINES - len(newest)),
            *newest,
        ]

    def handle(self, text: str) -> State | None:
        key = text.strip().lower()
        if key == "q":
            return LeaveState(self.game, self.title)
        if key == "i":
            return InventoryState(self.game, self.title)
        if key == "?":
            return HelpState(self.game, self.title)
        if key == "l":
            return LogState(self.game, self.title)
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
            return WinState(self.game, self.title)
        if self.game.killed_by is not None:
            return GameOverState(self.game, self.title)
        return self


class InventoryState(_InGameState):
    """What the player is carrying, in the order they picked it up."""

    def draw(self) -> list[str]:
        player = self.game.player
        # The weapon in hand is the first of the strongest kind carried.
        in_hand = player.inventory.index(player.weapon) if player.weapon else None
        items = [
            f"  {item.glyph} {item.name}" + ("   (in hand)" if row == in_hand else "")
            for row, item in enumerate(player.inventory)
        ]
        return [
            "Items",
            "",
            *(items or ["  You aren't carrying anything yet."]),
            "",
            BACK,
        ]

    def handle(self, text: str) -> State | None:
        return PlayingState(self.game, self.title)


class HelpState(_InGameState):
    """The keys, and what they do."""

    def draw(self) -> list[str]:
        return [
            "How to play",
            "",
            "  w a s d   move north, west, south or east",
            "  >         go down the stairs, when you're on them",
            "  i         look at your items",
            "  p         drink a potion, healing 5 hit points",
            "  l         read every message so far",
            "  c         clear the messages",
            "  ?         show this help",
            "  q         leave this game",
            "",
            "Each key acts as soon as you press it. Walk onto an item to pick it up.",
            BACK,
        ]

    def handle(self, text: str) -> State | None:
        return PlayingState(self.game, self.title)


class WinState(_InGameState):
    """The player has found their way out of the dungeon."""

    def draw(self) -> list[str]:
        game = self.game
        return [
            "You escaped the dungeon!",
            "",
            f"You made it through all {game.floors} floors of seed {game.seed},"
            " carrying:",
            *_carried(game),
            "",
            TO_TITLE,
        ]

    def handle(self, text: str) -> State | None:
        return self.title

    def goodbye(self) -> str:
        game = self.game
        return f"Goodbye! You escaped all {game.floors} floors of seed {game.seed}."


class GameOverState(_InGameState):
    """The player's hit points have run out."""

    def draw(self) -> list[str]:
        game = self.game
        return [
            "You died.",
            "",
            f"The {game.killed_by} killed you on level {game.depth} of"
            f" {game.floors} of seed {game.seed}.",
            "You were carrying:",
            *_carried(game),
            "",
            TO_TITLE,
        ]

    def handle(self, text: str) -> State | None:
        return self.title

    def goodbye(self) -> str:
        game = self.game
        return f"Goodbye! You died on level {game.depth} of seed {game.seed}."


class LeaveState(_InGameState):
    """Checking the player meant to press q, since it sits right next to w."""

    def draw(self) -> list[str]:
        return [
            "Leave this game?",
            "",
            f"Your progress on seed {self.game.seed} will be lost.",
            "",
            "  y   Leave",
            "  any other key to keep playing",
        ]

    def handle(self, text: str) -> State | None:
        if text.strip().lower() == "y":
            return self.title
        return PlayingState(self.game, self.title)


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
        return PlayingState(self.game, self.title)


def _carried(game: Game) -> list[str]:
    """The lines listing what the player has with them at the end of a game."""
    items = [f"  {item.glyph} {item.name}" for item in game.player.inventory]
    return items or ["  nothing at all."]


def _frame(lines: list[str], height: int, label: str) -> list[str]:
    """Put a border round `lines`, with `label` in its top edge, first padding
    them with blank lines to `height`."""
    width = len(lines[0])
    padded = lines + [" " * width] * (height - len(lines))
    top = f"+- {label} ".ljust(width + 1, "-") + "+"
    bottom = "+" + "-" * width + "+"
    return [top, *(f"|{line}|" for line in padded), bottom]
