import copy

import pytest
from helpers import game_on, level_from

from dungeon_explorer.game import Game
from dungeon_explorer.generate import ITEMS, floor_count
from dungeon_explorer.level import Item, Tile
from dungeon_explorer.render import PLAYER, STAIRS_DOWN, draw_mini_map, draw_view
from dungeon_explorer.states import (
    LEGEND,
    HelpState,
    InventoryState,
    LogState,
    PlayingState,
    WinState,
)

POTION = Item("potion", "!")
GOLD = Item("gold", "$")

ROOM = level_from(
    "#####",
    "#...#",
    "#...#",
    "#...#",
    "#####",
)


def test_playing_draws_a_header_the_panels_with_a_legend_and_the_log():
    game = Game.new(seed=42)
    game.say("You pick up the potion.")
    game.say("A wall is in the way.")
    game.say("A wall is in the way.")

    lines = PlayingState(game).draw()

    view, mini_map = draw_view(game), draw_mini_map(game)
    menu = "i inventory  l log  c clear  ? help  q quit"
    assert lines[0] == "DUNGEON EXPLORER" + " " * 9 + menu
    assert lines[1] == f"Level 1 of {floor_count(42)}   Seed 42"
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
    # Three lines for the log, with a blank above the two messages so far.
    assert lines[20:] == ["", "You pick up the potion.", "A wall is in the way. (x2)"]
    assert len(lines) == 23
    assert max(len(line) for line in lines) <= 80


def test_playing_shows_only_the_newest_three_messages():
    game = game_on(ROOM, position=(2, 2))
    for number in range(5):
        game.say(f"Message {number}.")

    lines = PlayingState(game).draw()

    assert lines[-3:] == ["Message 2.", "Message 3.", "Message 4."]


def test_playing_clears_the_log_on_c_without_taking_a_turn():
    game = game_on(ROOM, position=(2, 2))
    game.say("A wall is in the way.")
    playing = PlayingState(game)

    assert playing.handle("c") is playing
    assert game.log == []
    assert game.player.position == (2, 2)


def test_playing_opens_the_log_on_l():
    game = game_on(ROOM, position=(2, 2))

    log = PlayingState(game).handle("l")

    assert isinstance(log, LogState)
    assert log.game is game


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
    assert str(game.log[-1]) == "There are no stairs down here."


def test_playing_says_when_it_doesnt_know_a_command():
    game = game_on(ROOM, position=(2, 2))
    playing = PlayingState(game)

    assert playing.handle(" jump ") is playing
    assert str(game.log[-1]) == "Unknown command 'jump'. Press ? for help."
    assert game.player.position == (2, 2)


def test_playing_ignores_an_empty_line():
    game = game_on(ROOM, position=(2, 2))
    game.say("You pick up the potion.")
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
    for key in ("w a s d", ">", "i", "l", "c", "?", "q"):
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


def _logged(count: int) -> LogState:
    """A log screen for a game that has said `count` numbered messages."""
    game = game_on(ROOM, position=(2, 2))
    for number in range(1, count + 1):
        game.say(f"Message {number}.")
    return LogState(game)


def test_the_log_screen_shows_every_message_when_they_fit():
    assert _logged(2).draw() == [
        "Message log   1-2 of 2",
        "",
        "  Message 1.",
        "  Message 2.",
        "",
        "w older   s newer   any other key to go back",
    ]


def test_the_log_screen_opens_on_the_newest_page():
    lines = _logged(25).draw()

    assert lines[0] == "Message log   6-25 of 25"
    assert lines[2] == "  Message 6."
    assert lines[21] == "  Message 25."


def test_the_log_screen_scrolls_older_with_w_and_newer_with_s():
    log = _logged(25)

    assert log.handle("w") is log
    assert log.handle("w") is log
    assert log.draw()[0] == "Message log   4-23 of 25"
    assert log.handle("s") is log
    assert log.draw()[0] == "Message log   5-24 of 25"


def test_the_log_screen_stops_scrolling_at_either_end():
    log = _logged(25)

    for _ in range(10):
        log.handle("w")
    assert log.draw()[0] == "Message log   1-20 of 25"
    for _ in range(10):
        log.handle("s")
    assert log.draw()[0] == "Message log   6-25 of 25"


def test_a_short_log_doesnt_scroll():
    log = _logged(2)

    log.handle("w")

    assert log.draw()[0] == "Message log   1-2 of 2"


def test_the_log_screen_says_when_there_are_no_messages():
    assert _logged(0).draw() == [
        "Message log",
        "",
        "  No messages yet.",
        "",
        "Press any key to go back.",
    ]


@pytest.mark.parametrize("text", ["", "q", "d", "l"])
def test_any_other_key_on_the_log_screen_goes_back_to_playing(text):
    log = _logged(3)
    before = copy.deepcopy(log.game)

    back = log.handle(text)

    assert isinstance(back, PlayingState)
    assert back.game is log.game
    assert log.game == before


def _on_the_last_stairs(seed: int) -> Game:
    """A new game for `seed`, taken down to its last floor and onto the stairs."""
    game = Game.new(seed)
    while game.depth < game.floors:
        game.player.position = game.level.stairs_down
        game.descend()
    game.player.position = game.level.stairs_down
    return game


def test_going_down_the_last_stairs_shows_the_win_screen():
    # Seed 1's dungeon has three floors.
    game = _on_the_last_stairs(seed=1)

    won = PlayingState(game).handle(">")

    assert isinstance(won, WinState)
    assert won.game is game


def test_stairs_before_the_last_floor_stay_on_the_playing_screen():
    game = Game.new(seed=1)
    game.player.position = game.level.stairs_down
    playing = PlayingState(game)

    assert playing.handle(">") is playing
    assert game.depth == 2


def test_the_win_screen_says_how_deep_and_what_was_carried_out():
    game = _on_the_last_stairs(seed=1)
    game.player.inventory = [POTION, GOLD]

    assert WinState(game).draw() == [
        "You escaped the dungeon!",
        "",
        "You made it through all 3 floors of seed 1, carrying:",
        "  ! potion",
        "  $ gold",
        "",
        "Press any key to finish.",
    ]


def test_the_win_screen_says_when_nothing_was_carried_out():
    game = _on_the_last_stairs(seed=1)

    assert WinState(game).draw()[3] == "  nothing at all."


@pytest.mark.parametrize("text", ["", "q", "w"])
def test_any_key_on_the_win_screen_ends_the_game(text):
    assert WinState(_on_the_last_stairs(seed=1)).handle(text) is None


def test_the_win_screen_says_goodbye_with_the_floors_escaped():
    game = _on_the_last_stairs(seed=1)

    assert WinState(game).goodbye() == "Goodbye! You escaped all 3 floors of seed 1."
