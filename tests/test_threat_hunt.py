"""Tests for the browser-playable Threat Hunt engine."""
import pytest

from games.web.engine import (
    Status,
    ThreatHunt,
    cell_to_label,
    label_to_cell,
)


def fresh(seed: int = 7) -> ThreatHunt:
    return ThreatHunt.new(width=6, height=6, implant_count=6, seed=seed)


def test_label_roundtrip():
    assert label_to_cell("A1") == (0, 0)
    assert label_to_cell("B4") == (1, 3)
    assert cell_to_label(1, 3) == "B4"


def test_bad_label_rejected():
    with pytest.raises(ValueError):
        label_to_cell("ZZ")


def test_first_scan_is_safe_and_deploys():
    g = fresh()
    g.scan(*label_to_cell("C3"))
    assert g.deployed
    assert label_to_cell("C3") not in g.implants
    assert g.status in (Status.HUNTING, Status.CONTAINED)
    assert len(g.implants) == 6


def test_scanning_an_implant_breaches():
    g = fresh()
    g.scan(2, 2)  # deploy
    implant = next(iter(g.implants))
    g.scan(*implant)
    assert g.status is Status.BREACHED


def test_clearing_all_clean_hosts_contains():
    g = fresh()
    g.scan(2, 2)
    for y in range(g.height):
        for x in range(g.width):
            if (x, y) not in g.implants:
                g.scan(x, y)
    assert g.status is Status.CONTAINED


def test_flag_toggles_and_counts():
    g = fresh()
    g.scan(2, 2)
    target = next(iter(g.implants))  # an unscanned cell
    g.flag(*target)
    assert target in g.flagged
    assert g.implants_remaining == 5
    g.flag(*target)
    assert target not in g.flagged
    assert g.implants_remaining == 6


def test_flagged_host_is_not_scanned():
    g = fresh()
    g.scan(2, 2)
    target = next(
        (x, y)
        for y in range(g.height)
        for x in range(g.width)
        if (x, y) not in g.scanned and (x, y) not in g.implants
    )
    g.flag(*target)
    g.scan(*target)
    assert target not in g.scanned


def test_serialization_roundtrip_preserves_state():
    g = fresh()
    g.scan(2, 2)
    g.flag(0, 5)
    restored = ThreatHunt.from_dict(g.to_dict())
    assert restored.to_dict() == g.to_dict()
    assert restored.implants == g.implants
    assert restored.status is g.status


def test_no_moves_after_game_over():
    g = fresh()
    g.scan(2, 2)
    implant = next(iter(g.implants))
    g.scan(*implant)  # breach
    before = g.to_dict()
    g.scan(0, 0)
    g.flag(0, 0)
    assert g.to_dict() == before
