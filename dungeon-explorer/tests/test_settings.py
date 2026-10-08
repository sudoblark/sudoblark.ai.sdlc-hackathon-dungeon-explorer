from pathlib import Path

import pytest

from dungeon_explorer.game import Game
from dungeon_explorer.level import Item, Monster
from dungeon_explorer.settings import DEFAULT_SETTINGS, Settings, load_settings


def test_the_defaults_are_the_game_as_it_has_always_been():
    assert DEFAULT_SETTINGS == Settings(
        min_floors=3,
        max_floors=7,
        level_width=64,
        level_height=32,
        max_rooms=9,
        room_widths=(4, 12),
        room_heights=(3, 7),
        items_per_level=(3, 6),
        monsters_per_floor=(1, 3),
        items=(
            (Item("potion", "!", healing=5), 1),
            (Item("gold", "$"), 1),
            (Item("scroll", "?"), 1),
            (Item("dagger", ")", damage=2), 1),
            (Item("sword", "/", damage=3), 2),
            (Item("axe", "\\", damage=4), 4),
        ),
        monsters=(
            (Monster("rat", "r", hit_points=2, damage=1), 1),
            (Monster("goblin", "g", hit_points=4, damage=2), 2),
            (Monster("orc", "o", hit_points=7, damage=3), 4),
        ),
        view_width=31,
        view_height=15,
        log_lines=3,
    )


def test_a_game_keeps_its_settings_all_the_way_down():
    settings = Settings(min_floors=3, max_floors=3, level_width=40, level_height=20)
    game = Game.new(seed=1, settings=settings)

    game.player.position = game.level.stairs_down
    game.descend()

    assert game.settings is settings
    assert game.floors == 3
    assert (game.level.width, game.level.height) == (40, 20)


def test_a_game_without_settings_uses_the_defaults():
    assert Game.new(seed=42).settings is DEFAULT_SETTINGS


SHIPPED = Path(__file__).parent.parent / "settings.toml"


def _load(tmp_path: Path, text: str) -> tuple[Settings, list[str]]:
    path = tmp_path / "settings.toml"
    path.write_text(text)
    return load_settings(path)


def test_the_shipped_settings_file_is_exactly_the_defaults():
    assert load_settings(SHIPPED) == (DEFAULT_SETTINGS, [])


def test_without_a_settings_file_the_game_uses_the_defaults(tmp_path):
    assert load_settings(tmp_path / "settings.toml") == (DEFAULT_SETTINGS, [])


def test_a_settings_file_the_player_named_must_exist(tmp_path):
    settings, warnings = load_settings(tmp_path / "mine.toml", required=True)

    assert settings == DEFAULT_SETTINGS
    assert warnings == [f"{tmp_path / 'mine.toml'} doesn't exist"]


def test_a_file_that_isnt_toml_falls_back_to_the_defaults(tmp_path):
    settings, warnings = _load(tmp_path, "[dungeon\nmin_floors = ")

    assert settings == DEFAULT_SETTINGS
    assert len(warnings) == 1
    assert "can't be read" in warnings[0]


def test_a_file_only_changes_what_it_sets(tmp_path):
    settings, warnings = _load(tmp_path, "[dungeon]\nmax_floors = 5\n")

    assert warnings == []
    assert settings.max_floors == 5
    assert settings == Settings(max_floors=5)


def test_items_and_monsters_in_the_file_replace_the_defaults(tmp_path):
    text = """
[[items]]
name = "gem"
glyph = "*"
first_floor = 2

[[monsters]]
name = "bat"
glyph = "b"
hit_points = 1
damage = 1
"""
    settings, warnings = _load(tmp_path, text)

    assert warnings == []
    assert settings.items == ((Item("gem", "*"), 2),)
    assert settings.monsters == ((Monster("bat", "b", hit_points=1, damage=1), 1),)


def test_unknown_tables_and_keys_are_ignored_with_a_warning(tmp_path):
    text = "[sounds]\nvolume = 11\n\n[level]\nwidht = 50\nheight = 20\n"

    settings, warnings = _load(tmp_path, text)

    assert settings == Settings(level_height=20)
    assert sorted(warnings) == [
        "'sounds' isn't a table this game has, so it's ignored",
        "[level] has no key 'widht', so it's ignored",
    ]


@pytest.mark.parametrize(
    "line",
    [
        'log_lines = "three"',  # not a number
        "log_lines = true",  # TOML's true isn't the number 1
        "log_lines = 1.5",  # not whole
        "log_lines = 0",  # too few
    ],
)
def test_a_bad_number_keeps_its_default(tmp_path, line):
    settings, warnings = _load(tmp_path, f"[screen]\n{line}\nview_width = 21\n")

    assert settings == Settings(view_width=21)
    assert len(warnings) == 1
    assert warnings[0].startswith("[screen] log_lines: ")
    assert warnings[0].endswith(", so it uses the default")


@pytest.mark.parametrize(
    ("value", "problem"),
    [
        ("[5]", "Field required"),
        ("[8, 4]", "should go from fewest to most"),
        ("[2, 6]", "should start at 3 or more"),
    ],
)
def test_a_bad_range_keeps_its_default(tmp_path, value, problem):
    settings, warnings = _load(tmp_path, f"[level]\nroom_widths = {value}\n")

    assert settings == DEFAULT_SETTINGS
    assert problem in warnings[0]


def test_more_min_floors_than_max_resets_the_dungeon_table(tmp_path):
    settings, warnings = _load(tmp_path, "[dungeon]\nmin_floors = 8\n")

    assert (settings.min_floors, settings.max_floors) == (3, 7)
    assert warnings == [
        "[dungeon] min_floors (8) is more than max_floors (7),"
        " so the whole table uses the defaults"
    ]


def test_a_level_too_small_for_its_rooms_resets_the_level_table(tmp_path):
    settings, warnings = _load(tmp_path, "[level]\nwidth = 10\n")

    assert settings.level_width == 64
    assert warnings == [
        "[level] a 10x32 level can't fit rooms up to 12x7,"
        " so the whole table uses the defaults"
    ]


def test_a_kind_with_a_mistake_is_skipped_and_the_rest_kept(tmp_path):
    text = """
[[monsters]]
name = "bat"
glyph = "b"
hit_points = 1
damage = 1

[[monsters]]
name = "slime"
glyph = "ss"
hit_points = 2
damage = 1

[[monsters]]
name = "ghost"
glyph = "h"
damage = 2
"""
    settings, warnings = _load(tmp_path, text)

    assert [monster.name for monster, _ in settings.monsters] == ["bat"]
    assert warnings[0].startswith("[[monsters]] number 2 (slime) glyph: ")
    assert warnings[1].startswith("[[monsters]] number 2 (ghost) hit_points: ")
    assert all(warning.endswith(", so it's skipped") for warning in warnings)


def test_when_no_kinds_can_be_used_the_defaults_stay(tmp_path):
    settings, warnings = _load(tmp_path, '[[items]]\nname = "gem"\n')

    assert settings.items == DEFAULT_SETTINGS.items
    assert warnings[0].endswith("and with none left, the items use the defaults")


def test_a_glyph_the_screen_or_another_kind_uses_is_skipped(tmp_path):
    text = """
[[monsters]]
name = "wall-crawler"
glyph = "#"
hit_points = 1
damage = 1

[[monsters]]
name = "ghost"
glyph = "!"
hit_points = 3
damage = 2

[[monsters]]
name = "bat"
glyph = "b"
hit_points = 1
damage = 1
"""
    settings, warnings = _load(tmp_path, text)

    assert [monster.name for monster, _ in settings.monsters] == ["bat"]
    assert warnings == [
        "the wall-crawler can't use '#', which is taken, so it's skipped",
        "the ghost can't use '!', which is taken, so it's skipped",
    ]


def test_the_same_settings_always_give_the_same_fingerprint():
    assert Settings().fingerprint == DEFAULT_SETTINGS.fingerprint
    # Pinned, so a change to the defaults can't go unnoticed by replays.
    assert DEFAULT_SETTINGS.fingerprint == "546d8c"


@pytest.mark.parametrize(
    "changed",
    [
        Settings(min_floors=2),
        Settings(level_width=60),
        Settings(room_widths=(4, 11)),
        Settings(view_height=13),
        Settings(log_lines=4),
        Settings(items=DEFAULT_SETTINGS.items[:-1]),
        Settings(
            monsters=(
                (Monster("rat", "r", hit_points=3, damage=1), 1),
                *DEFAULT_SETTINGS.monsters[1:],
            )
        ),
    ],
)
def test_any_change_to_the_settings_changes_the_fingerprint(changed):
    assert changed.fingerprint != DEFAULT_SETTINGS.fingerprint


def test_a_fingerprint_is_six_hex_characters():
    fingerprint = Settings(max_floors=9).fingerprint

    assert len(fingerprint) == 6
    assert set(fingerprint) <= set("0123456789abcdef")


def test_a_settings_file_matching_the_defaults_has_the_default_fingerprint():
    settings, _ = load_settings(SHIPPED)

    assert settings.fingerprint == DEFAULT_SETTINGS.fingerprint
