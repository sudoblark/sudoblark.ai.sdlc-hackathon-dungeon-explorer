import copy

import pytest
from helpers import game_on, level_from

from dungeon_explorer.game import Game
from dungeon_explorer.generate import floor_count
from dungeon_explorer.level import Item, Monster, Tile
from dungeon_explorer.render import PLAYER, STAIRS_DOWN, draw_mini_map, draw_view
from dungeon_explorer.settings import DEFAULT_SETTINGS, Settings
from dungeon_explorer.states import (
    GameOverState,
    HelpState,
    InventoryState,
    LeaveState,
    LogState,
    PlayingState,
    SeedState,
    TitleState,
    WinState,
    legend,
)

# The fingerprint of the default settings, which every game here uses.
FP = DEFAULT_SETTINGS.fingerprint
POTION = Item("potion", "!")
GOLD = Item("gold", "$")

ROOM = level_from(
    "#####",
    "#...#",
    "#...#",
    "#...#",
    "#####",
)


def test_the_playing_screen_is_framed_in_labelled_panels():
    game = Game.new(seed=42)
    game.say("You pick up the potion.")
    game.say("A wall is in the way.")
    game.say("A wall is in the way.")

    lines = PlayingState(game).draw()

    view, mini_map = draw_view(game), draw_mini_map(game)
    key = [" @ you", " # wall", " . floor", " > stairs", " ! potion", " $ gold"]
    key += [" ? scroll", " ) dagger", " / sword", " \\ axe", " r rat", " g goblin"]
    key += [" o orc"]
    # The title has a banner of its own, apart from the game.
    assert lines[:3] == [
        "+" + "=" * 75 + "+",
        "|" + "D U N G E O N   E X P L O R E R".center(75) + "|",
        "+" + "=" * 75 + "+",
    ]
    status = f"Level 1 of {floor_count(42)}   Seed 42 (settings {FP})"
    assert lines[3] == "| " + status + "HP 20/20".rjust(73 - len(status)) + " |"
    assert lines[4] == "+-- View " + "-" * 23 + "+-- Map " + "-" * 25 + "+-- Key ---+"
    # The view is 15 lines, so it gets a blank line to match the mini-map.
    for row in range(16):
        left = view[row] if row < len(view) else " " * 31
        right = key[row] if row < len(key) else ""
        assert lines[5 + row] == f"|{left}|{mini_map[row]}|{right.ljust(10)}|"
    assert lines[21] == "+-- Messages " + "-" * 63 + "+"
    assert lines[22:25] == [
        "|" + " " * 75 + "|",
        "| " + "You pick up the potion.".ljust(73) + " |",
        "| " + "A wall is in the way. (x2)".ljust(73) + " |",
    ]
    menu = "i items  p drink  l log  c clear  ? help  q leave"
    assert lines[25:] == [
        "+" + "-" * 75 + "+",
        "| " + menu.center(73) + " |",
        "+" + "-" * 75 + "+",
    ]
    assert {len(line) for line in lines} == {77}


def test_the_legend_explains_every_symbol_the_playing_screen_can_show():
    glyphs = {glyph for glyph, _ in legend(DEFAULT_SETTINGS)}

    assert {PLAYER, STAIRS_DOWN, Tile.WALL, Tile.FLOOR} <= glyphs
    assert {item.glyph for item, _ in DEFAULT_SETTINGS.items} <= glyphs
    assert {monster.glyph for monster, _ in DEFAULT_SETTINGS.monsters} <= glyphs


@pytest.mark.parametrize(
    ("text", "state"),
    [("i", InventoryState), ("I", InventoryState), ("?", HelpState)],
)
def test_playing_opens_the_inventory_and_help_screens(text, state):
    game = game_on(ROOM, position=(2, 2))

    assert isinstance(PlayingState(game).handle(text), state)


def test_q_asks_before_leaving_the_game():
    game = game_on(ROOM, position=(2, 2))

    leave = PlayingState(game).handle("q")

    assert isinstance(leave, LeaveState)
    assert leave.game is game


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


def _parts(lines: list[str]) -> tuple[str, list[str], str, list[str]]:
    """A framed screen's label, the lines in its panel, the text of its keys
    bar, and any lines below its edge, checking the edge lines up all round."""
    bottom = max(i for i, line in enumerate(lines) if line and set(line) <= {"+", "-"})
    framed, after = lines[: bottom + 1], lines[bottom + 1 :]
    assert len({len(line) for line in framed}) == 1
    assert framed[1].strip("| ") == "D U N G E O N   E X P L O R E R"
    label = framed[3].removeprefix("+-- ").rstrip("-+").rstrip()
    body = [line[2:-2].rstrip() for line in framed[5:-4]]
    # In-game screens are padded to the playing screen's height.
    while body and not body[-1]:
        body.pop()
    keys = framed[-2][2:-2].strip()
    return label, body, keys, after


def test_the_inventory_lists_what_the_player_carries_in_order():
    game = game_on(ROOM, position=(2, 2))
    game.player.inventory = [POTION, GOLD]

    assert _parts(InventoryState(game).draw()) == (
        "Items",
        ["  ! potion", "  $ gold"],
        "Press any key to go back.",
        [],
    )


def test_the_inventory_says_when_it_is_empty():
    game = game_on(ROOM, position=(2, 2))

    _, body, _, _ = _parts(InventoryState(game).draw())

    assert body == ["  You aren't carrying anything yet."]


def test_the_help_lists_every_key():
    label, body, keys, _ = _parts(HelpState(game_on(ROOM, position=(2, 2))).draw())

    assert label == "How to play"
    assert keys == "Press any key to go back."
    for key in ("w a s d", ">", "i", "p", "l", "c", "?", "q"):
        assert any(line.startswith(f"  {key} ") for line in body), key


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

    assert (
        screen(game).goodbye()
        == f"Goodbye! You reached level 1 of seed 42 (settings {FP})."
    )


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
    assert _parts(_logged(2).draw()) == (
        "Message log   1-2 of 2",
        ["  Message 1.", "  Message 2."],
        "w older   s newer   any other key to go back",
        [],
    )


def test_the_log_screen_opens_on_the_newest_page():
    label, body, _, _ = _parts(_logged(25).draw())

    assert label == "Message log   6-25 of 25"
    assert body[0] == "  Message 6."
    assert body[-1] == "  Message 25."


def test_the_log_screen_scrolls_older_with_w_and_newer_with_s():
    log = _logged(25)

    assert log.handle("w") is log
    assert log.handle("w") is log
    assert _parts(log.draw())[0] == "Message log   4-23 of 25"
    assert log.handle("s") is log
    assert _parts(log.draw())[0] == "Message log   5-24 of 25"


def test_the_log_screen_stops_scrolling_at_either_end():
    log = _logged(25)

    for _ in range(10):
        log.handle("w")
    assert _parts(log.draw())[0] == "Message log   1-20 of 25"
    for _ in range(10):
        log.handle("s")
    assert _parts(log.draw())[0] == "Message log   6-25 of 25"


def test_a_short_log_doesnt_scroll():
    log = _logged(2)

    log.handle("w")

    assert _parts(log.draw())[0] == "Message log   1-2 of 2"


def test_the_log_screen_says_when_there_are_no_messages():
    assert _parts(_logged(0).draw()) == (
        "Message log",
        ["  No messages yet."],
        "Press any key to go back.",
        [],
    )


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

    assert _parts(WinState(game).draw()) == (
        "You escaped the dungeon!",
        [
            "You made it through all 3 floors of seed 1, carrying:",
            "  ! potion",
            "  $ gold",
        ],
        "Press any key to go back to the title.",
        [],
    )


def test_the_win_screen_says_when_nothing_was_carried_out():
    game = _on_the_last_stairs(seed=1)

    assert _parts(WinState(game).draw())[1][1] == "  nothing at all."


@pytest.mark.parametrize("text", ["", "q", "w"])
def test_any_key_on_the_win_screen_ends_the_game(text):
    assert WinState(_on_the_last_stairs(seed=1)).handle(text) is None


def test_the_win_screen_says_goodbye_with_the_floors_escaped():
    game = _on_the_last_stairs(seed=1)

    assert (
        WinState(game).goodbye()
        == f"Goodbye! You escaped all 3 floors of seed 1 (settings {FP})."
    )


def _title(seed: int | None = None) -> TitleState:
    """A title screen whose random seeds are always 99."""
    return TitleState(seed, random_seed=lambda: 99)


def test_the_title_screen_highlights_new_game_first():
    assert _title().draw() == [
        "+------------------------------+",
        "|       DUNGEON EXPLORER       |",
        "+------------------------------+",
        "",
        "  > New game <",
        "    Exit",
        "",
        "w/s to choose, Enter to pick",
    ]


def test_w_and_s_move_the_highlight_and_stop_at_either_end():
    title = _title()

    assert title.handle("s") is title
    assert title.draw()[4:6] == ["    New game", "  > Exit <"]
    title.handle("s")
    assert title.choice == 1
    title.handle("w")
    title.handle("w")
    assert title.choice == 0


@pytest.mark.parametrize("enter", ["", "\n", "\r"])
def test_enter_on_new_game_opens_the_seed_screen(enter):
    title = _title(seed=42)

    seed = title.handle(enter)

    assert isinstance(seed, SeedState)
    assert seed.digits == "42"
    assert seed.title is title


def test_the_seed_screen_starts_blank_without_a_seed_from_the_command_line():
    assert _title().handle("").digits == ""


def test_enter_on_exit_ends_the_game():
    title = _title()
    title.handle("s")

    assert title.handle("") is None
    assert title.goodbye() == "Goodbye!"


def test_other_keys_on_the_title_screen_do_nothing():
    title = _title()

    assert title.handle("x") is title
    assert title.choice == 0


def test_the_seed_screen_shows_what_has_been_typed():
    seed = SeedState(_title(), digits="42")

    assert _parts(seed.draw()) == (
        "New game",
        [
            "Type a seed and press Enter, or leave it blank for a random one.",
            "",
            "  Seed: 42_",
        ],
        "Enter to start   q to go back",
        [],
    )


def test_typing_digits_adds_them_and_backspace_takes_them_away():
    seed = SeedState(_title())

    for key in ("1", "2", "3", "\x7f", "4", "\b"):
        assert seed.handle(key) is seed

    assert seed.digits == "12"


def test_a_typed_line_of_digits_adds_them_all():
    seed = SeedState(_title(), digits="1")

    seed.handle("234")

    assert seed.digits == "1234"


def test_seeds_stop_at_nine_digits():
    seed = SeedState(_title())

    seed.handle("1234567890")

    assert seed.digits == "123456789"


def test_enter_starts_a_game_with_the_typed_seed():
    title = _title()

    playing = SeedState(title, digits="7").handle("")

    assert isinstance(playing, PlayingState)
    assert playing.game.seed == 7
    assert playing.game.depth == 1
    assert playing.title is title


def test_enter_on_a_blank_seed_starts_a_game_with_a_random_one():
    playing = SeedState(_title(), digits="").handle("")

    assert playing.game.seed == 99


def test_q_on_the_seed_screen_goes_back_to_the_title():
    title = _title()

    assert SeedState(title, digits="7").handle("q") is title


def test_other_keys_on_the_seed_screen_do_nothing():
    seed = SeedState(_title(), digits="7")

    assert seed.handle("x") is seed
    assert seed.digits == "7"


def test_leaving_asks_for_confirmation():
    game = Game.new(seed=42)

    assert _parts(LeaveState(game).draw()) == (
        "Leave this game?",
        ["Your progress on seed 42 will be lost."],
        "y to leave   any other key to keep playing",
        [],
    )


def test_y_leaves_the_game_for_the_title_screen():
    title = _title()
    game = game_on(ROOM, position=(2, 2))

    assert LeaveState(game, title).handle("y") is title


def test_y_without_a_title_screen_ends_everything():
    assert LeaveState(game_on(ROOM, position=(2, 2))).handle("y") is None


@pytest.mark.parametrize("text", ["", "n", "q", "w"])
def test_any_other_key_keeps_playing(text):
    title = _title()
    game = game_on(ROOM, position=(2, 2))

    back = LeaveState(game, title).handle(text)

    assert isinstance(back, PlayingState)
    assert back.game is game
    assert back.title is title


def test_the_screens_of_a_game_keep_hold_of_the_title_screen():
    title = _title()
    playing = PlayingState(game_on(ROOM, position=(2, 2)), title)

    for key in ("i", "?", "l", "q"):
        screen = playing.handle(key)
        assert screen.title is title
        assert screen.handle("x").title is title


def test_the_win_screen_goes_back_to_the_title_screen():
    title = _title()

    assert WinState(_on_the_last_stairs(seed=1), title).handle("x") is title


DAGGER = Item("dagger", ")", damage=2)
SWORD = Item("sword", "/", damage=3)


def test_the_inventory_marks_the_weapon_in_hand():
    game = game_on(ROOM, position=(2, 2))
    game.player.inventory = [DAGGER, POTION, SWORD, SWORD]

    assert _parts(InventoryState(game).draw())[1] == [
        "  ) dagger",
        "  ! potion",
        "  / sword   (in hand)",
        "  / sword",
    ]


def test_the_status_line_shows_the_players_hit_points():
    game = game_on(ROOM, position=(2, 2))
    game.player.hit_points = 7

    assert PlayingState(game).draw()[3].endswith("   HP 7/20 |")


def _about_to_die() -> Game:
    """Seed 1's first floor, with a goblin next to the player on one hit point."""
    game = Game.new(seed=1)
    x, y = game.player.position
    goblin = Monster("goblin", "g", hit_points=4, damage=2, position=(x + 1, y))
    game.level.monsters = [goblin]
    game.player.hit_points = 1
    return game


def test_losing_the_last_hit_point_shows_the_game_over_screen():
    title = _title()
    game = _about_to_die()

    # Punching the goblin is a turn, and it hits back.
    over = PlayingState(game, title).handle("d")

    assert isinstance(over, GameOverState)
    assert over.game is game
    assert over.title is title


def test_the_game_over_screen_says_what_killed_the_player_and_where():
    game = _about_to_die()
    PlayingState(game).handle("d")

    assert _parts(GameOverState(game).draw()) == (
        "You died",
        [
            "The goblin killed you on level 1 of 3 of seed 1.",
            "You were carrying:",
            "  nothing at all.",
        ],
        "Press any key to go back to the title.",
        [],
    )


def test_the_game_over_screen_lists_what_the_player_was_carrying():
    game = _about_to_die()
    game.player.inventory = [POTION, GOLD]
    PlayingState(game).handle("d")

    assert _parts(GameOverState(game).draw())[1][1:] == [
        "You were carrying:",
        "  ! potion",
        "  $ gold",
    ]


def test_any_key_on_the_game_over_screen_goes_back_to_the_title():
    title = _title()
    game = _about_to_die()

    assert GameOverState(game, title).handle("x") is title
    assert GameOverState(game).handle("x") is None


def test_the_game_over_screen_says_goodbye_with_the_level_and_seed():
    game = _about_to_die()

    assert (
        GameOverState(game).goodbye()
        == f"Goodbye! You died on level 1 of seed 1 (settings {FP})."
    )


def test_the_playing_screen_takes_its_sizes_and_legend_from_the_settings():
    gem = Item("gem", "*")
    settings = Settings(view_width=11, view_height=5, log_lines=1, items=((gem, 1),))
    game = Game.new(seed=42, settings=settings)
    game.say("First.")
    game.say("Second.")

    lines = PlayingState(game).draw()

    assert lines[4].startswith("+-- View ---+-- Map ")  # 11 wide
    assert "| * gem" in "\n".join(lines)
    assert "potion" not in "\n".join(lines)
    # One log line, between the Messages edge and the menu bar.
    assert lines[-5].startswith("+-- Messages ")
    assert lines[-4].strip("| ").rstrip() == "Second."
    assert "First." not in "\n".join(lines)


def test_a_new_game_from_the_seed_screen_uses_the_title_screens_settings():
    settings = Settings(min_floors=2, max_floors=2)
    title = TitleState(None, random_seed=lambda: 5, settings=settings)

    playing = SeedState(title, digits="7").handle("")

    assert playing.game.settings is settings
    assert playing.game.floors == 2


def test_the_title_screen_lists_problems_with_the_settings_file():
    long = (
        "[dungeon] min_floors (8) is more than max_floors (7), so the whole"
        " table uses the defaults"
    )
    title = TitleState(None, lambda: 1, warnings=("[level] has no key 'w'", long))

    assert title.draw()[8:] == [
        "",
        "Problems with the settings file:",
        "  [level] has no key 'w'",
        "  [dungeon] min_floors (8) is more than max_floors (7), so the whole table",
        "    uses the defaults",
    ]


def test_the_title_screen_has_no_problems_section_without_warnings():
    assert "Problems with the settings file:" not in _title().draw()


def test_a_narrow_view_still_fits_the_status_and_menu_inside_the_edge():
    game = Game.new(seed=42, settings=Settings(view_width=5))

    lines = PlayingState(game).draw()

    # The Key panel takes the width the narrow view lacks, so the edge meets.
    assert len({len(line) for line in lines}) == 1
    assert lines[3].startswith(f"| Level 1 of {floor_count(42)}   Seed 42 (settings ")
    assert lines[3].endswith("HP 20/20 |")
    assert "i items  p drink  l log  c clear  ? help  q leave" in lines[-2]


def _with_settings(game: Game, settings: Settings) -> Game:
    game.settings = settings
    return game


def test_the_end_screens_show_how_to_replay_settings_that_arent_the_defaults():
    settings = Settings(min_floors=3, max_floors=3)
    won = WinState(_with_settings(_on_the_last_stairs(seed=1), settings))
    lost = GameOverState(_with_settings(_about_to_die(), settings))

    for screen in (won, lost):
        # Below the edge, so the code is never cut short or mixed with it.
        assert _parts(screen.draw())[3] == [
            "Replay these settings with:",
            f"--settings-code {settings.code}",
        ]


def test_the_end_screens_have_no_replay_code_with_the_default_settings():
    lines = WinState(_on_the_last_stairs(seed=1)).draw()

    assert "Replay these settings with:" not in lines


def test_goodbyes_add_the_replay_code_for_settings_that_arent_the_defaults():
    settings = Settings(min_floors=3, max_floors=3)
    game = _with_settings(Game.new(seed=42), settings)

    assert PlayingState(game).goodbye().splitlines() == [
        f"Goodbye! You reached level 1 of seed 42 (settings {settings.fingerprint}).",
        "Replay these settings with:",
        f"--settings-code {settings.code}",
    ]


@pytest.mark.parametrize(
    "screen", [InventoryState, HelpState, LogState, LeaveState, WinState, GameOverState]
)
def test_every_screen_of_a_game_is_the_same_size_as_the_playing_screen(screen):
    game = _about_to_die()

    playing, lines = PlayingState(game).draw(), screen(game).draw()

    assert {len(line) for line in lines} == {len(playing[0])}
    assert len(lines) == len(playing)


def test_the_title_screen_keeps_its_own_look():
    assert _title().draw()[:3] == [
        "+------------------------------+",
        "|       DUNGEON EXPLORER       |",
        "+------------------------------+",
    ]
