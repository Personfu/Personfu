#!/usr/bin/env python3
"""Repository health checks for the PersonFu profile repo.

This script is intentionally dependency-free. It is safe to run in GitHub Actions,
locally, or from a clean Python install.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
MANIFEST = ROOT / "ops" / "repo_manifest.yml"

BLOCKED_ROOT_PATTERNS = (
    "ROADMAP",
    "GROWTH",
    "OPERATING_PLAN",
    "STATUS",
    "DRAFT",
)

REQUIRED_README_PATTERNS = {
    "fllc.net": r"https://fllc\.net",
    "CyberWorld": r"CyberWorld",
    "NASA ASCEND": r"NASA\s+ASCEND",
    "GitHub stats": r"GitHub\s+Stats",
}

SENSITIVE_PATTERNS = {
    "private key": r"-----BEGIN (RSA |OPENSSH |EC |DSA |PGP )?PRIVATE KEY-----",
    "github token": r"gh[pousr]_[A-Za-z0-9_]{20,}",
    "generic secret assignment": r"(?i)(api[_-]?key|secret|token|password)\s*=\s*['\"][^'\"]{12,}['\"]",
}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def ok(message: str) -> None:
    print(f"[OK] {message}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(ROOT)}")


def check_readme() -> None:
    text = read_text(README)
    for label, pattern in REQUIRED_README_PATTERNS.items():
        if not re.search(pattern, text, flags=re.IGNORECASE):
            fail(f"README missing expected profile signal: {label}")
    ok("README profile signals present")


def check_manifest() -> None:
    text = read_text(MANIFEST)
    for required in ("public GitHub profile", "quality_gate", "public_safety"):
        if required not in text:
            fail(f"operations manifest missing: {required}")
    ok("operations manifest present")


def check_root_sprawl() -> None:
    offenders: list[str] = []
    for item in ROOT.iterdir():
        if not item.is_file():
            continue
        name = item.name.upper()
        if item.name == "README.md":
            continue
        if any(pattern in name for pattern in BLOCKED_ROOT_PATTERNS):
            offenders.append(item.name)
    if offenders:
        fail("root planning/sprawl files should move to docs or be deleted: " + ", ".join(sorted(offenders)))
    ok("root directory is clean of planning-file sprawl")


def check_sensitive_strings() -> None:
    findings: list[str] = []
    skip_dirs = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__"}
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for filename in files:
            path = Path(base) / filename
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".mp4", ".zip"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            rel = path.relative_to(ROOT)
            for label, pattern in SENSITIVE_PATTERNS.items():
                if re.search(pattern, text):
                    findings.append(f"{rel}: {label}")
    if findings:
        fail("possible sensitive content found: " + "; ".join(findings[:10]))
    ok("no obvious secrets detected")


def main() -> int:
    check_readme()
    check_manifest()
    check_root_sprawl()
    check_sensitive_strings()
    print("repository health checks complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
