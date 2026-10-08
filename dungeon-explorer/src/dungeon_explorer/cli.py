"""Runs the game in the terminal: the only module that reads input or prints.

This is the Game Loop from Game Programming Patterns, in its simplest,
turn-based form: draw the current state, wait for a line of input, hand it
to the state, and go round again until there's no next state.
"""

import argparse
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

    `read_line` and `write` work like input() and print(), which main passes
    in, so tests can script the player's input and collect what's drawn.
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
        game_loop(Game.new(seed), input, print, clear=sys.stdout.isatty())
    except KeyboardInterrupt:
        print()
        return 130
    return 0
