#!/usr/bin/env python3
"""Build navigable public-repository and starred-repository catalogs.

The profile README should stay concise. This script keeps the exhaustive public
inventory in ``docs/REPOSITORIES.md`` and ``docs/STARRED.md``, then refreshes the
small summary block embedded in ``README.md``.

The script is dependency-free and uses only GitHub's public REST API. A
``GITHUB_TOKEN`` or ``GH_TOKEN`` is optional; invalid credentials fall back to
anonymous public access without printing the token.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DOCS = ROOT / "docs"

SUMMARY_START = "<!-- PROFILE-CATALOG:START -->"
SUMMARY_END = "<!-- PROFILE-CATALOG:END -->"

API_VERSION = "2022-11-28"
PER_PAGE = 100
MAX_PAGES = 20


def _request_json(url: str, accept: str, token: str | None) -> Any:
    headers = {
        "Accept": accept,
        "User-Agent": "Personfu-profile-catalog/1.0",
        "X-GitHub-Api-Version": API_VERSION,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 401 and token:
            # Local environments occasionally expose a stale CLI token. Public
            # catalog generation should still work anonymously.
            return _request_json(url, accept, None)
        raise


def fetch_pages(user: str, resource: str, accept: str) -> list[dict[str, Any]]:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    encoded_user = urllib.parse.quote(user, safe="")
    items: list[dict[str, Any]] = []

    for page in range(1, MAX_PAGES + 1):
        query = urllib.parse.urlencode({"per_page": PER_PAGE, "page": page})
        url = f"https://api.github.com/users/{encoded_user}/{resource}?{query}"
        payload = _request_json(url, accept, token)
        if not isinstance(payload, list):
            raise RuntimeError(f"unexpected GitHub response for {resource}")
        items.extend(item for item in payload if isinstance(item, dict))
        if len(payload) < PER_PAGE:
            return items

    raise RuntimeError(f"{resource} exceeded the {MAX_PAGES}-page safety limit")


def clean_text(value: Any, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    # Public descriptions are mutable, untrusted input. HTML-escape first, then
    # encode Markdown controls and URL punctuation as entities. Entity decoding
    # happens after Markdown parsing, so descriptions render normally without
    # being able to create links, images, raw HTML, or formatting in the catalog.
    text = html.escape(text, quote=False)
    markdown_entities = str.maketrans(
        {
            "\\": "&#92;",
            "[": "&#91;",
            "]": "&#93;",
            "(": "&#40;",
            ")": "&#41;",
            "!": "&#33;",
            "*": "&#42;",
            "_": "&#95;",
            "`": "&#96;",
            "#": "&#35;",
            "|": "&#124;",
            "{": "&#123;",
            "}": "&#125;",
            "+": "&#43;",
            "-": "&#45;",
            ".": "&#46;",
            ":": "&#58;",
            "/": "&#47;",
            "@": "&#64;",
            "~": "&#126;",
            "=": "&#61;",
        }
    )
    return text.translate(markdown_entities)


def safe_repo_url(repo: dict[str, Any]) -> str:
    url = str(repo.get("html_url") or "")
    if url.startswith("https://github.com/"):
        return url
    full_name = urllib.parse.quote(str(repo.get("full_name") or ""), safe="/")
    return f"https://github.com/{full_name}"


def short_date(value: Any) -> str:
    return str(value or "unknown")[:10]


def counted(count: int, singular: str, plural: str | None = None) -> str:
    noun = singular if count == 1 else (plural or singular + "s")
    return f"**{count}** {noun}"


def language_name(repo: dict[str, Any]) -> str:
    return clean_text(repo.get("language") or "Unspecified", limit=50)


def repo_line(repo: dict[str, Any], date_field: str) -> str:
    full_name = clean_text(repo.get("full_name") or repo.get("name"), limit=120)
    description = clean_text(repo.get("description") or "No public description yet.")
    language = language_name(repo)
    date = short_date(repo.get(date_field))
    flags: list[str] = []
    if repo.get("archived"):
        flags.append("archived")
    if repo.get("fork"):
        flags.append("fork")
    suffix = f" · **{', '.join(flags)}**" if flags else ""
    return (
        f"- [{full_name}]({safe_repo_url(repo)}) — {description} "
        f"{language} · {date}{suffix}"
    )


def table_rows(counter: Counter[str], limit: int | None = None) -> list[str]:
    rows = ["| Language | Repositories |", "|---|---:|"]
    for language, count in counter.most_common(limit):
        rows.append(f"| {clean_text(language, limit=50)} | {count} |")
    return rows


def details_by_language(
    repos: Iterable[dict[str, Any]], date_field: str
) -> list[str]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for repo in repos:
        grouped[str(repo.get("language") or "Unspecified")].append(repo)

    sections: list[str] = []
    ordered = sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0].lower()))
    for language, group in ordered:
        group.sort(
            key=lambda repo: (
                str(repo.get(date_field) or ""),
                str(repo.get("full_name") or "").lower(),
            ),
            reverse=True,
        )
        sections.extend(
            [
                "<details>",
                f"<summary><strong>{clean_text(language, 50)}</strong> ({len(group)})</summary>",
                "",
                *[repo_line(repo, date_field) for repo in group],
                "",
                "</details>",
                "",
            ]
        )
    return sections


def render_repositories(user: str, repos: list[dict[str, Any]]) -> str:
    originals = [repo for repo in repos if not repo.get("fork")]
    forks = [repo for repo in repos if repo.get("fork")]
    archived = sum(bool(repo.get("archived")) for repo in repos)
    languages = Counter(str(repo.get("language") or "Unspecified") for repo in repos)

    originals.sort(
        key=lambda repo: (
            str(repo.get("pushed_at") or repo.get("updated_at") or ""),
            str(repo.get("name") or "").lower(),
        ),
        reverse=True,
    )

    lines = [
        "# Public repository map",
        "",
        f"[← Back to the {user} profile](../README.md) · "
        f"[Live repository view](https://github.com/{user}?tab=repositories)",
        "",
        "> This is a generated map of publicly visible repositories. Original work is kept",
        "> separate from forks so maintained projects and research references are not confused.",
        "",
        "## Snapshot",
        "",
        f"- {counted(len(repos), 'public repository', 'public repositories')}",
        f"- {counted(len(originals), 'original repository', 'original repositories')}",
        f"- {counted(len(forks), 'fork or reference mirror', 'forks or reference mirrors')}",
        f"- {counted(archived, 'archived repository', 'archived repositories')}",
        "",
        *table_rows(languages),
        "",
        "## Original repositories",
        "",
        *[repo_line(repo, "updated_at") for repo in originals],
        "",
        "## Forks and reference mirrors",
        "",
        "> A fork may be a reading copy, experiment, contribution base, or compatibility snapshot.",
        "> Presence here does not imply authorship or active maintenance.",
        "",
        *details_by_language(forks, "updated_at"),
    ]
    return "\n".join(lines).rstrip() + "\n"


STAR_LISTS = (
    ("Compromised Repositories Index", "compromised-repositories-index"),
    ("Education", "education"),
    ("FLLC", "fllc"),
    ("Guides", "guides"),
    ("OSINT", "osint"),
    ("Tools", "tools"),
    ("Training", "training"),
)


def render_stars(user: str, starred_items: list[dict[str, Any]]) -> str:
    entries: list[tuple[str, dict[str, Any]]] = []
    for item in starred_items:
        repo = item.get("repo") if isinstance(item.get("repo"), dict) else item
        if isinstance(repo, dict):
            entries.append((str(item.get("starred_at") or ""), repo))

    repos = [repo for _, repo in entries]
    languages = Counter(str(repo.get("language") or "Unspecified") for repo in repos)
    archived = sum(bool(repo.get("archived")) for repo in repos)
    forks = sum(bool(repo.get("fork")) for repo in repos)
    owners = {str(repo.get("owner", {}).get("login") or "") for repo in repos}
    owners.discard("")
    newest = max((starred_at for starred_at, _ in entries), default="unknown")

    for starred_at, repo in entries:
        repo["_starred_at"] = starred_at

    list_links = [
        f"- [{clean_text(name, 80)}](https://github.com/stars/{user}/lists/{slug})"
        for name, slug in STAR_LISTS
    ]

    recent = sorted(
        repos,
        key=lambda repo: str(repo.get("_starred_at") or ""),
        reverse=True,
    )[:20]

    lines = [
        "# Starred research library",
        "",
        f"[← Back to the {user} profile](../README.md) · "
        f"[Browse the live Stars view](https://github.com/{user}?tab=stars) · "
        f"[Open GitHub Lists](https://github.com/stars/{user})",
        "",
        "> Stars are bookmarks for research and evaluation, not endorsements. Some repositories",
        "> are dual-use, archived, experimental, or unreviewed. Validate provenance, licensing,",
        "> safety, and authorization before use.",
        "",
        "> GitHub's signed-in interface may show a higher total. This catalog includes only",
        "> entries returned by the public API; inaccessible, private, or deleted entries are",
        "> neither inferred nor published.",
        "",
        "## Snapshot",
        "",
        f"- {counted(len(repos), 'publicly retrievable starred repository', 'publicly retrievable starred repositories')}",
        f"- {counted(len(owners), 'unique owner')}",
        f"- {counted(len(languages), 'represented primary-language value')}",
        f"- {counted(archived, 'archived repository', 'archived repositories')}",
        f"- {counted(forks, 'fork')}",
        f"- newest public bookmark: **{short_date(newest)}**",
        "",
        *table_rows(languages),
        "",
        "## Curated GitHub Lists",
        "",
        "> Lists overlap by design. Use them for subject-oriented browsing; use the complete",
        "> catalog below when you need every publicly retrievable bookmark.",
        "",
        *list_links,
        "",
        "## Recently starred",
        "",
        *[repo_line(repo, "_starred_at") for repo in recent],
        "",
        "## Complete catalog",
        "",
        "Grouped by primary language so every public bookmark appears exactly once.",
        "",
        *details_by_language(repos, "_starred_at"),
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_readme_summary(
    user: str, repos: list[dict[str, Any]], starred_items: list[dict[str, Any]]
) -> str:
    originals = sum(not bool(repo.get("fork")) for repo in repos)
    stars = sum(
        isinstance(item.get("repo"), dict) or "full_name" in item for item in starred_items
    )
    return "\n".join(
        [
            SUMMARY_START,
            "| Public work | Research library | Other GitHub surfaces |",
            "|---|---|---|",
            f"| [{originals} original projects / {len(repos)} public repositories]"
            f"(docs/REPOSITORIES.md) | [{stars} publicly retrievable stars]"
            f"(docs/STARRED.md) · [live Stars](https://github.com/{user}?tab=stars) | "
            f"[Packages](https://github.com/{user}?tab=packages) · "
            f"[Gists](https://gist.github.com/{user}) |",
            SUMMARY_END,
        ]
    )


def replace_summary(readme: str, summary: str) -> str:
    if SUMMARY_START not in readme or SUMMARY_END not in readme:
        raise RuntimeError("README is missing PROFILE-CATALOG markers")
    start = readme.index(SUMMARY_START)
    end = readme.index(SUMMARY_END) + len(SUMMARY_END)
    return readme[:start] + summary + readme[end:]


def write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", default="Personfu", help="GitHub username")
    args = parser.parse_args(argv)

    repos = fetch_pages(args.user, "repos", "application/vnd.github+json")
    stars = fetch_pages(args.user, "starred", "application/vnd.github.star+json")

    changed = [
        write_if_changed(DOCS / "REPOSITORIES.md", render_repositories(args.user, repos)),
        write_if_changed(DOCS / "STARRED.md", render_stars(args.user, stars)),
    ]

    summary = render_readme_summary(args.user, repos, stars)
    readme = README.read_text(encoding="utf-8")
    changed.append(write_if_changed(README, replace_summary(readme, summary)))

    print(
        f"cataloged {len(repos)} repositories and {len(stars)} stars; "
        f"updated {sum(changed)} file(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
