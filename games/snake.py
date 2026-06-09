"""Classic Snake — a small, well-factored implementation.

The :class:`SnakeGame` class holds *all* of the rules and none of the
rendering. State advances one step at a time through :meth:`SnakeGame.tick`,
which makes the engine deterministic and fully unit-testable (see
``tests/test_snake.py``). The curses front-end in :func:`play` is a thin
presentation layer that only reads state and forwards input.
"""
from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque, List, Optional

from .core import Cell


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def opposite(self) -> "Direction":
        dx, dy = self.value
        return Direction((-dx, -dy))


@dataclass
class SnakeGame:
    """Headless Snake engine.

    Parameters
    ----------
    width, height:
        Board dimensions in cells.
    rng:
        Injectable :class:`random.Random` so tests can pin food placement.
    """

    width: int = 30
    height: int = 20
    rng: random.Random = field(default_factory=random.Random)

    snake: Deque[Cell] = field(init=False)
    direction: Direction = field(init=False)
    food: Cell = field(init=False)
    score: int = field(init=False, default=0)
    alive: bool = field(init=False, default=True)
    _pending: Direction = field(init=False)

    def __post_init__(self) -> None:
        if self.width < 4 or self.height < 4:
            raise ValueError("board must be at least 4x4")
        self.reset()

    def reset(self) -> None:
        cx, cy = self.width // 2, self.height // 2
        # Three-segment snake, head first, pointing right.
        self.snake = deque([(cx, cy), (cx - 1, cy), (cx - 2, cy)])
        self.direction = Direction.RIGHT
        self._pending = Direction.RIGHT
        self.score = 0
        self.alive = True
        self.food = self._spawn_food()

    @property
    def head(self) -> Cell:
        return self.snake[0]

    def change_direction(self, new: Direction) -> None:
        """Queue a turn, ignoring 180° reversals into the snake's own neck."""
        if new.opposite is not self.direction:
            self._pending = new

    def _spawn_food(self) -> Cell:
        free = self._free_cells()
        # ``_free_cells`` is only empty on a perfect win; caller guards on that.
        return self.rng.choice(free) if free else self.head

    def _free_cells(self) -> List[Cell]:
        occupied = set(self.snake)
        return [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in occupied
        ]

    def tick(self) -> bool:
        """Advance one frame. Returns ``self.alive`` after the step."""
        if not self.alive:
            return False

        self.direction = self._pending
        dx, dy = self.direction.value
        hx, hy = self.head
        new_head = (hx + dx, hy + dy)

        if self._is_fatal(new_head):
            self.alive = False
            return False

        self.snake.appendleft(new_head)
        if new_head == self.food:
            self.score += 1
            if len(self.snake) == self.width * self.height:
                self.alive = False  # board cleared — a win is also game-over
            else:
                self.food = self._spawn_food()
        else:
            self.snake.pop()  # no growth: drop the tail
        return self.alive

    def _is_fatal(self, cell: Cell) -> bool:
        x, y = cell
        if not (0 <= x < self.width and 0 <= y < self.height):
            return True  # wall
        # Walking onto the current tail tip is safe because it moves away,
        # unless the snake is about to grow into it.
        body = set(self.snake)
        if cell == self.snake[-1] and cell != self.food:
            body.discard(self.snake[-1])
        return cell in body


def play(stdscr, *, tick_seconds: float = 0.12) -> Optional[int]:  # pragma: no cover
    """Curses front-end. Returns the final score, or ``None`` if quit early."""
    import curses

    curses.curs_set(0)
    stdscr.nodelay(True)
    max_y, max_x = stdscr.getmaxyx()
    width = max(10, min(48, (max_x - 2) // 2))
    height = max(8, min(24, max_y - 4))
    game = SnakeGame(width=width, height=height)

    keymap = {
        curses.KEY_UP: Direction.UP,
        curses.KEY_DOWN: Direction.DOWN,
        curses.KEY_LEFT: Direction.LEFT,
        curses.KEY_RIGHT: Direction.RIGHT,
        ord("w"): Direction.UP,
        ord("s"): Direction.DOWN,
        ord("a"): Direction.LEFT,
        ord("d"): Direction.RIGHT,
    }

    while True:
        key = stdscr.getch()
        if key in (ord("q"), 27):
            return None
        if key in keymap:
            game.change_direction(keymap[key])

        game.tick()
        _render(stdscr, game)
        if not game.alive:
            stdscr.nodelay(False)
            stdscr.addstr(0, 2, f" GAME OVER — score {game.score}.  press any key ")
            stdscr.getch()
            return game.score

        curses.napms(int(tick_seconds * 1000))


def _render(stdscr, game: SnakeGame) -> None:  # pragma: no cover
    stdscr.erase()
    stdscr.border()
    title = f" SNAKE   score {game.score}   (arrows/WASD, q to quit) "
    stdscr.addstr(0, 2, title)
    fx, fy = game.food
    stdscr.addstr(fy + 1, fx * 2 + 1, "*")
    for i, (x, y) in enumerate(game.snake):
        stdscr.addstr(y + 1, x * 2 + 1, "@" if i == 0 else "o")
    stdscr.refresh()
