# 🕹️ CYBER OPS ARCADE

Dependency-free games themed around threat actors and security operations.
No `pip install` — they run on the Python standard library (`curses`), and on
Windows with `windows-curses`.

```bash
python3 -m games          # opens the launcher
```

| Game | Theme | Controls |
|------|-------|----------|
| 🪱 **NET WORM** | a self-propagating worm crawling the subnet, consuming vulnerable nodes | arrows / `WASD` · `q` quit |
| 🛰️ **THREAT HUNT** | sweep a subnet for planted APT implants without detonating one | arrows/`WASD` move · `space` scan · `f` flag · `q` quit |

## 🌐 Play THREAT HUNT in the browser

The same hunt is playable **directly from the profile README** — no clone. Each
click opens a pre-filled GitHub issue; an Actions workflow plays the move,
redraws the board, and closes the issue.

- engine: [`web/engine.py`](web/engine.py) — fully serializable (state round-trips
  through JSON, since every move runs in its own Actions job)
- board renderer: [`web/render.py`](web/render.py) — turns state into a clickable
  markdown grid of issue links
- controller: [`web/play.py`](web/play.py) — invoked by `.github/workflows/play.yml`

## Why it's built this way

Every game splits a **pure rules engine** (no I/O, no globals, deterministic via
an injected/seeded `random.Random`) from a thin front-end. That separation is
what makes the logic testable:

```bash
pip install pytest
pytest            # 25 tests across the terminal engines and the browser hunt
```

## Layout

```
games/
├── __main__.py        # launcher menu (python3 -m games)
├── snake.py           # NET WORM engine + curses UI
├── minesweeper.py     # THREAT HUNT engine + curses UI
├── core/grid.py       # shared, side-effect-free grid helpers
└── web/               # browser-playable THREAT HUNT (issue-driven)
    ├── engine.py
    ├── render.py
    └── play.py
tests/
├── test_snake.py
├── test_minesweeper.py
└── test_threat_hunt.py
```
