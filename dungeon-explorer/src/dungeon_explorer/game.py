"""The state of a game in play, and the rules for changing it."""

from dataclasses import dataclass, field
from typing import Self

from dungeon_explorer.generate import floor_count, generate_level
from dungeon_explorer.level import Direction, Item, Level, Monster, Point, Tile
from dungeon_explorer.settings import DEFAULT_SETTINGS, Settings

# What the player hits with when they carry no weapon.
FIST_DAMAGE = 1
# The most hit points the player can have, and how many they start with.
PLAYER_HIT_POINTS = 20


@dataclass
class Player:
    """The person exploring the dungeon.

    `inventory` holds what they've picked up, in the order they picked it up.
    """

    position: Point
    inventory: list[Item] = field(default_factory=list)
    hit_points: int = PLAYER_HIT_POINTS

    @property
    def weapon(self) -> Item | None:
        """The strongest weapon carried, which is the one the player fights with."""
        weapons = [item for item in self.inventory if item.damage > 0]
        return max(weapons, key=lambda item: item.damage, default=None)

    @property
    def damage(self) -> int:
        """How much each hit does: the weapon's damage, or a punch's."""
        return self.weapon.damage if self.weapon else FIST_DAMAGE


@dataclass
class Message:
    """Something that happened, and how many times in a row it happened."""

    text: str
    count: int = 1

    def __str__(self) -> str:
        return self.text if self.count == 1 else f"{self.text} (x{self.count})"


@dataclass
class Game:
    """Everything about a game in play.

    `explored` holds every tile of this level the player has seen, and `log`
    holds every message of the game, oldest first, for showing to the player.
    `finished` turns true when the player goes down the last floor's stairs,
    and `killed_by` names the monster that took their last hit point.
    """

    seed: int
    level: Level
    player: Player
    depth: int = 1
    explored: set[Point] = field(default_factory=set)
    log: list[Message] = field(default_factory=list)
    finished: bool = False
    killed_by: str | None = None
    settings: Settings = DEFAULT_SETTINGS

    def __post_init__(self) -> None:
        self._explore()

    @property
    def floors(self) -> int:
        """How many floors this game's dungeon has, set by its seed."""
        return floor_count(self.seed, self.settings)

    @classmethod
    def new(cls, seed: int, settings: Settings = DEFAULT_SETTINGS) -> Self:
        """Start a game at the top of the dungeon for `seed`."""
        level = generate_level(seed, 1, settings)
        player = Player(level.player_start)
        return cls(seed=seed, level=level, player=player, settings=settings)

    def move(self, direction: Direction) -> None:
        """Step the player one tile, or attack the monster standing there.

        Anything on the tile they step onto goes into their inventory. A step
        or an attack is a turn, so the monsters then take theirs. Bumping into
        a wall isn't, so a slip of the finger never lets them close in.
        """
        target = direction.step_from(self.player.position)
        if not self._is_floor(target):
            self.say("A wall is in the way.")
            return
        monster = self.level.monster_at(target)
        if monster is not None:
            self._attack(monster)
        else:
            self.player.position = target
            self._pick_up()
            self._explore()
        self._monsters_act()

    def descend(self) -> None:
        """Go down to the next level, if the player is standing on the stairs.

        The new level comes from the same seed, so it's the same whatever
        happened on the levels above. The player keeps their inventory. The
        last floor's stairs lead out of the dungeon, which finishes the game.
        """
        if self.player.position != self.level.stairs_down:
            self.say("There are no stairs down here.")
            return
        if self.depth == self.floors:
            self.finished = True
            self.say("You go down the last stairs and out of the dungeon.")
            return
        self.depth += 1
        self.level = generate_level(self.seed, self.depth, self.settings)
        self.player.position = self.level.player_start
        self.explored = set()
        self._explore()
        self.say(f"You go down the stairs to level {self.depth}.")
        if self.depth == self.floors:
            self.say("This is the last floor: its stairs lead out of the dungeon.")

    def monsters_in_sight(self) -> list[Monster]:
        """The monsters the player can see from where they stand."""
        position = self.player.position
        return [
            m for m in self.level.monsters if self.level.can_see(position, m.position)
        ]

    def drink(self) -> None:
        """Drink the first potion carried, healing up to the most hit points.

        Drinking is a turn, so the monsters then take theirs. With nothing to
        drink, or nothing to heal, it isn't.
        """
        player = self.player
        potion = next((item for item in player.inventory if item.healing), None)
        if potion is None:
            self.say("You have nothing to drink.")
            return
        if player.hit_points == PLAYER_HIT_POINTS:
            self.say("You're already at full health.")
            return
        player.inventory.remove(potion)
        healed = min(potion.healing, PLAYER_HIT_POINTS - player.hit_points)
        player.hit_points += healed
        self.say(f"You drink the {potion.name} and heal {healed} hit points.")
        self._monsters_act()

    def say(self, text: str) -> None:
        """Add `text` to the log, counting it again if it's the same as the last."""
        if self.log and self.log[-1].text == text:
            self.log[-1].count += 1
        else:
            self.log.append(Message(text))

    def clear_log(self) -> None:
        self.log.clear()

    def _attack(self, monster: Monster) -> None:
        """Hit `monster` with the player's weapon, or fists, removing it once
        its hit points run out."""
        weapon = self.player.weapon
        hit_with = weapon.name if weapon else "fists"
        monster.hit_points -= self.player.damage
        if monster.hit_points > 0:
            self.say(f"You hit the {monster.name} with your {hit_with}.")
            return
        self.level.monsters = [m for m in self.level.monsters if m is not monster]
        self.say(f"You kill the {monster.name} with your {hit_with}.")

    def _monsters_act(self) -> None:
        """Each monster that can see the player takes its turn: one next to the
        player attacks, and the rest step one tile closer. A monster that has
        only just arrived next to the player waits until its next turn."""
        for monster in self.level.monsters:
            if self.player.hit_points == 0:
                return
            if _next_to(monster.position, self.player.position):
                self._hit_player(monster)
            elif self.level.can_see(monster.position, self.player.position):
                self._step_towards_player(monster)

    def _hit_player(self, monster: Monster) -> None:
        """`monster` hits the player for its damage, never taking them below zero."""
        player = self.player
        player.hit_points = max(player.hit_points - monster.damage, 0)
        if player.hit_points == 0:
            self.killed_by = monster.name
            self.say(f"The {monster.name} kills you.")
        else:
            self.say(f"The {monster.name} hits you.")

    def _step_towards_player(self, monster: Monster) -> None:
        """Move `monster` one tile closer to the player, along the axis they're
        furthest apart on, or the other if that's blocked. It never steps into
        a wall, onto another monster, or onto the player.
        """
        (x, y), (player_x, player_y) = monster.position, self.player.position
        across, down = player_x - x, player_y - y
        steps = [(_sign(across), 0), (0, _sign(down))]
        if abs(down) > abs(across):
            steps.reverse()
        for step_x, step_y in steps:
            target = (x + step_x, y + step_y)
            if target == monster.position:
                continue
            if target == self.player.position:
                return
            if self._is_floor(target) and self.level.monster_at(target) is None:
                monster.position = target
                return

    def _pick_up(self) -> None:
        """Move any item under the player off the level and into their inventory."""
        item = self.level.items.pop(self.player.position, None)
        if item is None:
            return
        self.player.inventory.append(item)
        self.say(f"You pick up the {item.name}.")

    def _explore(self) -> None:
        """Reveal what the player can see from where they stand.

        That's the whole of the room they're in, walls and all, and the eight
        tiles around them, which maps corridors as they're walked.
        """
        position = self.player.position
        for room in self.level.rooms:
            if position in room.tiles():
                self.explored.update(room.tiles())
                self.explored.update(room.walls())
        x, y = position
        around = [(x + dx, y + dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
        self.explored.update(tile for tile in around if self._on_level(tile))

    def _is_floor(self, point: Point) -> bool:
        """Whether `point` is on the level and is floor, so it can be walked on."""
        return self._on_level(point) and self.level.tile(*point) is Tile.FLOOR

    def _on_level(self, point: Point) -> bool:
        x, y = point
        return 0 <= x < self.level.width and 0 <= y < self.level.height


def _sign(number: int) -> int:
    """-1, 0 or 1, the direction `number` points in."""
    return (number > 0) - (number < 0)


def _next_to(a: Point, b: Point) -> bool:
    """Whether `a` and `b` are side by side: one step north, east, south or west."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
