#!/usr/bin/env python3
"""
Personfu Tower Defense SVG Generator
=====================================
Generates a fully-animated cyberpunk tower defense simulation SVG
for embedding in a GitHub profile README.

All animation is pure SMIL + CSS — no JavaScript required.
Enemy units travel the glowing path via <animateMotion>/<mpath>.
Towers fire colored beams at the nearest path waypoint.
A HUD bar shows wave info, score, and base health.
"""

import math
import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Layout constants
# ─────────────────────────────────────────────────────────────────────────────
CELL  = 16           # pixels per grid cell
COLS  = 52           # grid columns
ROWS  = 13           # grid rows
GW    = COLS * CELL  # 832 – game area width
GH    = ROWS * CELL  # 208 – game area height
UI_H  = 52           # stats bar height
W, H  = GW, GH + UI_H  # 832 × 260 total

# ─────────────────────────────────────────────────────────────────────────────
# Colors  (dark cyberpunk palette)
# ─────────────────────────────────────────────────────────────────────────────
BG         = "#04080f"
GRID       = "#0c1420"
PATH_FILL  = "#0e1c36"
PATH_LINE  = "#1048c0"

TCOL = {  # tower: (neon, dark-base, glow-filter-id)
    "laser" : ("#00e5ff", "#002233", "gb"),
    "rocket": ("#39ff14", "#002200", "gg"),
    "plasma": ("#dd00ff", "#220033", "gp"),
    "mortar": ("#ff7700", "#331100", "go"),
}
ECOL = {  # enemy: (fill, glow)
    "basic": ("#ff3333", "#ff0000"),
    "fast" : ("#ffaa00", "#ff6600"),
    "heavy": ("#cc44ff", "#880099"),
}

# ─────────────────────────────────────────────────────────────────────────────
# Enemy path  (list of (col, row) grid coordinates)
# ─────────────────────────────────────────────────────────────────────────────
def make_path():
    P = []
    for c in range(0, 7):       P.append((c, 7))   # → enter left at row 7
    for r in range(7, 0, -1):   P.append((7, r))   # ↑ up col 7
    for c in range(8, 14):      P.append((c, 1))   # → row 1
    for r in range(2, 12):      P.append((14, r))  # ↓ col 14
    for c in range(15, 21):     P.append((c, 11))  # → row 11
    for r in range(10, 0, -1):  P.append((21, r))  # ↑ col 21
    for c in range(22, 28):     P.append((c, 1))   # → row 1
    for r in range(2, 12):      P.append((28, r))  # ↓ col 28
    for c in range(29, 35):     P.append((c, 11))  # → row 11
    for r in range(10, 5, -1):  P.append((35, r))  # ↑ col 35
    for c in range(36, COLS):   P.append((c, 6))   # → exit right row 6
    return P

PATH = make_path()

def cxy(col, row):
    """Pixel center of grid cell."""
    return col * CELL + CELL // 2, row * CELL + CELL // 2

def path_d():
    """SVG path data string for the enemy route."""
    x0, y0 = cxy(*PATH[0])
    parts = [f"M{x0},{y0}"]
    for p in PATH[1:]:
        x, y = cxy(*p)
        parts.append(f"L{x},{y}")
    return " ".join(parts)

# ─────────────────────────────────────────────────────────────────────────────
# Tower placements  (col, row, type)  — all verified off-path
# ─────────────────────────────────────────────────────────────────────────────
PATH_SET = set(PATH)

TOWERS = [
    (3,  4, "laser"),  (3,  9, "rocket"),
    (10, 4, "plasma"), (10, 8, "mortar"),
    (18, 4, "laser"),  (18, 8, "rocket"),
    (25, 4, "plasma"), (25, 9, "mortar"),
    (31, 4, "laser"),  (31, 8, "rocket"),
    (39, 4, "plasma"), (39, 9, "mortar"),
    (44, 4, "laser"),  (44, 9, "rocket"),
    (48, 4, "plasma"), (48, 9, "mortar"),
]

def nearest_path_pt(col, row):
    """Return the path waypoint closest to (col, row)."""
    tx, ty = cxy(col, row)
    best, bd = PATH[0], float("inf")
    for pt in PATH:
        px, py = cxy(*pt)
        d = (px - tx) ** 2 + (py - ty) ** 2
        if d < bd:
            bd, best = d, pt
    return best

# ─────────────────────────────────────────────────────────────────────────────
# SVG generation helpers
# ─────────────────────────────────────────────────────────────────────────────
def e(tag, content="", **attrs):
    """Build an SVG element string."""
    a = " ".join(
        f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items() if v is not None
    )
    if content:
        return f"<{tag} {a}>{content}</{tag}>" if a else f"<{tag}>{content}</{tag}>"
    return f"<{tag} {a}/>" if a else f"<{tag}/>"

def anim(attr, values, dur, begin="0s", key_times=None, repeat="indefinite", calc_mode=None):
    kw = dict(
        attributeName=attr,
        values=values,
        dur=f"{dur}s",
        begin=begin,
        repeatCount=repeat,
    )
    if key_times:
        kw["keyTimes"] = key_times
    if calc_mode:
        kw["calcMode"] = calc_mode
    return e("animate", **kw)

# ─────────────────────────────────────────────────────────────────────────────
# Section generators
# ─────────────────────────────────────────────────────────────────────────────

def gen_defs():
    pd = path_d()
    # Build rocket tower sub-paths (tower → nearest path point)
    tower_paths = []
    for i, (col, row, kind) in enumerate(TOWERS):
        tx, ty = cxy(col, row)
        np_ = nearest_path_pt(col, row)
        px, py = cxy(*np_)
        tower_paths.append(f'<path id="tp{i}" d="M{tx},{ty} L{px},{py}"/>')

    return f"""<defs>
  <!-- Glow filters -->
  <filter id="gb" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="4" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="gg" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="4" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="gp" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="5" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="go" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="4" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="gpath" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur stdDeviation="7" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="ge" x="-100%" y="-100%" width="300%" height="300%">
    <feGaussianBlur stdDeviation="5" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="gtxt" x="-5%" y="-20%" width="110%" height="140%">
    <feGaussianBlur stdDeviation="2" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <!-- Radial vignette -->
  <radialGradient id="vign" cx="50%" cy="50%" r="70%">
    <stop offset="0%" stop-color="transparent"/>
    <stop offset="100%" stop-color="{BG}" stop-opacity="0.65"/>
  </radialGradient>
  <!-- Enemy route path (used by animateMotion) -->
  <path id="epath" d="{pd}"/>
  <!-- Tower-to-target paths (used by rocket projectiles) -->
  {''.join(tower_paths)}
</defs>"""


def gen_style():
    return """<style>
  @keyframes lp { 0%,100%{opacity:.75} 50%{opacity:1} }
  @keyframes gp { 0%,100%{opacity:.6}  50%{opacity:1} }
  @keyframes rp { 0%,100%{opacity:.7}  50%{opacity:.95} }
  @keyframes op { 0%,100%{opacity:.7}  50%{opacity:1} }
  @keyframes scan { 0%{transform:translateY(0)} 100%{transform:translateY(16px)} }
  @keyframes blink { 0%,49%{opacity:1} 50%,100%{opacity:0} }
  .tl{animation:lp 1.8s ease-in-out infinite}
  .tr{animation:rp 2.2s ease-in-out infinite}
  .tp{animation:gp 1.5s ease-in-out infinite}
  .tm{animation:op 2.5s ease-in-out infinite}
  .cursor{animation:blink 1s step-end infinite}
</style>"""


def gen_background():
    lines = [f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    # Subtle grid
    for c in range(COLS + 1):
        x = c * CELL
        lines.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{GH}" '
                     f'stroke="{GRID}" stroke-width="0.5"/>')
    for r in range(ROWS + 1):
        y = r * CELL
        lines.append(f'<line x1="0" y1="{y}" x2="{GW}" y2="{y}" '
                     f'stroke="{GRID}" stroke-width="0.5"/>')
    # HUD separator
    lines.append(f'<rect x="0" y="{GH}" width="{GW}" height="{UI_H}" fill="#060c18"/>')
    lines.append(f'<line x1="0" y1="{GH}" x2="{GW}" y2="{GH}" '
                 f'stroke="#0c2040" stroke-width="1"/>')
    return "\n".join(lines)


def gen_path_layer():
    parts = []
    # Highlighted path cells
    for col, row in PATH:
        x, y = col * CELL, row * CELL
        parts.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                     f'fill="{PATH_FILL}"/>')

    pd = path_d()
    # Glow halo behind the path
    parts.append(f'<path d="{pd}" stroke="#0838a0" stroke-width="{CELL - 2}" '
                 f'fill="none" stroke-linecap="square" filter="url(#gpath)" opacity="0.35"/>')
    # Core path line (pulsing)
    parts.append(
        f'<path d="{pd}" stroke="#2055e0" stroke-width="2" '
        f'fill="none" stroke-linecap="round" stroke-linejoin="round">'
        f'{anim("stroke-opacity","0.3;0.85;0.3","3.5")}'
        f'</path>'
    )

    # ── Spawn marker (left edge) ──────────────────────────────────────────
    sx, sy = cxy(*PATH[0])
    parts.append(
        f'<circle cx="{sx}" cy="{sy}" r="10" fill="none" '
        f'stroke="#ff4444" stroke-width="1.5">'
        f'{anim("r","8;14;8","2")}'
        f'{anim("stroke-opacity","1;0;1","2")}'
        f'</circle>'
    )
    parts.append(
        f'<text x="{sx}" y="{sy - 16}" text-anchor="middle" '
        f'font-family="monospace" font-size="7" fill="#ff4444" '
        f'filter="url(#ge)">SPAWN</text>'
    )

    # ── Base marker (right edge) ──────────────────────────────────────────
    ex, ey = cxy(*PATH[-1])
    parts.append(
        f'<rect x="{ex - 11}" y="{ey - 11}" width="22" height="22" rx="2" '
        f'fill="#001a0d" stroke="#00ffaa" stroke-width="1.5">'
        f'{anim("stroke-opacity","0.4;1;0.4","1.8")}'
        f'</rect>'
    )
    # Shield icon inside base box
    parts.append(
        f'<text x="{ex}" y="{ey + 4}" text-anchor="middle" '
        f'font-family="monospace" font-size="10" fill="#00ffaa" '
        f'filter="url(#ge)">⬡</text>'
    )
    parts.append(
        f'<text x="{ex}" y="{ey + 18}" text-anchor="middle" '
        f'font-family="monospace" font-size="7" fill="#00cc88">BASE</text>'
    )

    return "\n".join(parts)


def gen_towers():
    parts = []
    for i, (col, row, kind) in enumerate(TOWERS):
        cx, cy = cxy(col, row)
        neon, dark, fid = TCOL[kind]
        css = {"laser": "tl", "rocket": "tr", "plasma": "tp", "mortar": "tm"}[kind]
        s = 6  # shape half-size

        # Base plate
        parts.append(
            f'<rect x="{cx - 9}" y="{cy - 9}" width="18" height="18" rx="2" '
            f'fill="{dark}" stroke="{neon}" stroke-width="0.5" opacity="0.9"/>'
        )

        # Tower shape
        if kind == "laser":
            pts = f"{cx},{cy - s} {cx + s},{cy} {cx},{cy + s} {cx - s},{cy}"
            parts.append(
                f'<polygon points="{pts}" fill="{neon}" class="{css}" '
                f'filter="url(#{fid})"/>'
            )
        elif kind == "rocket":
            pts = f"{cx},{cy - s} {cx + s},{cy + s - 2} {cx - s},{cy + s - 2}"
            parts.append(
                f'<polygon points="{pts}" fill="{neon}" class="{css}" '
                f'filter="url(#{fid})"/>'
            )
        elif kind == "plasma":
            hex_pts = " ".join(
                f"{cx + int(s * math.cos(math.radians(60 * i_)))},{cy + int(s * math.sin(math.radians(60 * i_)))}"
                for i_ in range(6)
            )
            parts.append(
                f'<polygon points="{hex_pts}" fill="{neon}" class="{css}" '
                f'filter="url(#{fid})"/>'
            )
        else:  # mortar = circle + ring
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{s}" fill="{neon}" '
                f'class="{css}" filter="url(#{fid})"/>'
            )
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{s + 3}" fill="none" '
                f'stroke="{neon}" stroke-width="1" opacity="0.4">'
                f'{anim("r", f"{s};{s + 5};{s}", "2.5")}'
                f'{anim("opacity", "0.4;0;0.4", "2.5")}'
                f'</circle>'
            )

    return "\n".join(parts)


def gen_attacks():
    """Animated beams / impacts for each tower."""
    parts = []
    for i, (col, row, kind) in enumerate(TOWERS):
        tx, ty = cxy(col, row)
        neon, dark, fid = TCOL[kind]
        np_ = nearest_path_pt(col, row)
        px, py = cxy(*np_)

        # Stagger: each tower has a unique offset and period
        offset = round((i * 0.41) % 2.8, 2)
        period = round(2.0 + (i % 5) * 0.28, 2)
        f0 = round(1 - 0.22 / period, 3)  # keyTimes fractions
        f1 = round(1 - 0.10 / period, 3)
        f2 = round(1 - 0.04 / period, 3)

        if kind == "laser":
            # Solid beam flash
            parts.append(
                f'<line x1="{tx}" y1="{ty}" x2="{px}" y2="{py}" '
                f'stroke="{neon}" stroke-width="2" opacity="0" '
                f'filter="url(#{fid})">'
                f'{anim("opacity", f"0;0;0.9;0.9;0", period, f"{offset}s", f"0;{f0};{f1};{f2};1")}'
                f'{anim("stroke-width", "1;1;3;1;1", period, f"{offset}s", f"0;{f0};{f1};{f2};1")}'
                f'</line>'
            )
            # Impact flash
            parts.append(
                f'<circle cx="{px}" cy="{py}" r="0" fill="{neon}" opacity="0" '
                f'filter="url(#{fid})">'
                f'{anim("r", f"0;0;6;10;0", period, f"{offset}s", f"0;{f0};{f1};{f2};1")}'
                f'{anim("opacity", f"0;0;0.8;0;0", period, f"{offset}s", f"0;{f0};{f1};{f2};1")}'
                f'</circle>'
            )

        elif kind == "rocket":
            # Growing beam (line extends from tower to target)
            parts.append(
                f'<line x1="{tx}" y1="{ty}" x2="{tx}" y2="{ty}" '
                f'stroke="{neon}" stroke-width="2" stroke-dasharray="3,3" '
                f'opacity="0" filter="url(#{fid})">'
                f'{anim("x2", f"{tx};{px};{px}", period, f"{offset}s", f"0;0.18;1")}'
                f'{anim("y2", f"{ty};{py};{py}", period, f"{offset}s", f"0;0.18;1")}'
                f'{anim("opacity", "0;0.8;0.5;0;0", period, f"{offset}s", "0;0.01;0.18;0.28;1")}'
                f'</line>'
            )
            # Projectile dot
            parts.append(
                f'<circle r="3" fill="{neon}" opacity="0" filter="url(#{fid})">'
                f'{anim("opacity", "0;1;1;0;0", period, f"{offset}s", "0;0.01;0.17;0.2;1")}'
                f'<animateMotion dur="{period}s" begin="{offset}s" repeatCount="indefinite">'
                f'<mpath href="#tp{i}"/></animateMotion>'
                f'</circle>'
            )

        elif kind == "plasma":
            # Expanding AOE ring at target
            parts.append(
                f'<circle cx="{px}" cy="{py}" r="0" '
                f'fill="{neon}" fill-opacity="0.12" '
                f'stroke="{neon}" stroke-width="2" opacity="0" '
                f'filter="url(#{fid})">'
                f'{anim("r", "0;0;18;30;20", period, f"{offset}s", "0;0.65;0.75;0.9;1")}'
                f'{anim("opacity", "0;0;0.85;0;0", period, f"{offset}s", "0;0.65;0.75;0.9;1")}'
                f'</circle>'
            )
            # Charge beam
            parts.append(
                f'<line x1="{tx}" y1="{ty}" x2="{px}" y2="{py}" '
                f'stroke="{neon}" stroke-width="3" opacity="0" '
                f'filter="url(#{fid})">'
                f'{anim("opacity", "0;0;0.9;0;0", period, f"{offset}s", "0;0.65;0.75;0.9;1")}'
                f'</line>'
            )

        else:  # mortar: lob + explosion
            # Dashed arc (approximated as straight dashed line)
            parts.append(
                f'<line x1="{tx}" y1="{ty}" x2="{px}" y2="{py}" '
                f'stroke="{neon}" stroke-width="1" stroke-dasharray="4,6" '
                f'opacity="0">'
                f'{anim("opacity", "0;0.5;0", period, f"{offset}s", "0;0.5;1")}'
                f'</line>'
            )
            # Explosion at impact
            for radius, alpha in [(10, "0.9"), (20, "0.5"), (30, "0.2")]:
                parts.append(
                    f'<circle cx="{px}" cy="{py}" r="0" '
                    f'fill="{neon}" fill-opacity="0.15" '
                    f'stroke="{neon}" stroke-width="1" opacity="0" '
                    f'filter="url(#{fid})">'
                    f'{anim("r", f"0;0;{radius}", period, f"{offset}s", "0;0.72;1")}'
                    f'{anim("opacity", f"0;0;{alpha};0", period, f"{offset}s", "0;0.72;0.82;1")}'
                    f'</circle>'
                )

    return "\n".join(parts)


def gen_enemies():
    """All enemy units with animateMotion along #epath."""
    parts = []

    WAVES = [
        # (type, cross_dur_s, count, wave_start_offset_s, shape_r)
        ("basic", 22.0, 4, 0.0,  6),
        ("fast",  14.0, 4, 3.5,  4),
        ("heavy", 32.0, 3, 7.0,  8),
    ]
    STAGGER = 1.1  # seconds between enemies in same wave

    for wtype, dur, count, wstart, r in WAVES:
        fill, glow = ECOL[wtype]

        for n in range(count):
            begin = round(wstart + n * STAGGER, 2)

            # Health bar: starts full (width=14), depletes to 0 over dur seconds
            hbar = (
                f'<rect x="-7" y="-{r + 6}" width="14" height="3" rx="1" '
                f'fill="#1a0000"/>'
                f'<rect x="-7" y="-{r + 6}" height="3" rx="1" fill="#00ff44">'
                f'{anim("width", "14;0", dur, f"{begin}s")}'
                f'</rect>'
            )

            if wtype == "basic":
                body = (
                    f'<circle r="{r}" fill="{fill}" filter="url(#ge)"/>'
                    f'<circle r="{r - 2}" fill="{fill}" opacity="0.6"/>'
                    f'<circle r="2" fill="white" cx="-2" cy="-2" opacity="0.7"/>'
                )
            elif wtype == "fast":
                # Diamond shape (rotated square)
                body = (
                    f'<rect x="-{r}" y="-{r}" width="{r * 2}" height="{r * 2}" '
                    f'rx="1" fill="{fill}" filter="url(#ge)" '
                    f'transform="rotate(45)"/>'
                    f'<circle r="1.5" fill="white" cx="-1.5" cy="-1.5" opacity="0.7"/>'
                )
            else:  # heavy
                body = (
                    f'<circle r="{r + 3}" fill="none" stroke="{glow}" '
                    f'stroke-width="1.5" opacity="0.5">'
                    f'{anim("r", f"{r+2};{r+5};{r+2}", "1.8")}'
                    f'{anim("opacity", "0.3;0.7;0.3", "1.8")}'
                    f'</circle>'
                    f'<circle r="{r}" fill="{fill}" filter="url(#ge)"/>'
                    f'<circle r="{r - 3}" fill="{fill}" opacity="0.5"/>'
                    f'<circle r="2.5" fill="white" cx="-2" cy="-2" opacity="0.6"/>'
                )

            parts.append(
                f'<g>'
                f'{hbar}'
                f'{body}'
                f'<animateMotion dur="{dur}s" begin="{begin}s" '
                f'repeatCount="indefinite" rotate="auto">'
                f'<mpath href="#epath"/>'
                f'</animateMotion>'
                f'</g>'
            )

    return "\n".join(parts)


def gen_ui():
    """Bottom HUD bar."""
    y0 = GH  # top of UI bar
    mid_y = y0 + UI_H // 2

    lines = []

    # Left bracket decoration
    lines.append(
        f'<polyline points="8,{y0 + 8} 8,{y0 + UI_H - 8} {GW - 8},{y0 + UI_H - 8} '
        f'{GW - 8},{y0 + 8} 8,{y0 + 8}" fill="none" stroke="#0c2040" stroke-width="1"/>'
    )

    # ── Title (left) ──────────────────────────────────────────────────────
    lines.append(
        f'<text x="20" y="{mid_y - 8}" font-family="monospace" font-size="10" '
        f'font-weight="bold" fill="#00e5ff" filter="url(#gtxt)">◈ CYBER DEFENSE SIM</text>'
    )
    lines.append(
        f'<text x="20" y="{mid_y + 7}" font-family="monospace" font-size="8" '
        f'fill="#1a5080">personfu.github.io</text>'
    )

    # ── Wave indicator (center-left) ──────────────────────────────────────
    wx = 250
    lines.append(
        f'<text x="{wx}" y="{mid_y - 8}" font-family="monospace" font-size="9" '
        f'fill="#4488cc">WAVE</text>'
    )
    # Animated wave number cycling 1→5
    for wave_n, begin, dur in [
        ("01", "0s",  "11s"),
        ("02", "11s", "11s"),
        ("03", "22s", "11s"),
        ("04", "33s", "11s"),
        ("05", "44s", "11s"),
    ]:
        lines.append(
            f'<text x="{wx + 34}" y="{mid_y - 8}" font-family="monospace" font-size="9" '
            f'fill="#00ccff" opacity="0">'
            f'{anim("opacity", "0;1;1;0", "11", begin, "0;0.02;0.9;1")}'
            f'{wave_n}</text>'
        )

    # Wave progress bar
    bar_w = 80
    lines.append(
        f'<rect x="{wx}" y="{mid_y + 1}" width="{bar_w}" height="6" rx="2" '
        f'fill="#0c1830" stroke="#0c2848" stroke-width="1"/>'
    )
    # Animated bar fill cycling
    lines.append(
        f'<rect x="{wx}" y="{mid_y + 1}" width="0" height="6" rx="2" '
        f'fill="#00ccff" opacity="0.7">'
        f'{anim("width", f"0;{bar_w};0", "55")}'
        f'</rect>'
    )

    # ── Score (center) ────────────────────────────────────────────────────
    sx = 390
    lines.append(
        f'<text x="{sx}" y="{mid_y - 8}" font-family="monospace" font-size="9" '
        f'fill="#4488cc">SCORE</text>'
    )
    # Score ticking up
    for score, begin, dur in [
        ("00000", "0s",   "5s"),
        ("01240", "5s",   "5s"),
        ("04820", "10s",  "5s"),
        ("09600", "15s",  "5s"),
        ("18430", "20s",  "5s"),
        ("32750", "25s",  "5s"),
        ("51280", "30s",  "5s"),
        ("72040", "35s",  "5s"),
        ("96500", "40s",  "15s"),
    ]:
        lines.append(
            f'<text x="{sx + 44}" y="{mid_y - 8}" font-family="monospace" font-size="9" '
            f'fill="#00ff88" opacity="0">'
            f'{anim("opacity", "0;1;1;0", "5", begin, "0;0.05;0.9;1")}'
            f'{score}</text>'
        )

    # ── Base health (right) ───────────────────────────────────────────────
    hx = 530
    lines.append(
        f'<text x="{hx}" y="{mid_y - 8}" font-family="monospace" font-size="9" '
        f'fill="#4488cc">BASE HP</text>'
    )
    # 5 hearts: lose one at t=18s, another at t=36s
    heart_colors = [
        # (phase0_color, phase1_color, phase2_color)
        ("#ff4444", "#ff4444", "#ff4444"),
        ("#ff4444", "#ff4444", "#ff4444"),
        ("#ff4444", "#ff4444", "#ff4444"),
        ("#ff4444", "#333", "#333"),
        ("#ff4444", "#ff4444", "#333"),
    ]
    for hi, (c0, c1, c2) in enumerate(heart_colors):
        hbx = hx + hi * 16
        # heart drawn as ♥
        lines.append(
            f'<text x="{hbx}" y="{mid_y + 7}" font-family="monospace" '
            f'font-size="12" fill="{c0}">'
            f'{anim("fill", f"{c0};{c0};{c1};{c1};{c2};{c2}", "55", "0s", "0;0.32;0.33;0.65;0.66;1")}'
            f'♥</text>'
        )

    # ── Kills counter (right) ─────────────────────────────────────────────
    kx = 740
    lines.append(
        f'<text x="{kx}" y="{mid_y - 8}" font-family="monospace" font-size="9" '
        f'fill="#4488cc">KILLS</text>'
    )
    for kills, begin, dur in [
        ("000", "0s",  "8s"),
        ("007", "8s",  "6s"),
        ("019", "14s", "6s"),
        ("038", "20s", "6s"),
        ("064", "26s", "8s"),
        ("093", "34s", "21s"),
    ]:
        lines.append(
            f'<text x="{kx + 36}" y="{mid_y - 8}" font-family="monospace" font-size="9" '
            f'fill="#ff4444" opacity="0">'
            f'{anim("opacity", "0;1;1;0", dur, begin, "0;0.05;0.9;1")}'
            f'{kills}</text>'
        )

    # ── Cursor blink (right edge) ─────────────────────────────────────────
    lines.append(
        f'<text x="{GW - 20}" y="{mid_y + 7}" font-family="monospace" '
        f'font-size="12" fill="#00e5ff" class="cursor">_</text>'
    )

    return "\n".join(lines)


def gen_title_overlay():
    """Game title and corner HUD brackets."""
    lines = []

    # Top-left bracket
    lines.append(
        f'<polyline points="4,4 4,24 24,24" fill="none" stroke="#00e5ff" '
        f'stroke-width="1.5" opacity="0.5"/>'
    )
    # Top-right bracket
    lines.append(
        f'<polyline points="{GW - 4},4 {GW - 4},24 {GW - 24},24" fill="none" '
        f'stroke="#00e5ff" stroke-width="1.5" opacity="0.5"/>'
    )
    # Bottom-left bracket
    lines.append(
        f'<polyline points="4,{GH - 4} 4,{GH - 24} 24,{GH - 24}" fill="none" '
        f'stroke="#00e5ff" stroke-width="1.5" opacity="0.4"/>'
    )
    # Bottom-right bracket
    lines.append(
        f'<polyline points="{GW - 4},{GH - 4} {GW - 4},{GH - 24} '
        f'{GW - 24},{GH - 24}" fill="none" stroke="#00e5ff" '
        f'stroke-width="1.5" opacity="0.4"/>'
    )

    # Title text (top center)
    lines.append(
        f'<text x="{GW // 2}" y="16" text-anchor="middle" '
        f'font-family="monospace" font-size="9" font-weight="bold" '
        f'fill="#00e5ff" filter="url(#gtxt)" opacity="0.8">'
        f'◈ PERSONFU TOWER DEFENSE ◈</text>'
    )

    # Vignette overlay
    lines.append(
        f'<rect width="{GW}" height="{GH}" fill="url(#vign)" '
        f'pointer-events="none"/>'
    )

    return "\n".join(lines)


def gen_scanlines():
    """Subtle scanline effect (two-pixel rows, very faint)."""
    lines = []
    for y in range(0, GH, 4):
        lines.append(
            f'<line x1="0" y1="{y}" x2="{GW}" y2="{y}" '
            f'stroke="black" stroke-width="1" opacity="0.12"/>'
        )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def generate_svg() -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        gen_defs(),
        gen_style(),
        gen_background(),
        f'<g id="path-layer">{gen_path_layer()}</g>',
        f'<g id="attacks">{gen_attacks()}</g>',
        f'<g id="towers">{gen_towers()}</g>',
        f'<g id="enemies">{gen_enemies()}</g>',
        gen_scanlines(),
        gen_title_overlay(),
        f'<g id="ui">{gen_ui()}</g>',
        '</svg>',
    ]
    return "\n".join(parts)


if __name__ == "__main__":
    out_dir = Path("assets")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "tower-defense.svg"

    svg = generate_svg()
    out_path.write_text(svg, encoding="utf-8")
    print(f"Generated {out_path}  ({len(svg):,} bytes)")
