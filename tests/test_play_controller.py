"""Tests for the Actions controller: parsing, attribution, and state shape."""
import json

import pytest

import games.web.play as play
from games.web.engine import Status, ThreatHunt


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Point the controller's file paths at a temp dir with a minimal README."""
    readme = tmp_path / "README.md"
    readme.write_text("# profile\n")
    monkeypatch.setattr(play, "STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr(play, "README_PATH", readme)
    monkeypatch.setattr(play, "COMMENT_PATH", tmp_path / "last_move.md")
    monkeypatch.setenv("GITHUB_REPOSITORY", "Personfu/Personfu")
    return tmp_path


def test_parse_move_accepts_valid_titles():
    assert play.parse_move("ops: scan B4") == ("scan", "B4", True)
    assert play.parse_move("  ops:  flag  a12 ") == ("flag", "A12", True)
    assert play.parse_move("ops: new") == ("new", "", True)


def test_parse_move_rejects_garbage():
    assert play.parse_move("rm -rf /; echo pwn")[2] is False
    assert play.parse_move("ops: scan")[2] is False        # missing cell
    assert play.parse_move("ops: scan Z9")[2] is False      # column out of range
    assert play.parse_move("")[2] is False


def test_sanitize_actor():
    assert play.sanitize_actor("octocat") == "octocat"
    assert play.sanitize_actor("a-b-1") == "a-b-1"
    assert play.sanitize_actor("-bad") == ""
    assert play.sanitize_actor("inj](http://x)") == ""
    assert play.sanitize_actor("") == ""


def test_apply_move_writes_state_readme_and_comment(sandbox):
    game = play.apply_move("ops: scan C3", actor="octocat")
    assert game.deployed

    state = json.loads((sandbox / "state.json").read_text())
    assert set(state) == {"game", "champions", "last_move"}
    assert "@octocat" in state["last_move"]

    readme = (sandbox / "README.md").read_text()
    assert "THREAT HUNT" in readme and "last op:" in readme
    assert (sandbox / "last_move.md").exists()


def test_legacy_bare_game_state_still_loads(sandbox):
    legacy = ThreatHunt.new(seed=5).to_dict()
    (sandbox / "state.json").write_text(json.dumps(legacy))
    game, champions, last_move = play.load_state()
    assert game.seed == 5
    assert champions == [] and last_move == ""


def test_containment_adds_champion_once(sandbox):
    g = ThreatHunt.new(width=6, height=6, implant_count=6, seed=7)
    g.scan(2, 2)
    # Reveal everything but one clean host, so one move finishes the hunt.
    clean = [
        (x, y)
        for y in range(g.height)
        for x in range(g.width)
        if (x, y) not in g.implants
    ]
    for cell in clean[:-1]:
        g.scan(*cell)
    assert g.status is Status.HUNTING
    play.save_state(g, ["earlier-hunter"], "")

    from games.web.engine import cell_to_label
    final = cell_to_label(*clean[-1])
    play.apply_move(f"ops: scan {final}", actor="octocat")

    state = json.loads((sandbox / "state.json").read_text())
    assert state["game"]["status"] == "CONTAINED"
    assert state["champions"] == ["earlier-hunter", "octocat"]
    readme = (sandbox / "README.md").read_text()
    assert "HUNTERS WHO CONTAINED THE THREAT" in readme
    assert "[@octocat](https://github.com/octocat)" in readme
