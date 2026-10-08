import copy

import pytest
from helpers import game_on, level_from

from dungeon_explorer.game import Game
from dungeon_explorer.level import Item
from dungeon_explorer.render import draw_mini_map, draw_view
from dungeon_explorer.states import HelpState, InventoryState, PlayingState

POTION = Item("potion", "!")
GOLD = Item("gold", "$")

ROOM = level_from(
    "#####",
    "#...#",
    "#...#",
    "#...#",
    "#####",
)


def test_playing_draws_the_status_framed_view_and_mini_map_then_the_message():
    game = Game.new(seed=42)
    game.message = "A wall is in the way."

    lines = PlayingState().draw(game)

    view, mini_map = draw_view(game), draw_mini_map(game)
    assert lines[0] == "Level 1   Seed 42   ? for help"
    assert lines[1] == "+" + "-" * 31 + "+ +" + "-" * 32 + "+"
    # The view is 15 lines and the mini-map 16, so the view gets a blank line.
    for row in range(16):
        left = view[row] if row < len(view) else " " * 31
        assert lines[2 + row] == f"|{left}| |{mini_map[row]}|"
    assert lines[18] == lines[1]
    assert lines[19] == "A wall is in the way."
    assert len(lines) == 20
    assert max(len(line) for line in lines) <= 80


@pytest.mark.parametrize(
    ("text", "state"),
    [("i", InventoryState), ("I", InventoryState), ("?", HelpState)],
)
def test_playing_opens_the_inventory_and_help_screens(text, state):
    game = game_on(ROOM, position=(2, 2))

    assert isinstance(PlayingState().handle(game, text), state)


def test_playing_quits_on_q():
    game = game_on(ROOM, position=(2, 2))

    assert PlayingState().handle(game, "q") is None


def test_playing_runs_commands_and_stays_on_the_playing_screen():
    game = game_on(ROOM, position=(2, 2))
    playing = PlayingState()

    assert playing.handle(game, "w") is playing
    assert game.player.position == (2, 1)
    assert playing.handle(game, ">") is playing
    assert game.message == "There are no stairs down here."


def test_playing_says_when_it_doesnt_know_a_command():
    game = game_on(ROOM, position=(2, 2))
    playing = PlayingState()

    assert playing.handle(game, " jump ") is playing
    assert game.message == "Unknown command 'jump'. Press ? for help."
    assert game.player.position == (2, 2)


def test_playing_ignores_an_empty_line():
    game = game_on(ROOM, position=(2, 2))
    game.message = "You pick up the potion."
    before = copy.deepcopy(game)
    playing = PlayingState()

    assert playing.handle(game, "") is playing
    assert game == before


def test_the_inventory_lists_what_the_player_carries_in_order():
    game = game_on(ROOM, position=(2, 2))
    game.player.inventory = [POTION, GOLD]

    assert InventoryState().draw(game) == [
        "Inventory",
        "",
        "  ! potion",
        "  $ gold",
        "",
        "Press any key to go back.",
    ]


def test_the_inventory_says_when_it_is_empty():
    game = game_on(ROOM, position=(2, 2))

    assert InventoryState().draw(game) == [
        "Inventory",
        "",
        "  You aren't carrying anything yet.",
        "",
        "Press any key to go back.",
    ]


def test_the_help_lists_every_key():
    lines = HelpState().draw(game_on(ROOM, position=(2, 2)))

    assert lines[0] == "How to play"
    for key in ("w a s d", ">", "i", "?", "q"):
        assert any(line.startswith(f"  {key} ") for line in lines), key


@pytest.mark.parametrize("state", [InventoryState(), HelpState()])
@pytest.mark.parametrize("text", ["", "q", "w", "i"])
def test_any_input_on_the_inventory_or_help_goes_back_to_playing(state, text):
    game = game_on(ROOM, position=(2, 2))
    before = copy.deepcopy(game)

    assert isinstance(state.handle(game, text), PlayingState)
    # Keys only act on the playing screen, so nothing else changes.
    assert game == before
