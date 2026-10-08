"""Runs the game in the terminal: the only module that reads input or prints.

This is the Game Loop from Game Programming Patterns, in its simplest,
turn-based form: draw the current state, wait for the player's input, hand
it to the state, and go round again until there's no next state.

In a terminal each keypress counts straight away. When input is piped in,
it's read a line at a time instead, so scripted runs work the same anywhere.
"""

import argparse
import os
import random
import shutil
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager, nullcontext
from pathlib import Path

from dungeon_explorer.settings import load_settings, load_settings_code
from dungeon_explorer.states import State, TitleState

PROMPT = "> "
# ANSI codes to clear the terminal and move to its top left, so each turn
# redraws the screen in place.
CLEAR_SCREEN = "\033[2J\033[H"
# ANSI codes to hide the terminal's blinking cursor, and to show it again.
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
# Seeds picked for you stay short enough to type back in.
RANDOM_SEEDS = 1_000_000
# Read from the folder the game runs in, unless --settings names another file.
SETTINGS_FILE = Path("settings.toml")


def game_loop(
    state: State,
    read_line: Callable[[str], str],
    write: Callable[[str], None],
    clear: bool = False,
    terminal_size: Callable[[], os.terminal_size] | None = None,
) -> None:
    """Show `state`, then each state it leads to, until the player quits or
    the input runs out. The last state shown says goodbye.

    `read_line` and `write` work like input() and print(). main passes in
    read_key or input, and print, so tests can script the player's input and
    collect what's drawn. Given `terminal_size`, each screen is centred in the
    terminal, measured afresh every turn in case it's been resized.
    """
    while True:
        screen = "\n".join(state.draw())
        if terminal_size is not None:
            screen = centre(screen, terminal_size())
        write(CLEAR_SCREEN + screen if clear else screen)
        try:
            text = read_line(PROMPT)
        except EOFError:
            break
        next_state = state.handle(text)
        if next_state is None:
            break
        state = next_state
    write(state.goodbye())


def centre(screen: str, size: os.terminal_size) -> str:
    """`screen` moved to the middle of a terminal of `size`.

    It moves as one block, so its lines stay lined up with each other. A
    screen too big for the terminal stays in the top left.
    """
    lines = screen.split("\n")
    width = max(len(line) for line in lines)
    left = " " * max((size.columns - width) // 2, 0)
    top = max((size.lines - len(lines)) // 2, 0)
    return "\n" * top + "\n".join(left + line if line else line for line in lines)


def main(argv: list[str] | None = None) -> int:
    """Start a game from the command line, and return the exit code."""
    parser = argparse.ArgumentParser(
        prog="dungeon-explorer",
        description="A turn-based ASCII dungeon explorer, generated from a seed.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="fill in the seed for a new game; the same seed always gives the "
        "same dungeon (default: a random one, shown on screen)",
    )
    # One or the other: a code already holds every setting it changes.
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument(
        "--settings",
        type=Path,
        help=f"the settings file to play with (default: {SETTINGS_FILE}, if there "
        "is one; otherwise the built-in settings)",
    )
    choice.add_argument(
        "--settings-code",
        metavar="CODE",
        help="play with the settings a code from the end of another game gives",
    )
    args = parser.parse_args(argv)
    if args.settings_code is not None:
        settings, warnings = load_settings_code(args.settings_code)
    else:
        path = args.settings or SETTINGS_FILE
        settings, warnings = load_settings(path, required=args.settings is not None)
    title = TitleState(
        args.seed,
        lambda: random.randrange(RANDOM_SEEDS),
        settings=settings,
        warnings=tuple(warnings),
    )
    read = read_key if sys.stdin.isatty() else input
    # Only a terminal is cleared, centred and has its cursor hidden: piped
    # output stays as drawn.
    terminal = sys.stdout.isatty()
    size = shutil.get_terminal_size if terminal else None
    try:
        with cursor_hidden(_write_code) if terminal else nullcontext():
            game_loop(title, read, print, clear=terminal, terminal_size=size)
    except KeyboardInterrupt:
        print()
        return 130
    return 0


@contextmanager
def cursor_hidden(write: Callable[[str], None]) -> Iterator[None]:
    """Hide the terminal's cursor inside the `with`, and always show it again,
    whether the game ends normally, by Ctrl-C or with an error, so the terminal
    is never left without one."""
    write(HIDE_CURSOR)
    try:
        yield
    finally:
        write(SHOW_CURSOR)


def _write_code(code: str) -> None:
    """Send a terminal code straight away, without a newline."""
    print(code, end="", flush=True)


def read_key(prompt: str = "") -> str:
    """Wait for one keypress in the terminal and return it, without Enter.

    `prompt` is ignored, because the screen is redrawn after every key. Keys
    that send an escape, such as arrows, are skipped, so they can't be taken
    for Enter. Ctrl-C raises KeyboardInterrupt and Ctrl-D raises EOFError, as
    they do for input().
    """
    while True:
        if sys.platform == "win32":
            key = _key_from(_read_windows_key())
        else:
            key = _key_from(_read_unix_key())
        if key:
            return key


def _read_unix_key() -> str:
    import termios
    import tty

    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    try:
        # cbreak hands over each key at once without echoing it, but unlike
        # raw mode it still turns Ctrl-C into KeyboardInterrupt.
        tty.setcbreak(fd)
        # One read takes every byte of a key such as an arrow, which sends an
        # escape sequence, so none of it is left over to act as the next key.
        return os.read(fd, 32).decode(errors="replace")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)


def _read_windows_key() -> str:
    import msvcrt

    key = msvcrt.getwch()
    if key in ("\x00", "\xe0"):
        # Arrow and function keys arrive as two characters: take the second
        # too, and report the pair as an escape for _key_from to ignore.
        msvcrt.getwch()
        return "\x1b"
    return key


def _key_from(raw: str) -> str:
    """The key the player pressed, from what the terminal sent.

    Ctrl-C and Ctrl-D act as they do at a prompt, as does the terminal
    closing. Keys that send an escape, such as arrows, come back empty, so
    the game ignores them.
    """
    if raw == "\x03":
        raise KeyboardInterrupt
    if raw in ("", "\x04"):
        raise EOFError
    if raw.startswith("\x1b") or len(raw) != 1:
        return ""
    return raw
