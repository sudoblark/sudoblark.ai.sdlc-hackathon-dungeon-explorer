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
import sys
from collections.abc import Callable

from dungeon_explorer.game import Game
from dungeon_explorer.states import PlayingState, State

PROMPT = "> "
# ANSI codes to clear the terminal and move to its top left, so each turn
# redraws the screen in place.
CLEAR_SCREEN = "\033[2J\033[H"
# Seeds picked for you stay short enough to type back in.
RANDOM_SEEDS = 1_000_000


def game_loop(
    game: Game,
    read_line: Callable[[str], str],
    write: Callable[[str], None],
    clear: bool = False,
) -> None:
    """Play `game` until the player quits or the input runs out.

    `read_line` and `write` work like input() and print(). main passes in
    read_key or input, and print, so tests can script the player's input and
    collect what's drawn.
    """
    state: State | None = PlayingState()
    while state is not None:
        screen = "\n".join(state.draw(game))
        write(CLEAR_SCREEN + screen if clear else screen)
        try:
            text = read_line(PROMPT)
        except EOFError:
            break
        state = state.handle(game, text)
    write(f"Goodbye! You reached level {game.depth} of seed {game.seed}.")


def main(argv: list[str] | None = None) -> int:
    """Start a game from the command line, and return the exit code."""
    parser = argparse.ArgumentParser(
        prog="dungeon-explorer",
        description="A turn-based ASCII dungeon explorer, generated from a seed.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="the dungeon to explore; the same seed always gives the same "
        "dungeon (default: a random one, shown on screen)",
    )
    args = parser.parse_args(argv)
    seed = args.seed if args.seed is not None else random.randrange(RANDOM_SEEDS)
    try:
        read = read_key if sys.stdin.isatty() else input
        game_loop(Game.new(seed), read, print, clear=sys.stdout.isatty())
    except KeyboardInterrupt:
        print()
        return 130
    return 0


def read_key(prompt: str = "") -> str:
    """Wait for one keypress in the terminal and return it, without Enter.

    `prompt` is ignored, because the screen is redrawn after every key.
    Ctrl-C raises KeyboardInterrupt and Ctrl-D raises EOFError, as they do
    for input().
    """
    if sys.platform == "win32":
        return _key_from(_read_windows_key())
    return _key_from(_read_unix_key())


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
