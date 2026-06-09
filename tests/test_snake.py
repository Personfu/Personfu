"""Deterministic unit tests for the headless Snake engine."""
import random

import pytest

from games.snake import Direction, SnakeGame


def make_game() -> SnakeGame:
    # Seeded rng makes food placement reproducible.
    return SnakeGame(width=10, height=8, rng=random.Random(1234))


def test_initial_state():
    g = make_game()
    assert g.alive
    assert g.score == 0
    assert len(g.snake) == 3
    assert g.head == (5, 4)
    assert g.direction is Direction.RIGHT


def test_tick_moves_head_forward():
    g = make_game()
    g.tick()
    assert g.head == (6, 4)
    assert len(g.snake) == 3  # no growth without food


def test_cannot_reverse_into_neck():
    g = make_game()
    g.change_direction(Direction.LEFT)  # opposite of RIGHT — ignored
    g.tick()
    assert g.head == (6, 4)


def test_wall_collision_kills():
    g = make_game()
    g.change_direction(Direction.UP)
    for _ in range(10):
        g.tick()
    assert not g.alive
    assert g.head[1] < 0 or g.head == (5, 0)


def test_eating_food_grows_and_scores():
    g = make_game()
    g.food = (6, 4)  # directly ahead of the head
    g.tick()
    assert g.score == 1
    assert len(g.snake) == 4
    assert g.food != (6, 4)  # respawned elsewhere


def test_self_collision_kills():
    g = SnakeGame(width=12, height=12, rng=random.Random(0))
    # Grow to length 5 by feeding straight ahead, so a tight U-turn can bite.
    for _ in range(2):
        hx, hy = g.head
        g.food = (hx + 1, hy)
        g.tick()
    assert len(g.snake) == 5
    g.food = (-1, -1)  # park food off-board so length stays fixed
    # A 3-step square turn now walks the head back into the body.
    for d in (Direction.UP, Direction.LEFT, Direction.DOWN):
        g.change_direction(d)
        g.tick()
    assert not g.alive


def test_opposite_directions():
    assert Direction.UP.opposite is Direction.DOWN
    assert Direction.LEFT.opposite is Direction.RIGHT


def test_rejects_tiny_board():
    with pytest.raises(ValueError):
        SnakeGame(width=3, height=3)
