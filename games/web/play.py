"""Controller for the browser-playable Threat Hunt.

Invoked by the play workflow:

    python -m games.web.play apply "ops: scan B4"   # parse + apply a move
    python -m games.web.play render                 # just redraw (bootstrap)

It loads/saves ``games/web/state.json``, rewrites the THREAT-HUNT block inside
``README.md``, and writes the issue reply to ``games/web/last_move.md`` for the
workflow to post. The issue title is untrusted input, so parsing is strict.

The player's GitHub login arrives via the ``ISSUE_AUTHOR`` env var; it is used
for board attribution and the hall of fame. Only logins matching GitHub's own
username rules are accepted, so it cannot smuggle markdown into the README.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

from .engine import Status, ThreatHunt, label_to_cell
from .render import END, START, move_comment, render_block

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "games" / "web" / "state.json"
README_PATH = ROOT / "README.md"
COMMENT_PATH = ROOT / "games" / "web" / "last_move.md"

# Strict: "ops: <verb> [CELL]" — verb in scan/flag/new, cell like B4.
MOVE_RE = re.compile(r"^\s*ops:\s*(scan|flag|new)\s*([A-Pa-p]\d{1,2})?\s*$")
# GitHub login rules: alphanumerics and single hyphens, 1-39 chars.
ACTOR_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")
MAX_CHAMPIONS = 10


def load_state() -> Tuple[ThreatHunt, List[str], str]:
    """Return (game, champions, last_move). Tolerates the legacy bare-game shape."""
    if not STATE_PATH.exists():
        return ThreatHunt.new(), [], ""
    raw = json.loads(STATE_PATH.read_text())
    if "game" in raw:
        return (
            ThreatHunt.from_dict(raw["game"]),
            list(raw.get("champions", [])),
            str(raw.get("last_move", "")),
        )
    return ThreatHunt.from_dict(raw), [], ""


def save_state(game: ThreatHunt, champions: List[str], last_move: str) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "game": game.to_dict(),
        "champions": champions[-MAX_CHAMPIONS:],
        "last_move": last_move,
    }
    STATE_PATH.write_text(json.dumps(payload, indent=2) + "\n")


def sanitize_actor(raw: str) -> str:
    raw = (raw or "").strip()
    return raw if ACTOR_RE.match(raw) else ""


def repo_slug() -> Tuple[str, str]:
    slug = os.environ.get("GITHUB_REPOSITORY", "Personfu/Personfu")
    owner, _, repo = slug.partition("/")
    return owner or "Personfu", repo or "Personfu"


def update_readme(game: ThreatHunt, owner: str, repo: str,
                  champions: List[str], last_move: str) -> None:
    block = render_block(game, owner, repo, last_move=last_move, champions=champions)
    text = README_PATH.read_text()
    if START in text and END in text:
        pre = text[: text.index(START)]
        post = text[text.index(END) + len(END):]
        README_PATH.write_text(pre + block + post)
    else:
        # First install: append the block near the end, before the footer rule.
        README_PATH.write_text(text.rstrip() + "\n\n" + block + "\n")


def parse_move(title: str) -> Tuple[str, str, bool]:
    m = MOVE_RE.match(title or "")
    if not m:
        return "", "", False
    verb, cell = m.group(1).lower(), (m.group(2) or "").upper()
    if verb in ("scan", "flag") and not cell:
        return verb, "", False
    return verb, cell, True


def apply_move(title: str, actor: str = "") -> ThreatHunt:
    owner, repo = repo_slug()
    verb, label, ok = parse_move(title)
    actor = sanitize_actor(actor)
    game, champions, last_move = load_state()

    if ok and verb == "new":
        game = ThreatHunt.new()
    elif ok and verb == "scan":
        game.scan(*label_to_cell(label))
    elif ok and verb == "flag":
        game.flag(*label_to_cell(label))

    if ok:
        last_move = f"`{verb} {label}`".replace("  ", " ").replace(" `", "`")
        if actor:
            last_move += f" by @{actor}"
        if game.status is Status.CONTAINED and actor and actor not in champions:
            champions.append(actor)

    save_state(game, champions, last_move)
    update_readme(game, owner, repo, champions, last_move)
    COMMENT_PATH.write_text(move_comment(game, verb, label, ok))
    return game


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "render"
    if cmd == "apply":
        title = argv[2] if len(argv) > 2 else ""
        actor = os.environ.get("ISSUE_AUTHOR", "")
        game = apply_move(title, actor)
        print(f"applied: {title!r} -> {game.status.value}")
        return 0
    if cmd == "render":
        owner, repo = repo_slug()
        game, champions, last_move = load_state()
        save_state(game, champions, last_move)
        update_readme(game, owner, repo, champions, last_move)
        print(f"rendered: {game.status.value}")
        return 0
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
