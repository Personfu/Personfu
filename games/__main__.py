"""Launcher: ``python3 -m games`` opens a menu to pick a game.

Falls back to a readable message when stdout is not an interactive TTY (CI,
piped output) instead of crashing inside curses.
"""
from __future__ import annotations

import sys
from typing import Callable, Dict, Tuple

from . import GAMES, __version__

BANNER = r"""
  ____                            __        _                      _
 |  _ \ ___ _ __ ___  ___  _ __  / _|_   _ / \   _ __ ___ __ _  __| | ___
 | |_) / _ \ '__/ __|/ _ \| '_ \| |_| | | / _ \ | '__/ __/ _` |/ _` |/ _ \
 |  __/  __/ |  \__ \ (_) | | | |  _| |_| / ___ \| | | (_| (_| | (_| |  __/
 |_|   \___|_|  |___/\___/|_| |_|_|  \__,_/_/   \_\_|  \___\__,_|\__,_|\___|
"""


def _menu(stdscr, games: Dict[str, Tuple[str, Callable]]):  # pragma: no cover
    import curses

    curses.curs_set(0)
    items = list(games.items())
    idx = 0
    while True:
        stdscr.erase()
        for i, line in enumerate(BANNER.strip("\n").splitlines()):
            stdscr.addstr(i + 1, 2, line)
        stdscr.addstr(9, 2, f"  v{__version__} — arrow keys to choose, Enter to play, q to quit")
        for i, (_, (label, _fn)) in enumerate(items):
            prefix = " > " if i == idx else "   "
            attr = curses.A_REVERSE if i == idx else 0
            stdscr.addstr(11 + i, 4, f"{prefix}{label}", attr)
        stdscr.refresh()

        key = stdscr.getch()
        if key in (ord("q"), 27):
            return
        if key in (curses.KEY_UP, ord("k")):
            idx = (idx - 1) % len(items)
        elif key in (curses.KEY_DOWN, ord("j")):
            idx = (idx + 1) % len(items)
        elif key in (ord("\n"), curses.KEY_ENTER, ord(" ")):
            items[idx][1][1](stdscr)


def main() -> int:
    if not sys.stdout.isatty():
        print("Personfu Arcade needs an interactive terminal.")
        print("Run it locally with:  python3 -m games")
        print("Available games:", ", ".join(label for label, _ in GAMES.values()))
        return 0
    try:
        import curses
    except ImportError:  # pragma: no cover - Windows without windows-curses
        print("This launcher needs the 'curses' module (pip install windows-curses on Windows).")
        return 1
    curses.wrapper(_menu, GAMES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
