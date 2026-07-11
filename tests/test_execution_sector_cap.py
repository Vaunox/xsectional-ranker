"""Ex-ante ceil(k/2) sector cap tests."""

from __future__ import annotations

from xsranker.execution.sector_cap import apply_sector_cap


def test_cap_skips_to_next_eligible() -> None:
    ranked = [("A", "IT"), ("B", "IT"), ("C", "IT"), ("D", "Auto"), ("E", "FMCG")]
    # k=4, cap=ceil(4/2)=2 -> C (3rd IT) skipped, D/E fill
    assert apply_sector_cap(ranked, k=4, per_sector_cap=2) == ["A", "B", "D", "E"]


def test_returns_fewer_when_pool_exhausted_under_cap() -> None:
    ranked = [("A", "IT"), ("B", "IT"), ("C", "IT")]
    assert apply_sector_cap(ranked, k=4, per_sector_cap=2) == ["A", "B"]


def test_no_violation_keeps_order() -> None:
    ranked = [("A", "IT"), ("B", "Auto"), ("C", "FMCG")]
    assert apply_sector_cap(ranked, k=3, per_sector_cap=2) == ["A", "B", "C"]
