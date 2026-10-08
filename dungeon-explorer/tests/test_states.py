import copy

import pytest
from helpers import game_on, level_from

from dungeon_explorer.game import Game
from dungeon_explorer.generate import ITEMS
from dungeon_explorer.level import Item, Tile
from dungeon_explorer.render import PLAYER, STAIRS_DOWN, draw_mini_map, draw_view
from dungeon_explorer.states import LEGEND, HelpState, InventoryState, PlayingState

POTION = Item("potion", "!")
GOLD = Item("gold", "$")

ROOM = level_from(
    "#####",
    "#...#",
    "#...#",
    "#...#",
    "#####",
)


def test_playing_draws_a_header_the_panels_with_a_legend_and_the_message():
    game = Game.new(seed=42)
    game.message = "A wall is in the way."

    lines = PlayingState(game).draw()

    view, mini_map = draw_view(game), draw_mini_map(game)
    assert lines[0] == "DUNGEON EXPLORER" + " " * 23 + "i inventory   ? help   q quit"
    assert lines[1] == "Level 1   Seed 42"
    assert lines[2] == "+- View " + "-" * 24 + "+ +- Map " + "-" * 26 + "+"
    key = ["Key", "@ you", "# wall", ". floor", "> stairs"]
    key += ["! potion", "$ gold", "? scroll", ") dagger"]
    # The view is 15 lines and the mini-map 16, so the view gets a blank line.
    for row in range(16):
        left = view[row] if row < len(view) else " " * 31
        panels = f"|{left}| |{mini_map[row]}|"
        beside = f"  {key[row]}" if row < len(key) else ""
        assert lines[3 + row] == panels + beside
    assert lines[19] == "+" + "-" * 31 + "+ +" + "-" * 32 + "+"
    assert lines[20] == "A wall is in the way."
    assert len(lines) == 21
    assert max(len(line) for line in lines) <= 80


def test_the_legend_explains_every_symbol_the_playing_screen_can_show():
    glyphs = {glyph for glyph, _ in LEGEND}

    assert {PLAYER, STAIRS_DOWN, Tile.WALL, Tile.FLOOR} <= glyphs
    assert {item.glyph for item in ITEMS} <= glyphs


@pytest.mark.parametrize(
    ("text", "state"),
    [("i", InventoryState), ("I", InventoryState), ("?", HelpState)],
)
def test_playing_opens_the_inventory_and_help_screens(text, state):
    game = game_on(ROOM, position=(2, 2))

    assert isinstance(PlayingState(game).handle(text), state)


def test_playing_quits_on_q():
    game = game_on(ROOM, position=(2, 2))

    assert PlayingState(game).handle("q") is None


def test_playing_runs_commands_and_stays_on_the_playing_screen():
    game = game_on(ROOM, position=(2, 2))
    playing = PlayingState(game)

    assert playing.handle("w") is playing
    assert game.player.position == (2, 1)
    assert playing.handle(">") is playing
    assert game.message == "There are no stairs down here."


def test_playing_says_when_it_doesnt_know_a_command():
    game = game_on(ROOM, position=(2, 2))
    playing = PlayingState(game)

    assert playing.handle(" jump ") is playing
    assert game.message == "Unknown command 'jump'. Press ? for help."
    assert game.player.position == (2, 2)


def test_playing_ignores_an_empty_line():
    game = game_on(ROOM, position=(2, 2))
    game.message = "You pick up the potion."
    before = copy.deepcopy(game)
    playing = PlayingState(game)

    assert playing.handle("") is playing
    assert game == before


def test_the_inventory_lists_what_the_player_carries_in_order():
    game = game_on(ROOM, position=(2, 2))
    game.player.inventory = [POTION, GOLD]

    assert InventoryState(game).draw() == [
        "Inventory",
        "",
        "  ! potion",
        "  $ gold",
        "",
        "Press any key to go back.",
    ]


def test_the_inventory_says_when_it_is_empty():
    game = game_on(ROOM, position=(2, 2))

    assert InventoryState(game).draw() == [
        "Inventory",
        "",
        "  You aren't carrying anything yet.",
        "",
        "Press any key to go back.",
    ]


def test_the_help_lists_every_key():
    lines = HelpState(game_on(ROOM, position=(2, 2))).draw()

    assert lines[0] == "How to play"
    for key in ("w a s d", ">", "i", "?", "q"):
        assert any(line.startswith(f"  {key} ") for line in lines), key


@pytest.mark.parametrize("screen", [InventoryState, HelpState])
@pytest.mark.parametrize("text", ["", "q", "w", "i"])
def test_any_input_on_the_inventory_or_help_goes_back_to_playing(screen, text):
    game = game_on(ROOM, position=(2, 2))
    before = copy.deepcopy(game)

    back = screen(game).handle(text)

    assert isinstance(back, PlayingState)
    assert back.game is game
    # Keys only act on the playing screen, so nothing else changes.
    assert game == before


@pytest.mark.parametrize("screen", [PlayingState, InventoryState, HelpState])
def test_every_screen_of_a_game_says_goodbye_with_its_level_and_seed(screen):
    game = Game.new(seed=42)

    assert screen(game).goodbye() == "Goodbye! You reached level 1 of seed 42."


def test_the_inventory_and_help_open_on_the_same_game():
    game = game_on(ROOM, position=(2, 2))

    assert PlayingState(game).handle("i").game is game
    assert PlayingState(game).handle("?").game is game
