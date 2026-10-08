import copy

import pytest
from helpers import game_on, level_from

from dungeon_explorer.commands import Descend, Drink, Move, parse_command
from dungeon_explorer.game import Game
from dungeon_explorer.level import Direction, Item

ROOM = level_from(
    "#####",
    "#...#",
    "#...#",
    "#...#",
    "#####",
)


@pytest.mark.parametrize(
    ("text", "command"),
    [
        ("w", Move(Direction.NORTH)),
        ("a", Move(Direction.WEST)),
        ("s", Move(Direction.SOUTH)),
        ("d", Move(Direction.EAST)),
        (">", Descend()),
        ("p", Drink()),
    ],
)
def test_each_key_gives_its_command(text, command):
    assert parse_command(text) == command


@pytest.mark.parametrize("text", ["W", " d ", "s\n"])
def test_case_and_surrounding_spaces_dont_matter(text):
    assert isinstance(parse_command(text), Move)


@pytest.mark.parametrize("text", ["", "x", "ww", "north", "i", "?", "q"])
def test_anything_else_gives_no_command(text):
    assert parse_command(text) is None


@pytest.mark.parametrize("direction", list(Direction))
def test_a_move_command_moves_the_player_just_as_move_does(direction):
    commanded = game_on(ROOM, position=(2, 2))
    direct = copy.deepcopy(commanded)

    Move(direction).execute(commanded)
    direct.move(direction)

    assert commanded == direct
    assert commanded.player.position != (2, 2)


def test_a_descend_command_goes_down_just_as_descend_does():
    commanded = Game.new(seed=42)
    commanded.player.position = commanded.level.stairs_down
    direct = copy.deepcopy(commanded)

    Descend().execute(commanded)
    direct.descend()

    assert commanded == direct
    assert commanded.depth == 2


def test_a_drink_command_drinks_just_as_drink_does():
    commanded = Game.new(seed=42)
    commanded.player.inventory = [Item("potion", "!", healing=5)]
    commanded.player.hit_points = 12
    direct = copy.deepcopy(commanded)

    Drink().execute(commanded)
    direct.drink()

    assert commanded == direct
    assert commanded.player.hit_points == 17
