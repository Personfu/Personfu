"""Minesweeper — engine + terminal front-end.

:class:`Minesweeper` is a pure rules engine: mine layout is generated lazily on
the first reveal so the opening click is always safe, reveals flood-fill across
zero-adjacency regions, and win/loss are derived from board state rather than
tracked by hand. The curses :func:`play` layer only renders and routes input.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Set

from .core import Cell, neighbors


class State(Enum):
    PLAYING = auto()
    WON = auto()
    LOST = auto()


@dataclass
class Minesweeper:
    width: int = 16
    height: int = 16
    mines: int = 40
    rng: random.Random = field(default_factory=random.Random)

    revealed: Set[Cell] = field(init=False, default_factory=set)
    flagged: Set[Cell] = field(init=False, default_factory=set)
    mine_set: Set[Cell] = field(init=False, default_factory=set)
    state: State = field(init=False, default=State.PLAYING)
    _placed: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        max_mines = self.width * self.height - 9  # keep a safe first-click pocket
        if not (1 <= self.mines <= max_mines):
            raise ValueError(f"mines must be in 1..{max_mines}")

    # -- board generation -------------------------------------------------
    def _place_mines(self, safe: Cell) -> None:
        sx, sy = safe
        forbidden = {safe, *neighbors(sx, sy, self.width, self.height)}
        candidates = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in forbidden
        ]
        self.mine_set = set(self.rng.sample(candidates, self.mines))
        self._placed = True

    def adjacent_mines(self, x: int, y: int) -> int:
        return sum(
            (nx, ny) in self.mine_set
            for nx, ny in neighbors(x, y, self.width, self.height)
        )

    # -- player actions ---------------------------------------------------
    def toggle_flag(self, x: int, y: int) -> None:
        if self.state is not State.PLAYING or (x, y) in self.revealed:
            return
        self.flagged.symmetric_difference_update({(x, y)})

    def reveal(self, x: int, y: int) -> None:
        """Reveal a cell, flood-filling empties and resolving win/loss."""
        if self.state is not State.PLAYING:
            return
        if (x, y) in self.revealed or (x, y) in self.flagged:
            return
        if not self._placed:
            self._place_mines((x, y))

        if (x, y) in self.mine_set:
            self.revealed.add((x, y))
            self.state = State.LOST
            return

        self._flood(x, y)
        if self._is_cleared():
            self.state = State.WON

    def _flood(self, x: int, y: int) -> None:
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in self.revealed or (cx, cy) in self.mine_set:
                continue
            self.revealed.add((cx, cy))
            self.flagged.discard((cx, cy))
            if self.adjacent_mines(cx, cy) == 0:
                stack.extend(neighbors(cx, cy, self.width, self.height))

    def _is_cleared(self) -> bool:
        return len(self.revealed) == self.width * self.height - self.mines

    @property
    def mines_remaining(self) -> int:
        return self.mines - len(self.flagged)

    def glyph(self, x: int, y: int, reveal_all: bool = False) -> str:
        """One-character display glyph for a cell, given the current state."""
        cell = (x, y)
        if (reveal_all or self.state is State.LOST) and cell in self.mine_set:
            return "*"
        if cell in self.flagged:
            return "F"
        if cell not in self.revealed:
            return "#"
        n = self.adjacent_mines(x, y)
        return str(n) if n else "."


def play(stdscr) -> Optional[State]:  # pragma: no cover
    """Curses front-end: arrow/WASD to move, space reveals, f flags, q quits."""
    import curses

    curses.curs_set(0)
    game = Minesweeper()
    cx = cy = 0
    moves = {
        curses.KEY_UP: (0, -1), ord("w"): (0, -1),
        curses.KEY_DOWN: (0, 1), ord("s"): (0, 1),
        curses.KEY_LEFT: (-1, 0), ord("a"): (-1, 0),
        curses.KEY_RIGHT: (1, 0), ord("d"): (1, 0),
    }

    while True:
        _render(stdscr, game, cx, cy)
        key = stdscr.getch()
        if key in (ord("q"), 27):
            return None
        if key in moves:
            dx, dy = moves[key]
            cx = max(0, min(game.width - 1, cx + dx))
            cy = max(0, min(game.height - 1, cy + dy))
        elif key in (ord(" "), ord("\n"), curses.KEY_ENTER):
            game.reveal(cx, cy)
        elif key in (ord("f"), ord("F")):
            game.toggle_flag(cx, cy)

        if game.state is not State.PLAYING:
            _render(stdscr, game, cx, cy)
            msg = "YOU WIN!" if game.state is State.WON else "BOOM."
            stdscr.addstr(0, 2, f" {msg}  press any key ")
            stdscr.nodelay(False)
            stdscr.getch()
            return game.state


def _render(stdscr, game: Minesweeper, cx: int, cy: int) -> None:  # pragma: no cover
    stdscr.erase()
    stdscr.border()
    stdscr.addstr(0, 2, f" THREAT HUNT // implants {game.mines_remaining}   (space scan, f flag, q quit) ")
    for y in range(game.height):
        for x in range(game.width):
            g = game.glyph(x, y)
            attr = 0
            if (x, y) == (cx, cy):
                import curses
                attr = curses.A_REVERSE
            try:
                stdscr.addstr(y + 1, x * 2 + 2, g, attr)
            except Exception:
                pass
    stdscr.refresh()
