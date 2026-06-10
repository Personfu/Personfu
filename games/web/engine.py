"""THREAT HUNT — a serializable, browser-playable cyber-ops board game.

A minesweeper-style sweep reimagined as adversary hunting: the grid is a subnet
of hosts, the "mines" are planted APT implants, and revealing a cell is scanning
a host. Numbers are the count of adjacent compromised hosts (proximity IOCs).

Unlike the terminal games, every move here happens in its own GitHub Actions
run, so the **entire** game state must round-trip through JSON — there is no
live RNG object to rely on between moves. Implants are placed once (first scan,
first-scan-safe) and then persisted as concrete coordinates.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from ..core import Cell, neighbors

COLS = "ABCDEFGHIJKLMNOP"


class Status(str, Enum):
    HUNTING = "HUNTING"
    CONTAINED = "CONTAINED"   # win: every clean host scanned
    BREACHED = "BREACHED"     # loss: scanned an implant


def label_to_cell(label: str) -> Cell:
    """Map a board label like ``"B4"`` to a zero-based ``(x, y)`` coordinate."""
    label = label.strip().upper()
    if len(label) < 2 or label[0] not in COLS or not label[1:].isdigit():
        raise ValueError(f"bad cell label: {label!r}")
    x = COLS.index(label[0])
    y = int(label[1:]) - 1
    return x, y


def cell_to_label(x: int, y: int) -> str:
    return f"{COLS[x]}{y + 1}"


@dataclass
class ThreatHunt:
    width: int = 6
    height: int = 6
    implant_count: int = 6
    implants: Set[Cell] = field(default_factory=set)
    scanned: Set[Cell] = field(default_factory=set)
    flagged: Set[Cell] = field(default_factory=set)
    status: Status = Status.HUNTING
    deployed: bool = False
    seed: int = 0

    # -- lifecycle --------------------------------------------------------
    @classmethod
    def new(cls, width: int = 6, height: int = 6, implant_count: int = 6,
            seed: Optional[int] = None) -> "ThreatHunt":
        if seed is None:
            seed = random.randrange(1, 2**31)
        max_implants = width * height - 9
        implant_count = max(1, min(implant_count, max_implants))
        return cls(width=width, height=height, implant_count=implant_count, seed=seed)

    def _deploy_implants(self, safe: Cell) -> None:
        sx, sy = safe
        forbidden = {safe, *neighbors(sx, sy, self.width, self.height)}
        candidates = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in forbidden
        ]
        rng = random.Random(self.seed)
        self.implants = set(rng.sample(candidates, self.implant_count))
        self.deployed = True

    # -- queries ----------------------------------------------------------
    def adjacent(self, x: int, y: int) -> int:
        return sum(
            (nx, ny) in self.implants
            for nx, ny in neighbors(x, y, self.width, self.height)
        )

    @property
    def implants_remaining(self) -> int:
        return self.implant_count - len(self.flagged)

    def _clean_fully_scanned(self) -> bool:
        return len(self.scanned) == self.width * self.height - self.implant_count

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    # -- actions ----------------------------------------------------------
    def scan(self, x: int, y: int) -> None:
        if self.status is not Status.HUNTING or not self.in_bounds(x, y):
            return
        if (x, y) in self.scanned or (x, y) in self.flagged:
            return
        if not self.deployed:
            self._deploy_implants((x, y))

        if (x, y) in self.implants:
            self.scanned.add((x, y))
            self.status = Status.BREACHED
            return

        self._sweep(x, y)
        if self._clean_fully_scanned():
            self.status = Status.CONTAINED

    def flag(self, x: int, y: int) -> None:
        if self.status is not Status.HUNTING or not self.in_bounds(x, y):
            return
        if (x, y) in self.scanned:
            return
        self.flagged ^= {(x, y)}

    def _sweep(self, x: int, y: int) -> None:
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in self.scanned or (cx, cy) in self.implants:
                continue
            self.scanned.add((cx, cy))
            self.flagged.discard((cx, cy))
            if self.adjacent(cx, cy) == 0:
                stack.extend(neighbors(cx, cy, self.width, self.height))

    # -- serialization ----------------------------------------------------
    def to_dict(self) -> Dict:
        return {
            "width": self.width,
            "height": self.height,
            "implant_count": self.implant_count,
            "implants": sorted(map(list, self.implants)),
            "scanned": sorted(map(list, self.scanned)),
            "flagged": sorted(map(list, self.flagged)),
            "status": self.status.value,
            "deployed": self.deployed,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "ThreatHunt":
        def cells(key: str) -> Set[Cell]:
            return {(int(x), int(y)) for x, y in d.get(key, [])}

        return cls(
            width=int(d["width"]),
            height=int(d["height"]),
            implant_count=int(d["implant_count"]),
            implants=cells("implants"),
            scanned=cells("scanned"),
            flagged=cells("flagged"),
            status=Status(d.get("status", "HUNTING")),
            deployed=bool(d.get("deployed", False)),
            seed=int(d.get("seed", 0)),
        )
