from __future__ import annotations

import pytest

from scripts.update_profile_catalogs import (
    SUMMARY_END,
    SUMMARY_START,
    clean_text,
    render_readme_summary,
    render_repositories,
    render_stars,
    replace_summary,
)


def sample_repo(**overrides):
    repo = {
        "name": "example",
        "full_name": "Personfu/example",
        "html_url": "https://github.com/Personfu/example",
        "description": "A public example",
        "language": "Python",
        "fork": False,
        "archived": False,
        "updated_at": "2026-10-04T12:00:00Z",
        "pushed_at": "2026-10-04T12:00:00Z",
        "owner": {"login": "Personfu"},
    }
    repo.update(overrides)
    return repo


def test_clean_text_escapes_public_markdown_and_html():
    value = "<img src=x> [click]\nnext"
    assert clean_text(value) == "&lt;img src&#61;x&gt; &#91;click&#93; next"


def test_clean_text_cannot_restore_a_markdown_link_with_backslashes():
    value = r"\[Trusted GitHub documentation\](https://example.com/phish)"
    cleaned = clean_text(value)
    assert cleaned.startswith("&#92;&#91;Trusted GitHub documentation")
    assert "](" not in cleaned
    assert "https://" not in cleaned


def test_replace_summary_updates_only_marker_block():
    original = f"before\n{SUMMARY_START}\nold\n{SUMMARY_END}\nafter\n"
    replacement = f"{SUMMARY_START}\nnew\n{SUMMARY_END}"
    assert replace_summary(original, replacement) == "before\n" + replacement + "\nafter\n"


def test_replace_summary_requires_markers():
    with pytest.raises(RuntimeError, match="PROFILE-CATALOG"):
        replace_summary("missing", "summary")


def test_rendered_catalogs_separate_authorship_from_bookmarks():
    original = sample_repo()
    fork = sample_repo(
        name="reference",
        full_name="Personfu/reference",
        html_url="https://github.com/Personfu/reference",
        fork=True,
    )
    repos = render_repositories("Personfu", [original, fork])
    assert "**1** original repository" in repos
    assert "**1** fork or reference mirror" in repos
    assert "Presence here does not imply authorship" in repos

    stars = render_stars(
        "Personfu",
        [{"starred_at": "2026-10-04T12:00:00Z", "repo": original}],
    )
    assert "Stars are bookmarks for research and evaluation, not endorsements" in stars
    assert "Personfu/example" in stars


def test_readme_summary_reports_public_counts():
    original = sample_repo()
    fork = sample_repo(fork=True, full_name="Personfu/reference")
    summary = render_readme_summary(
        "Personfu",
        [original, fork],
        [{"starred_at": "2026-10-04T12:00:00Z", "repo": original}],
    )
    assert "1 original projects / 2 public repositories" in summary
    assert "1 publicly retrievable stars" in summary
