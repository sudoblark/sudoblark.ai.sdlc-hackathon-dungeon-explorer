from dungeon_explorer.game import Game
from dungeon_explorer.level import Item, Monster
from dungeon_explorer.settings import DEFAULT_SETTINGS, Settings


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
