"""Small, dependency-free grid helpers shared across the games.

Kept deliberately pure (no I/O, no global state) so the game-logic layers
that build on top of it stay trivially unit-testable.
"""
from __future__ import annotations

from typing import Iterator, Tuple

Cell = Tuple[int, int]

# 4-connected and 8-connected neighbour offsets.
ORTHOGONAL = ((0, -1), (0, 1), (-1, 0), (1, 0))
DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))
NEIGHBORS_8 = ORTHOGONAL + DIAGONAL


def in_bounds(x: int, y: int, width: int, height: int) -> bool:
    """Return True when ``(x, y)`` lies inside a ``width`` x ``height`` grid."""
    return 0 <= x < width and 0 <= y < height


def neighbors(
    x: int,
    y: int,
    width: int,
    height: int,
    offsets: Tuple[Cell, ...] = NEIGHBORS_8,
) -> Iterator[Cell]:
    """Yield in-bounds neighbours of ``(x, y)`` for the given offset set."""
    for dx, dy in offsets:
        nx, ny = x + dx, y + dy
        if in_bounds(nx, ny, width, height):
            yield nx, ny


def clamp(value: int, low: int, high: int) -> int:
    """Clamp ``value`` into the inclusive range ``[low, high]``."""
    return max(low, min(high, value))
