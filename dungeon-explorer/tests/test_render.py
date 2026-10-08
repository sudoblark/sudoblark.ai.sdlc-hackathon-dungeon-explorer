from helpers import game_on, level_from

from dungeon_explorer.game import Game
from dungeon_explorer.level import Item, Point
from dungeon_explorer.render import draw_mini_map, draw_view

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


# An 8x6 level, so the mini-map is 4x3: each character covers 2x2 tiles.
CAVE = level_from(
    "########",
    "#..#####",
    "#..#####",
    "#......#",
    "########",
    "########",
    stairs_down=(6, 3),
)


def test_the_mini_map_shows_the_whole_level_at_half_scale():
    game = game_on(CAVE, position=(1, 1))
    game.explored = _everywhere(8, 6)

    assert draw_mini_map(game) == [
        "@.##",
        "...>",
        "####",
    ]


def test_the_mini_map_leaves_unexplored_blocks_blank_and_hides_the_stairs():
    game = game_on(CAVE, position=(1, 1))
    game.explored = {(x, y) for y in range(3) for x in range(3)}

    assert draw_mini_map(game) == [
        "@.  ",
        "..  ",
        "    ",
    ]


def test_a_block_of_explored_wall_shows_as_wall_on_the_mini_map():
    game = game_on(CAVE, position=(1, 1))
    game.explored = {(4, 0), (5, 0), (4, 1), (5, 1)}

    assert draw_mini_map(game) == [
        "@ # ",
        "    ",
        "    ",
    ]


def test_the_mini_map_covers_the_last_column_and_row_of_odd_sized_levels():
    game = game_on(HALL, position=(1, 1))
    game.explored = _everywhere(7, 4)

    # 7 wide, so the last column of blocks is only one tile wide.
    assert draw_mini_map(game) == [
        "@..#",
        "!.>#",
    ]


# A 6x4 level, with the stairs and a potion sharing the middle block of the
# bottom row, and gold on its own in the middle block of the top row.
VAULT = level_from(
    "######",
    "#....#",
    "#....#",
    "######",
    items={(3, 1): Item("gold", "$"), (3, 2): POTION},
    stairs_down=(2, 2),
)


def test_the_mini_map_shows_items_but_the_stairs_win_a_shared_block():
    game = game_on(VAULT, position=(1, 1))
    game.explored = _everywhere(6, 4)

    assert draw_mini_map(game) == [
        "@$.",
        ".>.",
    ]


def test_the_mini_map_hides_items_on_unexplored_tiles():
    game = game_on(VAULT, position=(1, 1))
    game.explored = _everywhere(6, 4) - {(3, 1)}

    assert draw_mini_map(game) == [
        "@..",
        ".>.",
    ]


def test_the_full_mini_map_is_32_by_16_with_the_player_in_their_block():
    game = Game.new(seed=42)

    lines = draw_mini_map(game)

    assert len(lines) == 16
    assert all(len(line) == 32 for line in lines)
    x, y = game.player.position
    assert lines[y // 2][x // 2] == "@"
