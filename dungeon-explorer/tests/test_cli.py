import re
from collections.abc import Callable

import pytest
from helpers import game_on, level_from

from dungeon_explorer import cli
from dungeon_explorer.cli import CLEAR_SCREEN, _key_from, game_loop, main
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

    game_loop(PlayingState(game), _script("d", "i", "", "q"), drawn.append)

    start = PlayingState(game_on(ROOM, position=(1, 1)))
    assert drawn[0] == "\n".join(start.draw())
    assert drawn[2] == "\n".join(InventoryState(game).draw())
    assert len(drawn) == 5  # four screens, then goodbye
    assert game.player.position == (2, 1)


def test_quitting_says_goodbye_with_the_level_and_seed():
    game = Game.new(seed=42)
    drawn: list[str] = []

    game_loop(PlayingState(game), _script("q"), drawn.append)

    assert drawn[-1] == "Goodbye! You reached level 1 of seed 42."


def test_the_loop_stops_when_the_input_runs_out():
    game = game_on(ROOM, position=(1, 1))
    drawn: list[str] = []

    game_loop(PlayingState(game), _script("d"), drawn.append)

    assert len(drawn) == 3  # two screens, then goodbye
    assert drawn[-1].startswith("Goodbye!")


def test_the_loop_clears_the_terminal_before_each_screen_when_asked():
    game = game_on(ROOM, position=(1, 1))
    drawn: list[str] = []

    game_loop(PlayingState(game), _script("d", "q"), drawn.append, clear=True)

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


class _Stdin:
    """Stands in for sys.stdin, saying whether it's a terminal."""

    def __init__(self, terminal: bool) -> None:
        self.terminal = terminal

    def isatty(self) -> bool:
        return self.terminal


def _refuse(prompt: str) -> str:
    raise AssertionError("read input the wrong way")


def test_in_a_terminal_the_command_reads_single_keys(monkeypatch, capsys):
    monkeypatch.setattr(cli.sys, "stdin", _Stdin(terminal=True))
    monkeypatch.setattr(cli, "read_key", _script("d", "q"))
    monkeypatch.setattr("builtins.input", _refuse)

    assert main(["--seed", "42"]) == 0
    assert "Goodbye! You reached level 1 of seed 42." in capsys.readouterr().out


def test_piped_input_is_read_a_line_at_a_time(monkeypatch, capsys):
    monkeypatch.setattr(cli.sys, "stdin", _Stdin(terminal=False))
    monkeypatch.setattr(cli, "read_key", _refuse)
    monkeypatch.setattr("builtins.input", _script("d", "q"))

    assert main(["--seed", "42"]) == 0
    assert "Goodbye! You reached level 1 of seed 42." in capsys.readouterr().out


@pytest.mark.parametrize(
    ("raw", "key"),
    [
        ("w", "w"),
        (">", ">"),
        ("\n", "\n"),  # Enter, which the screens treat as an empty line
        ("\x1b[A", ""),  # the up arrow's escape sequence
        ("\x1b", ""),  # Escape on its own
    ],
)
def test_keys_come_back_as_pressed_and_escapes_are_ignored(raw, key):
    assert _key_from(raw) == key


def test_ctrl_c_interrupts_as_it_does_at_a_prompt():
    with pytest.raises(KeyboardInterrupt):
        _key_from("\x03")


@pytest.mark.parametrize("raw", ["\x04", ""])
def test_ctrl_d_or_a_closed_terminal_ends_the_input(raw):
    with pytest.raises(EOFError):
        _key_from(raw)
