"""Personfu Arcade — a tiny collection of dependency-free terminal games.

Each game ships its rules as a pure, unit-tested engine class and a thin
curses presentation layer. Run the launcher with::

    python3 -m games
"""
from . import minesweeper, snake
from .minesweeper import Minesweeper, State
from .snake import Direction, SnakeGame

__version__ = "1.0.0"

GAMES = {
    "snake": ("Snake", snake.play),
    "minesweeper": ("Minesweeper", minesweeper.play),
}

__all__ = [
    "Direction",
    "GAMES",
    "Minesweeper",
    "SnakeGame",
    "State",
    "__version__",
    "minesweeper",
    "snake",
]
