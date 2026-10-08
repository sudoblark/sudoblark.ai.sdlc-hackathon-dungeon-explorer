from helpers import game_on, level_from

from dungeon_explorer.game import Game
from dungeon_explorer.level import Item, Point
from dungeon_explorer.render import draw_view

POTION = Item("potion", "!")

HALL = level_from(
    "#######",
    "#.....#",
    "#.....#",
    "#######",
    items={(1, 2): POTION},
    stairs_down=(5, 2),
)


def _everywhere(width: int, height: int) -> set[Point]:
    return {(x, y) for y in range(height) for x in range(width)}


def test_the_view_draws_explored_tiles_with_the_player_in_the_middle():
    game = game_on(HALL, position=(3, 1))
    game.explored = _everywhere(7, 4)

    assert draw_view(game, width=7, height=3) == [
        "#######",
        "#..@..#",
        "#!...>#",
    ]


def test_unexplored_tiles_are_blank_and_hide_what_is_on_them():
    game = game_on(HALL, position=(3, 1))
    # Only the eight tiles around the player, which leaves the potion at
    # (1, 2) and the stairs at (5, 2) unexplored.
    game.explored = {(x, y) for y in range(3) for x in range(2, 5)}

    assert draw_view(game, width=7, height=3) == [
        "  ###  ",
        "  .@.  ",
        "  ...  ",
    ]


def test_past_the_edge_of_the_level_is_blank():
    game = game_on(HALL, position=(1, 1))
    game.explored = _everywhere(7, 4)

    assert draw_view(game, width=7, height=3) == [
        "  #####",
        "  #@...",
        "  #!...",
    ]


def test_the_player_is_drawn_over_the_stairs():
    game = game_on(HALL, position=(5, 2))
    game.explored = _everywhere(7, 4)

    assert draw_view(game, width=3, height=3) == [
        "..#",
        ".@#",
        "###",
    ]


def test_the_full_view_is_31_by_15_with_the_player_in_the_middle():
    lines = draw_view(Game.new(seed=42))

    assert len(lines) == 15
    assert all(len(line) == 31 for line in lines)
    assert lines[7][15] == "@"
