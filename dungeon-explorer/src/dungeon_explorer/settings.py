"""Everything about the game a settings file can change, and its defaults."""

from dataclasses import dataclass

from dungeon_explorer.level import Item, Monster

# A kind of item or monster, and the first floor it can turn up on.
ItemKind = tuple[Item, int]
MonsterKind = tuple[Monster, int]


@dataclass(frozen=True)
class Settings:
    """The game's settings. Each default is the game as it's always been.

    Ranges are (fewest, most). The monster kinds are templates: each monster
    placed on a level is a copy.
    """

    # Each seed's dungeon has between these many floors.
    min_floors: int = 3
    max_floors: int = 7
    level_width: int = 64
    level_height: int = 32
    max_rooms: int = 9
    room_widths: tuple[int, int] = (4, 12)
    room_heights: tuple[int, int] = (3, 7)
    items_per_level: tuple[int, int] = (3, 6)
    # On the first floor. Each floor deeper adds one to both.
    monsters_per_floor: tuple[int, int] = (1, 3)
    # Stronger weapons and tougher monsters only turn up deeper.
    items: tuple[ItemKind, ...] = (
        (Item("potion", "!", healing=5), 1),
        (Item("gold", "$"), 1),
        (Item("scroll", "?"), 1),
        (Item("dagger", ")", damage=2), 1),
        (Item("sword", "/", damage=3), 2),
        (Item("axe", "\\", damage=4), 4),
    )
    monsters: tuple[MonsterKind, ...] = (
        (Monster("rat", "r", hit_points=2, damage=1), 1),
        (Monster("goblin", "g", hit_points=4, damage=2), 2),
        (Monster("orc", "o", hit_points=7, damage=3), 4),
    )
    view_width: int = 31
    view_height: int = 15
    # How many of the newest messages show under the map.
    log_lines: int = 3


DEFAULT_SETTINGS = Settings()
