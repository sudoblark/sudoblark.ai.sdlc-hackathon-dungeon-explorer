import os
import re
from collections.abc import Callable

import pytest
from helpers import game_on, level_from

from dungeon_explorer import cli
from dungeon_explorer.cli import (
    CLEAR_SCREEN,
    HIDE_CURSOR,
    SHOW_CURSOR,
    _key_from,
    centre,
    cursor_hidden,
    game_loop,
    main,
)
from dungeon_explorer.game import Game
from dungeon_explorer.generate import floor_count
from dungeon_explorer.level import Monster
from dungeon_explorer.settings import DEFAULT_SETTINGS, Settings
from dungeon_explorer.states import InventoryState, PlayingState

# Piped input for the menus: an empty line is Enter.
START = ("", "")  # New game, keeping the seed already filled in
LEAVE = ("q", "y")  # leave the game for the title screen
EXIT = ("s", "")  # move down to Exit and pick it

# The fingerprint of the default settings, and of two-floor settings.
FP = DEFAULT_SETTINGS.fingerprint
TWO_FLOORS = Settings(min_floors=2, max_floors=2).fingerprint

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


def _status(out: str) -> str:
    """The first status line in `out`, without the screen's edge or the padding
    that pushes the hit points to the right."""
    line = next(line for line in out.splitlines() if "   Seed " in line)
    return re.sub(" {3,}", "   ", line.strip("| "))


def test_the_loop_draws_each_screen_and_hands_each_line_to_it():
    game = game_on(ROOM, position=(1, 1))
    drawn: list[str] = []

    game_loop(PlayingState(game), _script("d", "i", "", "q"), drawn.append)

    start = PlayingState(game_on(ROOM, position=(1, 1)))
    assert drawn[0] == "\n".join(start.draw())
    assert drawn[2] == "\n".join(InventoryState(game).draw())
    assert "-- Leave this game? " in drawn[4]
    assert len(drawn) == 6  # five screens, then goodbye
    assert game.player.position == (2, 1)


def test_leaving_a_game_says_goodbye_with_the_level_and_seed():
    game = Game.new(seed=42)
    drawn: list[str] = []

    game_loop(PlayingState(game), _script(*LEAVE), drawn.append)

    assert drawn[-1] == f"Goodbye! You reached level 1 of seed 42 (settings {FP})."


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


def test_the_command_opens_on_the_title_screen(monkeypatch, capsys):
    code, out = _play(monkeypatch, capsys, ["--seed", "42"], *EXIT)

    assert code == 0
    assert "|       DUNGEON EXPLORER       |" in out
    assert out.strip().endswith("Goodbye!")
    assert CLEAR_SCREEN not in out  # output isn't a terminal under test


def test_a_new_game_plays_the_seed_given_on_the_command_line(monkeypatch, capsys):
    script = (*START, *LEAVE, *EXIT)

    code, out = _play(monkeypatch, capsys, ["--seed", "42"], *script)

    assert code == 0
    assert (
        _status(out)
        == f"Level 1 of {floor_count(42)}   Seed 42 (settings {FP})   HP 20/20"
    )
    assert out.strip().endswith("Goodbye!")


def test_a_typed_seed_replaces_the_one_filled_in(monkeypatch, capsys):
    # Enter on New game, delete the 42 filled in, type 7, then Enter.
    script = ("", "\x7f", "\x7f", "7", "", *LEAVE, *EXIT)

    _, out = _play(monkeypatch, capsys, ["--seed", "42"], *script)

    assert (
        _status(out)
        == f"Level 1 of {floor_count(7)}   Seed 7 (settings {FP})   HP 20/20"
    )


def test_the_same_seed_draws_the_same_game(monkeypatch, capsys):
    moves = (*START, "d", "d", "w", "w", "w", *LEAVE, *EXIT)
    _, first = _play(monkeypatch, capsys, ["--seed", "42"], *moves)
    _, second = _play(monkeypatch, capsys, ["--seed", "42"], *moves)
    _, other = _play(monkeypatch, capsys, ["--seed", "43"], *moves)

    assert first == second
    assert first != other


def test_without_a_seed_the_command_picks_one_and_shows_it(monkeypatch, capsys):
    monkeypatch.setattr(cli.random, "randrange", lambda _: 123456)

    _, out = _play(monkeypatch, capsys, [], *START, "d")

    assert (
        _status(out)
        == f"Level 1 of {floor_count(123456)}   Seed 123456 (settings {FP})   HP 20/20"
    )
    assert out.strip().endswith(f"You reached level 1 of seed 123456 (settings {FP}).")


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
    # In a terminal, Enter arrives as a newline.
    monkeypatch.setattr(cli, "read_key", _script("\n", "\n", "d"))
    monkeypatch.setattr("builtins.input", _refuse)

    assert main(["--seed", "42"]) == 0
    assert (
        f"Goodbye! You reached level 1 of seed 42 (settings {FP})."
        in capsys.readouterr().out
    )


def test_piped_input_is_read_a_line_at_a_time(monkeypatch, capsys):
    monkeypatch.setattr(cli.sys, "stdin", _Stdin(terminal=False))
    monkeypatch.setattr(cli, "read_key", _refuse)
    monkeypatch.setattr("builtins.input", _script(*START, "d"))

    assert main(["--seed", "42"]) == 0
    assert (
        f"Goodbye! You reached level 1 of seed 42 (settings {FP})."
        in capsys.readouterr().out
    )


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


def test_reading_a_key_skips_arrows_and_escape(monkeypatch):
    sent = iter(["\x1b[A", "\x1b", "w"])
    monkeypatch.setattr(cli, "_read_unix_key", lambda: next(sent))
    monkeypatch.setattr(cli, "_read_windows_key", lambda: next(sent))

    assert cli.read_key() == "w"


def test_ctrl_c_interrupts_as_it_does_at_a_prompt():
    with pytest.raises(KeyboardInterrupt):
        _key_from("\x03")


@pytest.mark.parametrize("raw", ["\x04", ""])
def test_ctrl_d_or_a_closed_terminal_ends_the_input(raw):
    with pytest.raises(EOFError):
        _key_from(raw)


def test_finishing_the_dungeon_ends_the_loop_on_the_win_screen():
    # Seed 1's dungeon has three floors: walk it with the stairs.
    game = Game.new(seed=1)
    while game.depth < game.floors:
        game.player.position = game.level.stairs_down
        game.descend()
    game.player.position = game.level.stairs_down
    drawn: list[str] = []

    game_loop(PlayingState(game), _script(">", "x", "never read"), drawn.append)

    assert "-- You escaped the dungeon! " in drawn[1]
    assert drawn[-1] == f"Goodbye! You escaped all 3 floors of seed 1 (settings {FP})."
    assert len(drawn) == 3  # playing, win, goodbye


def test_dying_ends_the_loop_on_the_game_over_screen():
    game = Game.new(seed=1)
    x, y = game.player.position
    game.level.monsters = [Monster("goblin", "g", 4, 2, position=(x + 1, y))]
    game.player.hit_points = 1
    drawn: list[str] = []

    game_loop(PlayingState(game), _script("d", "x", "never read"), drawn.append)

    assert "-- You died " in drawn[1]
    assert drawn[-1] == f"Goodbye! You died on level 1 of seed 1 (settings {FP})."
    assert len(drawn) == 3  # playing, game over, goodbye


def test_the_command_plays_with_the_settings_file_it_is_given(
    monkeypatch, capsys, tmp_path
):
    mine = tmp_path / "mine.toml"
    mine.write_text("[dungeon]\nmin_floors = 2\nmax_floors = 2\n")
    argv = ["--seed", "42", "--settings", str(mine)]

    _, out = _play(monkeypatch, capsys, argv, *START, *LEAVE, *EXIT)

    assert _status(out) == f"Level 1 of 2   Seed 42 (settings {TWO_FLOORS})   HP 20/20"


def test_settings_toml_in_the_folder_is_read_without_asking(
    monkeypatch, capsys, tmp_path
):
    (tmp_path / "settings.toml").write_text(
        "[dungeon]\nmin_floors = 2\nmax_floors = 2\n"
    )
    monkeypatch.chdir(tmp_path)

    _, out = _play(monkeypatch, capsys, ["--seed", "42"], *START, *LEAVE, *EXIT)

    assert _status(out) == f"Level 1 of 2   Seed 42 (settings {TWO_FLOORS})   HP 20/20"


def test_problems_with_the_settings_show_on_the_title_screen(
    monkeypatch, capsys, tmp_path
):
    missing = tmp_path / "missing.toml"

    _, out = _play(monkeypatch, capsys, ["--settings", str(missing)], *EXIT)

    assert "Problems with the settings file:" in out
    # A long path may wrap across lines inside the edge, but none of it is lost.
    inside = "".join(line.strip("| ") for line in out.splitlines())
    assert "".join(f"{missing} doesn't exist".split()) in "".join(inside.split())


def test_the_command_plays_with_the_settings_a_code_gives(monkeypatch, capsys):
    code = Settings(min_floors=2, max_floors=2).code

    _, out = _play(
        monkeypatch, capsys, ["--seed", "42", "--settings-code", code], *START, "d"
    )

    assert _status(out) == f"Level 1 of 2   Seed 42 (settings {TWO_FLOORS})   HP 20/20"
    assert out.strip().endswith(f"--settings-code {code}")


def test_a_settings_file_and_a_code_cant_both_be_given(capsys):
    with pytest.raises(SystemExit) as error:
        main(["--settings", "mine.toml", "--settings-code", "abc"])

    assert error.value.code == 2
    assert "not allowed with argument" in capsys.readouterr().err


def test_a_code_that_cant_be_read_is_reported_on_the_title_screen(monkeypatch, capsys):
    _, out = _play(monkeypatch, capsys, ["--settings-code", "not-a-code"], *EXIT)

    assert "Problems with the settings file:" in out
    assert "the settings code can't be read, so the defaults are used" in out


def _size(columns: int, lines: int) -> os.terminal_size:
    return os.terminal_size((columns, lines))


def test_a_screen_is_centred_across_and_down_in_a_bigger_terminal():
    screen = "abcd\nef"

    # 4 wide and 2 tall in 10 by 6: 3 columns in, 2 lines down.
    assert centre(screen, _size(10, 6)) == "\n\n   abcd\n   ef"


def test_a_centred_screen_keeps_its_lines_lined_up_and_blank_lines_empty():
    screen = "+--+\n\n|ab|"

    assert centre(screen, _size(8, 3)).split("\n") == ["  +--+", "", "  |ab|"]


def test_an_odd_space_left_over_goes_to_the_right_and_bottom():
    assert centre("ab", _size(5, 2)) == " ab"


def test_a_screen_too_big_for_the_terminal_stays_in_the_top_left():
    screen = "x" * 100 + "\n" + "y"

    assert centre(screen, _size(80, 1)) == screen


def test_the_loop_centres_each_screen_when_it_can_measure_the_terminal():
    game = game_on(ROOM, position=(1, 1))
    first_screen = "\n".join(PlayingState(game_on(ROOM, position=(1, 1))).draw())
    drawn: list[str] = []
    # The terminal shrinks between turns, so each screen is measured afresh.
    sizes = iter([_size(120, 40), _size(100, 30)])

    game_loop(
        PlayingState(game),
        _script("d"),
        drawn.append,
        terminal_size=lambda: next(sizes),
    )

    second_screen = "\n".join(PlayingState(game).draw())
    assert drawn[0] == centre(first_screen, _size(120, 40))
    assert drawn[1] == centre(second_screen, _size(100, 30))
    assert drawn[0] != first_screen


def test_without_a_terminal_the_screens_are_drawn_as_they_are():
    game = game_on(ROOM, position=(1, 1))
    drawn: list[str] = []

    game_loop(PlayingState(game), _script(), drawn.append)

    assert drawn[0] == "\n".join(PlayingState(game).draw())


def test_the_cursor_is_hidden_inside_and_shown_again_after():
    written: list[str] = []

    with cursor_hidden(written.append):
        assert written == [HIDE_CURSOR]

    assert written == [HIDE_CURSOR, SHOW_CURSOR]


@pytest.mark.parametrize("error", [KeyboardInterrupt, RuntimeError])
def test_the_cursor_comes_back_even_when_the_game_is_interrupted(error):
    written: list[str] = []

    with pytest.raises(error), cursor_hidden(written.append):
        raise error

    assert written == [HIDE_CURSOR, SHOW_CURSOR]


def _in_a_terminal(monkeypatch) -> None:
    """Make main think it's playing in a terminal 100 by 40."""
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(cli.sys, "stdin", _Stdin(terminal=True))
    monkeypatch.setattr(cli.shutil, "get_terminal_size", lambda: _size(100, 40))


def test_in_a_terminal_the_cursor_is_hidden_for_the_whole_game(monkeypatch, capsys):
    _in_a_terminal(monkeypatch)
    monkeypatch.setattr(cli, "read_key", _script(*EXIT))

    assert main(["--seed", "42"]) == 0

    out = capsys.readouterr().out
    assert out.startswith(HIDE_CURSOR)
    assert out.endswith(SHOW_CURSOR)
    assert out.count(HIDE_CURSOR) == out.count(SHOW_CURSOR) == 1


def test_after_ctrl_c_the_cursor_is_shown_again(monkeypatch, capsys):
    _in_a_terminal(monkeypatch)

    def ctrl_c(prompt: str) -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "read_key", ctrl_c)

    assert main(["--seed", "42"]) == 130
    assert SHOW_CURSOR in capsys.readouterr().out


def test_piped_output_never_hides_the_cursor(monkeypatch, capsys):
    _, out = _play(monkeypatch, capsys, ["--seed", "42"], *EXIT)

    assert HIDE_CURSOR not in out
    assert SHOW_CURSOR not in out
