"""Deterministic unit tests for the Minesweeper engine."""
import random

import pytest

from games.minesweeper import Minesweeper, State


def make_game(mines: int = 10) -> Minesweeper:
    return Minesweeper(width=8, height=8, mines=mines, rng=random.Random(42))


def test_first_click_is_always_safe():
    g = make_game()
    g.reveal(4, 4)
    assert g.state in (State.PLAYING, State.WON)
    assert (4, 4) not in g.mine_set  # never a mine
    assert (4, 4) in g.revealed


def test_mine_count_is_exact():
    g = make_game(mines=12)
    g.reveal(0, 0)
    assert len(g.mine_set) == 12


def test_flagging_toggles():
    g = make_game()
    g.toggle_flag(2, 2)
    assert (2, 2) in g.flagged
    assert g.mines_remaining == g.mines - 1
    g.toggle_flag(2, 2)
    assert (2, 2) not in g.flagged


def test_revealing_a_mine_loses():
    g = make_game()
    g.reveal(0, 0)  # generates the board, safe
    mine = next(iter(g.mine_set))
    g.reveal(*mine)
    assert g.state is State.LOST


def test_revealing_all_safe_cells_wins():
    g = make_game(mines=5)
    g.reveal(4, 4)
    for y in range(g.height):
        for x in range(g.width):
            if (x, y) not in g.mine_set:
                g.reveal(x, y)
    assert g.state is State.WON


def test_flood_fill_opens_region():
    g = make_game(mines=1)
    g.reveal(4, 4)
    # With a single mine, the first reveal should cascade across most cells.
    assert len(g.revealed) > 1


def test_flagged_cell_is_not_revealed():
    g = make_game()
    g.reveal(4, 4)
    target = next(
        (x, y)
        for y in range(g.height)
        for x in range(g.width)
        if (x, y) not in g.revealed and (x, y) not in g.mine_set
    )
    g.toggle_flag(*target)
    g.reveal(*target)
    assert target not in g.revealed


def test_invalid_mine_count_rejected():
    with pytest.raises(ValueError):
        Minesweeper(width=4, height=4, mines=999)
