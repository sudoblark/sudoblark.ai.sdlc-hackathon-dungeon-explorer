"""The screens of the game, each drawing itself and handling the player's input.

This is the State pattern from Game Programming Patterns: the game loop only
ever talks to the current state, which says what to draw and which state
comes next. Returning None ends the game. Each state holds whatever it shows,
so a state can start a new game or leave a finished one behind.

The game opens on the title screen. The screens of a game in play hold the
title screen too, so they can go back to it when the game ends.
"""

import textwrap
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

from dungeon_explorer.commands import parse_command
from dungeon_explorer.game import PLAYER_HIT_POINTS, Game
from dungeon_explorer.level import Tile
from dungeon_explorer.render import PLAYER, STAIRS_DOWN, draw_mini_map, draw_view
from dungeon_explorer.settings import DEFAULT_SETTINGS, Settings

BACK = "Press any key to go back."
TO_TITLE = "Press any key to go back to the title."
TITLE = "DUNGEON EXPLORER"
# The title spaced out, for the banner above the game.
BANNER = " ".join(TITLE)
MENU = "i items  p drink  l log  c clear  ? help  q leave"
# The keys that mean Enter: a terminal sends "\n" or "\r", and piped input
# reads an empty line.
ENTER = ("", "\n", "\r")
# Backspace sends DEL on macOS and Linux terminals, and BS on Windows.
BACKSPACE = ("\x7f", "\b")
# Long enough for any seed you'd want to type, short enough to show.
SEED_DIGITS = 9
# How wide screens are inside their edge before there's a game to match:
# the playing screen's width with the default settings.
FRAME_WIDTH = 75
# How many messages the log screen shows at once.
LOG_PAGE = 20


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
    `warnings` are mistakes found in the settings file, shown under the menu
    because the title screen clears anything printed before it.
    """

    seed: int | None
    random_seed: Callable[[], int]
    choice: int = 0
    settings: Settings = DEFAULT_SETTINGS
    warnings: tuple[str, ...] = ()

    OPTIONS = ("New game", "Exit")

    def draw(self) -> list[str]:
        options = [
            f"  > {option} <" if row == self.choice else f"    {option}"
            for row, option in enumerate(self.OPTIONS)
        ]
        lines = [
            "+" + "-" * 30 + "+",
            "|" + TITLE.center(30) + "|",
            "+" + "-" * 30 + "+",
            "",
            *options,
            "",
            "w/s to choose, Enter to pick",
        ]
        if self.warnings:
            lines += ["", "Problems with the settings file:"]
            for warning in self.warnings:
                # Never split a file path, which can be longer than the screen.
                lines += textwrap.wrap(
                    warning,
                    width=76,
                    initial_indent="  ",
                    subsequent_indent="    ",
                    break_on_hyphens=False,
                    break_long_words=False,
                )
        return lines

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
        body = [
            "Type a seed and press Enter, or leave it blank for a random one.",
            "",
            f"  Seed: {self.digits}_",
        ]
        return _framed("New game", body, "Enter to start   q to go back", FRAME_WIDTH)

    def handle(self, text: str) -> State | None:
        if text in ENTER:
            seed = int(self.digits) if self.digits else self.title.random_seed()
            return PlayingState(Game.new(seed, self.title.settings), self.title)
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
        return _goodbye(game, f"You reached level {game.depth} of {_seed(game)}.")

    def _framed(
        self, label: str, body: list[str], keys: str, after: list[str] | None = None
    ) -> list[str]:
        """This screen framed to the playing screen's size, so the edge stays
        exactly where it is as the player moves between them."""
        playing = PlayingState(self.game, self.title).draw()
        return _framed(label, body, keys, len(playing[0]) - 2, after, len(playing))


class PlayingState(_InGameState):
    """The dungeon, framed in one edge: the title banner, the status line, the
    View, Map and Key panels, the newest messages, and the menu."""

    def draw(self) -> list[str]:
        game = self.game
        view, mini_map = draw_view(game), draw_mini_map(game)
        key = [f" {glyph} {name}" for glyph, name in legend(game.settings)]
        height = max(len(view), len(mini_map), len(key))
        status = (
            f"Level {game.depth} of {game.floors}   Seed {game.seed}"
            f" (settings {game.settings.fingerprint})"
        )
        hit_points = f"HP {game.player.hit_points}/{PLAYER_HIT_POINTS}"
        # The Key panel takes any width the panels lack, so the status line,
        # the menu and the banner always fit inside the edge.
        key_width = max(len(line) for line in key) + 1
        needed = max(len(status) + len(hit_points) + 5, len(MENU) + 2, len(BANNER) + 2)
        key_width = max(key_width, needed - len(view[0]) - len(mini_map[0]) - 2)
        width = len(view[0]) + 1 + len(mini_map[0]) + 1 + key_width
        columns = [
            _pad(view, len(view[0]), height),
            _pad(mini_map, len(mini_map[0]), height),
            _pad(key, key_width, height),
        ]
        log_lines = game.settings.log_lines
        newest = [str(message) for message in game.log[-log_lines:]]
        # Blank lines above the newest messages keep the screen the same height.
        messages = [""] * (log_lines - len(newest)) + newest
        return [
            *_banner(width),
            _row(status + hit_points.rjust(width - len(status) - 2), width),
            _labelled_edge(
                [("View", len(view[0])), ("Map", len(mini_map[0])), ("Key", key_width)]
            ),
            *("|" + "|".join(parts) + "|" for parts in zip(*columns, strict=True)),
            _labelled_edge([("Messages", width)]),
            *(_row(message, width) for message in messages),
            _edge(width),
            _row(MENU.center(width - 2), width),
            _edge(width),
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
        body = items or ["  You aren't carrying anything yet."]
        return self._framed("Items", body, BACK)

    def handle(self, text: str) -> State | None:
        return PlayingState(self.game, self.title)


class HelpState(_InGameState):
    """The keys, and what they do."""

    def draw(self) -> list[str]:
        body = [
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
        ]
        return self._framed("How to play", body, BACK)

    def handle(self, text: str) -> State | None:
        return PlayingState(self.game, self.title)


class WinState(_InGameState):
    """The player has found their way out of the dungeon."""

    def draw(self) -> list[str]:
        game = self.game
        body = [
            f"You made it through all {game.floors} floors of seed {game.seed},"
            " carrying:",
            *_carried(game),
        ]
        return self._framed("You escaped the dungeon!", body, TO_TITLE, _replay(game))

    def handle(self, text: str) -> State | None:
        return self.title

    def goodbye(self) -> str:
        game = self.game
        return _goodbye(game, f"You escaped all {game.floors} floors of {_seed(game)}.")


class GameOverState(_InGameState):
    """The player's hit points have run out."""

    def draw(self) -> list[str]:
        game = self.game
        body = [
            f"The {game.killed_by} killed you on level {game.depth} of"
            f" {game.floors} of seed {game.seed}.",
            "You were carrying:",
            *_carried(game),
        ]
        return self._framed("You died", body, TO_TITLE, _replay(game))

    def handle(self, text: str) -> State | None:
        return self.title

    def goodbye(self) -> str:
        game = self.game
        return _goodbye(game, f"You died on level {game.depth} of {_seed(game)}.")


class LeaveState(_InGameState):
    """Checking the player meant to press q, since it sits right next to w."""

    def draw(self) -> list[str]:
        body = [f"Your progress on seed {self.game.seed} will be lost."]
        keys = "y to leave   any other key to keep playing"
        return self._framed("Leave this game?", body, keys)

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
            return self._framed("Message log", ["  No messages yet."], BACK)
        end = len(log) - self.scroll
        start = max(0, end - LOG_PAGE)
        label = f"Message log   {start + 1}-{end} of {len(log)}"
        body = [f"  {message}" for message in log[start:end]]
        keys = "w older   s newer   any other key to go back"
        return self._framed(label, body, keys)

    def handle(self, text: str) -> State | None:
        key = text.strip().lower()
        if key == "w":
            self.scroll = min(self.scroll + 1, max(0, len(self.game.log) - LOG_PAGE))
            return self
        if key == "s":
            self.scroll = max(self.scroll - 1, 0)
            return self
        return PlayingState(self.game, self.title)


def legend(settings: Settings) -> list[tuple[str, str]]:
    """Every symbol the playing screen can show, and what it means."""
    return [
        (PLAYER, "you"),
        (Tile.WALL, "wall"),
        (Tile.FLOOR, "floor"),
        (STAIRS_DOWN, "stairs"),
        *((item.glyph, item.name) for item, _ in settings.items),
        *((monster.glyph, monster.name) for monster, _ in settings.monsters),
    ]


def _seed(game: Game) -> str:
    """The game's seed and settings fingerprint, which together say which
    dungeon it was."""
    return f"seed {game.seed} (settings {game.settings.fingerprint})"


def _goodbye(game: Game, how_it_went: str) -> str:
    """Goodbye, how the game went, and how to replay its settings if needed."""
    return "\n".join([f"Goodbye! {how_it_went}", *_replay(game)])


def _replay(game: Game) -> list[str]:
    """How to play this game's settings again, if they aren't the defaults.
    The code goes on a line of its own, so it can be copied whole however the
    terminal wraps it."""
    code = game.settings.code
    if code is None:
        return []
    return ["Replay these settings with:", f"--settings-code {code}"]


def _carried(game: Game) -> list[str]:
    """The lines listing what the player has with them at the end of a game."""
    items = [f"  {item.glyph} {item.name}" for item in game.player.inventory]
    return items or ["  nothing at all."]


def _framed(
    label: str,
    body: list[str],
    keys: str,
    width: int,
    after: list[str] | None = None,
    height: int = 0,
) -> list[str]:
    """A screen in the game's edge: the title banner, a panel labelled `label`
    holding `body`, and a bar saying what the `keys` do. It's at least `width`
    inside and `height` tall, and bigger if its text needs it. Lines `after`
    go below the edge, unframed, so a code to copy is never cut short or mixed
    with the edge."""
    # The banner, labelled edge, blank lines, bar and edges take 9 lines.
    body = body + [""] * (height - 9 - len(body))
    width = max(
        width,
        *(len(line) + 2 for line in body),
        len(keys) + 2,
        len(label) + 6,
        len(BANNER) + 2,
    )
    return [
        *_banner(width),
        _labelled_edge([(label, width)]),
        _row("", width),
        *(_row(line, width) for line in body),
        _row("", width),
        _edge(width),
        _row(keys.center(width - 2), width),
        _edge(width),
        *(after or []),
    ]


def _banner(width: int) -> list[str]:
    """The title in a box of its own, `width` inside, to sit above the game."""
    return [_edge(width, "="), _row(BANNER.center(width - 2), width), _edge(width, "=")]


def _edge(width: int, fill: str = "-") -> str:
    """A border `width` inside, such as the top or bottom of a box."""
    return "+" + fill * width + "+"


def _labelled_edge(panels: list[tuple[str, int]]) -> str:
    """The border along the tops of panels side by side, each with its label,
    and sharing the borders between them. A panel too narrow for its label
    goes without, so the border still lines up."""
    edges = []
    for label, width in panels:
        labelled = f"-- {label} "
        edges.append(
            labelled.ljust(width, "-") if len(labelled) <= width else "-" * width
        )
    return "+" + "+".join(edges) + "+"


def _row(text: str, width: int) -> str:
    """A line of a box `width` inside, with a space before `text`. Anything
    too long is cut short, so the edge always lines up."""
    return "| " + text[: width - 2].ljust(width - 2) + " |"


def _pad(lines: list[str], width: int, height: int) -> list[str]:
    """`lines` made `width` wide and `height` tall with blank space."""
    return [line.ljust(width) for line in lines] + [" " * width] * (height - len(lines))
