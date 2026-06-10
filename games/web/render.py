"""Render a :class:`ThreatHunt` board to README markdown with clickable cells.

Each unscanned host is a link that opens a pre-filled GitHub issue; submitting
it triggers the play workflow, which applies the move and redraws this block.
That is the whole "play in the browser, no clone" trick — the board *is* a grid
of issue links.
"""
from __future__ import annotations

import urllib.parse

from .engine import COLS, Status, ThreatHunt, cell_to_label

# Markers the play controller rewrites inside README.md.
START = "<!-- THREAT-HUNT:START -->"
END = "<!-- THREAT-HUNT:END -->"

HIDDEN = "🟦"
EMPTY = "⬜"
FLAG = "🚩"
HIT = "💥"
IMPLANT = "☣️"
NUM = {0: EMPTY, 1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣",
       5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣"}


def issue_url(owner: str, repo: str, action: str, label: str = "") -> str:
    title = f"ops: {action} {label}".strip()
    body = (
        "Submit this issue to make your move — the Threat Hunt bot will play "
        "it, redraw the board on the profile, and close this issue.\n\n"
        "_Auto-generated. You can edit the title: `ops: scan B4`, "
        "`ops: flag B4`, or `ops: new`._"
    )
    q = urllib.parse.urlencode({"title": title, "body": body})
    return f"https://github.com/{owner}/{repo}/issues/new?{q}"


def _cell_md(game: ThreatHunt, x: int, y: int, owner: str, repo: str) -> str:
    over = game.status is not Status.HUNTING
    if (x, y) in game.scanned:
        if (x, y) in game.implants:
            return HIT
        return NUM[game.adjacent(x, y)]
    if over:
        if (x, y) in game.implants:
            return IMPLANT
        return FLAG if (x, y) in game.flagged else HIDDEN
    glyph = FLAG if (x, y) in game.flagged else HIDDEN
    return f"[{glyph}]({issue_url(owner, repo, 'scan', cell_to_label(x, y))})"


def status_line(game: ThreatHunt) -> str:
    if game.status is Status.CONTAINED:
        return "🟢 **THREAT CONTAINED** — subnet swept clean. Adversary evicted."
    if game.status is Status.BREACHED:
        return "🔴 **BREACHED** — you scanned a live implant. Detonation."
    return (
        f"🟡 **HUNTING** — implants suspected: `{game.implants_remaining}` · "
        f"hosts scanned: `{len(game.scanned)}`"
    )


def render_block(game: ThreatHunt, owner: str, repo: str) -> str:
    header = "| · | " + " | ".join(COLS[: game.width]) + " |"
    divider = "|---|" + "---|" * game.width
    rows = [header, divider]
    for y in range(game.height):
        cells = [_cell_md(game, x, y, owner, repo) for x in range(game.width)]
        rows.append(f"| **{y + 1}** | " + " | ".join(cells) + " |")
    board = "\n".join(rows)

    new_url = issue_url(owner, repo, "new")
    lines = [
        START,
        "",
        "### 🛰️ THREAT HUNT — Play in Your Browser",
        "",
        "> Click a host to **scan** it. Numbers count adjacent compromised hosts. "
        "Find every clean host without detonating an implant. "
        "No clone, no install — every click opens an issue a bot plays for you.",
        "",
        status_line(game),
        "",
        board,
        "",
        f"🚩 To flag a suspected implant, open `ops: flag B4`. "
        f"&nbsp;·&nbsp; [**▶ START A NEW HUNT**]({new_url})",
        "",
        f"<sub>🟦 host &nbsp; ⬜ clean &nbsp; 1️⃣–8️⃣ adjacent implants &nbsp; "
        f"🚩 flagged &nbsp; ☣️ implant &nbsp; 💥 detonated</sub>",
        "",
        END,
    ]
    return "\n".join(lines)


def move_comment(game: ThreatHunt, action: str, label: str, ok: bool) -> str:
    head = {
        Status.CONTAINED: "🟢 **THREAT CONTAINED.** The subnet is clean — nice hunt.",
        Status.BREACHED: "🔴 **BREACHED.** That host was running a live implant. "
                         "Start a new hunt from the profile.",
        Status.HUNTING: "✅ Move applied — the board on the profile has been redrawn.",
    }[game.status]
    if not ok:
        head = ("⚠️ Couldn't read that move. Use `ops: scan B4`, `ops: flag B4`, "
                "or `ops: new`.")
    return (
        f"{head}\n\n"
        f"- action: `{action} {label}`".rstrip() + "\n"
        f"- status: `{game.status.value}`\n"
        f"- hosts scanned: `{len(game.scanned)}` · implants suspected: "
        f"`{game.implants_remaining}`\n\n"
        "_Threat Hunt · automated by GitHub Actions_"
    )
