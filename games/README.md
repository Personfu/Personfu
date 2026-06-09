# 🎮 Personfu Arcade

A small collection of **actually playable**, dependency-free terminal games.
No `pip install` required — they run on the Python standard library (`curses`)
that ships with every Unix/macOS Python, and on Windows with `windows-curses`.

```bash
# clone, then from the repo root:
python3 -m games          # opens the launcher menu
```

| Game | Controls |
|------|----------|
| 🐍 **Snake** | Arrow keys / `WASD` to steer · `q` to quit |
| 💣 **Minesweeper** | Move with arrows/`WASD` · `space` reveal · `f` flag · `q` quit |

## Why it's built this way

Each game is split into two layers:

- **A pure rules engine** (`SnakeGame`, `Minesweeper`) — no I/O, no globals,
  deterministic given an injected `random.Random`. This is where the logic lives:
  collision detection, flood-fill reveals, first-click-safe mine placement,
  win/loss derivation.
- **A thin curses front-end** (`play`) that only renders state and forwards input.

That separation is what makes the engines trivially testable:

```bash
pip install pytest
pytest            # 15 tests covering both engines, deterministic via seeded RNG
```

## Layout

```
games/
├── __main__.py        # launcher menu (python3 -m games)
├── snake.py           # SnakeGame engine + curses UI
├── minesweeper.py     # Minesweeper engine + curses UI
└── core/grid.py       # shared, side-effect-free grid helpers
tests/
├── test_snake.py
└── test_minesweeper.py
```

Built as a demonstration of clean, testable Python — engine logic that would
survive a code review, not just a script that happens to run.
