"""Everything about the game a settings file can change, its defaults, and
reading it from a TOML file."""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    ValidationError,
    model_validator,
)

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


# The file is checked with Pydantic models that mirror its tables. Each one
# takes its defaults from DEFAULT_SETTINGS, so the defaults live in one place.
_DEFAULTS = DEFAULT_SETTINGS
# Glyphs the screen already uses for walls, floor, the player, the stairs and
# unseen tiles, so no item or monster can have them.
RESERVED_GLYPHS = {"#", ".", "@", ">", " "}


def _range(smallest: int) -> Any:
    """A [fewest, most] pair whose fewest is at least `smallest`."""

    def check(pair: tuple[int, int]) -> tuple[int, int]:
        fewest, most = pair
        if fewest < smallest:
            raise ValueError(f"should start at {smallest} or more")
        if fewest > most:
            raise ValueError("should go from fewest to most")
        return pair

    return Annotated[tuple[StrictInt, StrictInt], AfterValidator(check)]


class _Table(BaseModel):
    # A misspelt key is an error, rather than quietly doing nothing.
    model_config = ConfigDict(extra="forbid")


class _Dungeon(_Table):
    min_floors: StrictInt = Field(_DEFAULTS.min_floors, ge=1)
    max_floors: StrictInt = Field(_DEFAULTS.max_floors, ge=1)

    @model_validator(mode="after")
    def _fewest_first(self) -> Self:
        if self.min_floors > self.max_floors:
            raise ValueError(
                f"min_floors ({self.min_floors}) is more than"
                f" max_floors ({self.max_floors})"
            )
        return self


class _Level(_Table):
    width: StrictInt = Field(_DEFAULTS.level_width, ge=5)
    height: StrictInt = Field(_DEFAULTS.level_height, ge=5)
    max_rooms: StrictInt = Field(_DEFAULTS.max_rooms, ge=1)
    room_widths: _range(3) = _DEFAULTS.room_widths
    room_heights: _range(3) = _DEFAULTS.room_heights
    items_per_level: _range(0) = _DEFAULTS.items_per_level
    monsters_per_floor: _range(0) = _DEFAULTS.monsters_per_floor

    @model_validator(mode="after")
    def _rooms_fit(self) -> Self:
        # A room needs a wall round it, and the level's edge is wall too.
        widest, tallest = self.room_widths[1], self.room_heights[1]
        if self.width < widest + 2 or self.height < tallest + 2:
            raise ValueError(
                f"a {self.width}x{self.height} level can't fit rooms up to"
                f" {widest}x{tallest}"
            )
        return self


class _Screen(_Table):
    view_width: StrictInt = Field(_DEFAULTS.view_width, ge=5)
    view_height: StrictInt = Field(_DEFAULTS.view_height, ge=5)
    log_lines: StrictInt = Field(_DEFAULTS.log_lines, ge=1)


class _Kind(_Table):
    name: StrictStr = Field(min_length=1)
    glyph: StrictStr = Field(min_length=1, max_length=1)
    first_floor: StrictInt = Field(1, ge=1)


class _ItemKind(_Kind):
    damage: StrictInt = Field(0, ge=0)
    healing: StrictInt = Field(0, ge=0)


class _MonsterKind(_Kind):
    hit_points: StrictInt = Field(ge=1)
    damage: StrictInt = Field(ge=0)


class _SettingsFile(_Table):
    dungeon: _Dungeon = _Dungeon()
    level: _Level = _Level()
    screen: _Screen = _Screen()
    # None keeps the default kinds. Giving any replaces the whole list.
    items: list[_ItemKind] | None = None
    monsters: list[_MonsterKind] | None = None


def load_settings(path: Path, required: bool = False) -> tuple[Settings, list[str]]:
    """The settings in the TOML file at `path`, and a warning for each mistake.

    Anything the file doesn't set, or sets wrongly, keeps its default, so the
    game always starts. A missing file just means the defaults, unless it's
    `required` because the player named it.
    """
    try:
        with path.open("rb") as file:
            data = tomllib.load(file)
    except FileNotFoundError:
        return DEFAULT_SETTINGS, [f"{path} doesn't exist"] if required else []
    except (OSError, tomllib.TOMLDecodeError) as error:
        return DEFAULT_SETTINGS, [f"{path} can't be read: {error}"]
    warnings: list[str] = []
    # Each pass drops the first value that's wrong, so it falls back to its
    # default, until what's left is valid.
    while True:
        try:
            parsed = _SettingsFile.model_validate(data)
            break
        except ValidationError as error:
            warnings.append(_drop(data, error.errors()[0]))
    return _to_settings(parsed, warnings), warnings


def _drop(data: dict[str, Any], problem: Any) -> str:
    """Remove what `problem` is about from `data`, and say what was wrong."""
    location, message = problem["loc"], problem["msg"].removeprefix("Value error, ")
    first = location[0]
    if first in ("items", "monsters") and len(location) > 1:
        # A mistake in one kind skips that kind. If none are left, the
        # default kinds stay.
        entries, number = data[first], location[1]
        entry = entries[number]
        name = entry.get("name") if isinstance(entry, dict) else None
        what = f"[[{first}]] number {number + 1}"
        if isinstance(name, str) and name:
            what += f" ({name})"
        if len(location) > 2:
            what += f" {location[2]}"
        del entries[number]
        if entries:
            return f"{what}: {message}, so it's skipped"
        del data[first]
        return (
            f"{what}: {message}, so it's skipped, and with none left,"
            f" the {first} use the defaults"
        )
    if len(location) == 1:
        del data[first]
        if problem["type"] == "extra_forbidden":
            return f"'{first}' isn't a table this game has, so it's ignored"
        return f"[{first}] {message}, so the whole table uses the defaults"
    key = location[1]
    del data[first][key]
    if problem["type"] == "extra_forbidden":
        return f"[{first}] has no key '{key}', so it's ignored"
    return f"[{first}] {key}: {message}, so it uses the default"


def _to_settings(parsed: _SettingsFile, warnings: list[str]) -> Settings:
    """The game's Settings from a checked file, dropping any item or monster
    whose glyph is already taken, so every symbol on screen means one thing."""
    dungeon, level, screen = parsed.dungeon, parsed.level, parsed.screen
    items = _DEFAULTS.items
    if parsed.items is not None:
        items = tuple(
            (Item(k.name, k.glyph, damage=k.damage, healing=k.healing), k.first_floor)
            for k in parsed.items
        )
    monsters = _DEFAULTS.monsters
    if parsed.monsters is not None:
        monsters = tuple(
            (Monster(k.name, k.glyph, k.hit_points, k.damage), k.first_floor)
            for k in parsed.monsters
        )
    taken = set(RESERVED_GLYPHS)
    kept: dict[str, list] = {"items": [], "monsters": []}
    for key, kinds in (("items", items), ("monsters", monsters)):
        for kind, first_floor in kinds:
            if kind.glyph in taken:
                warnings.append(
                    f"the {kind.name} can't use '{kind.glyph}', which is taken,"
                    " so it's skipped"
                )
                continue
            taken.add(kind.glyph)
            kept[key].append((kind, first_floor))
    return Settings(
        min_floors=dungeon.min_floors,
        max_floors=dungeon.max_floors,
        level_width=level.width,
        level_height=level.height,
        max_rooms=level.max_rooms,
        room_widths=level.room_widths,
        room_heights=level.room_heights,
        items_per_level=level.items_per_level,
        monsters_per_floor=level.monsters_per_floor,
        items=tuple(kept["items"]),
        monsters=tuple(kept["monsters"]),
        view_width=screen.view_width,
        view_height=screen.view_height,
        log_lines=screen.log_lines,
    )
