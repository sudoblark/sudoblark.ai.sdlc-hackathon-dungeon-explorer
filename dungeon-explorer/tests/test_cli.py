import re
from collections.abc import Callable

import pytest
from helpers import game_on, level_from

from dungeon_explorer import cli
from dungeon_explorer.cli import CLEAR_SCREEN, game_loop, main
from dungeon_explorer.game import Game
from dungeon_explorer.states import InventoryState, PlayingState

ROOM = level_from(
    "#####",
    "#...#",
    "#...#",
    "#####",
)


def _script(*lines: str) -> Callable[[str], str]:
    """Stands in for input(): answers with `lines` in turn, then runs out."""
    answers = iter(lines)

    def read_line(prompt: str) -> str:
        assert prompt == "> "
        try:
            return next(answers)
        except StopIteration:
            raise EOFError from None

    return read_line


def test_the_loop_draws_each_screen_and_hands_each_line_to_it():
    game = game_on(ROOM, position=(1, 1))
    drawn: list[str] = []

    game_loop(game, read_line=_script("d", "i", "", "q"), write=drawn.append)

    playing, inventory = PlayingState(), InventoryState()
    assert drawn[0] == "\n".join(playing.draw(game_on(ROOM, position=(1, 1))))
    assert drawn[2] == "\n".join(inventory.draw(game))
    assert len(drawn) == 5  # four screens, then goodbye
    assert game.player.position == (2, 1)


def test_quitting_says_goodbye_with_the_level_and_seed():
    game = Game.new(seed=42)
    drawn: list[str] = []

    game_loop(game, read_line=_script("q"), write=drawn.append)

    assert drawn[-1] == "Goodbye! You reached level 1 of seed 42."


def test_the_loop_stops_when_the_input_runs_out():
    game = game_on(ROOM, position=(1, 1))
    drawn: list[str] = []

    game_loop(game, read_line=_script("d"), write=drawn.append)

    assert len(drawn) == 3  # two screens, then goodbye
    assert drawn[-1].startswith("Goodbye!")


def test_the_loop_clears_the_terminal_before_each_screen_when_asked():
    game = game_on(ROOM, position=(1, 1))
    drawn: list[str] = []

    game_loop(game, read_line=_script("d", "q"), write=drawn.append, clear=True)

    screens, goodbye = drawn[:-1], drawn[-1]
    assert all(screen.startswith(CLEAR_SCREEN) for screen in screens)
    assert not goodbye.startswith(CLEAR_SCREEN)


def _play(monkeypatch, capsys, argv: list[str], *lines: str) -> tuple[int, str]:
    """Run the command line with `lines` as the player's input."""
    monkeypatch.setattr("builtins.input", _script(*lines))
    code = main(argv)
    return code, capsys.readouterr().out


def test_the_command_plays_the_seed_it_is_given(monkeypatch, capsys):
    code, out = _play(monkeypatch, capsys, ["--seed", "42"], "q")

    assert code == 0
    assert out.startswith("Level 1   Seed 42   ? for help\n")
    assert CLEAR_SCREEN not in out  # output isn't a terminal under test


def test_the_same_seed_draws_the_same_game(monkeypatch, capsys):
    moves = ("d", "d", "w", "w", "w", "q")
    _, first = _play(monkeypatch, capsys, ["--seed", "42"], *moves)
    _, second = _play(monkeypatch, capsys, ["--seed", "42"], *moves)
    _, other = _play(monkeypatch, capsys, ["--seed", "43"], *moves)

    assert first == second
    assert first != other


def test_without_a_seed_the_command_picks_one_and_shows_it(monkeypatch, capsys):
    monkeypatch.setattr(cli.random, "randrange", lambda _: 123456)

    _, out = _play(monkeypatch, capsys, [], "q")

    assert "Seed 123456" in out.splitlines()[0]
    assert re.search(r"Goodbye! You reached level 1 of seed 123456\.$", out.strip())


def test_a_seed_must_be_a_whole_number(capsys):
    with pytest.raises(SystemExit) as error:
        main(["--seed", "dragon"])

    assert error.value.code == 2
    assert "invalid int value: 'dragon'" in capsys.readouterr().err
