# mypy: disable-error-code="no-untyped-def, no-any-return"
"""GATE ZERO — data-integrity validation against the REAL cache.

Local integration check (SKIPS in CI without the cache). Every sub-check is real:
the known-split no-spurious-gap check would go red on an unadjusted series.
"""

from __future__ import annotations

from xsranker.data.integrity import run_gate_zero


def test_gate_zero_all_checks_pass(data_ctx) -> None:
    report = run_gate_zero(data_ctx)
    assert report.all_passed, f"gate-zero failures: {[c.name for c in report.failures()]}"
    names = {c.name for c in report.checks}
    # the load-bearing checks are present and passed
    assert "known_split_no_spurious_gap" in names
    assert "adjusted_identity_phase1" in names
    assert "tradability_masks" in names


def test_known_split_check_has_teeth(data_ctx) -> None:
    """The split check measures a real, sub-split-scale max gap (not a vacuous pass)."""
    report = run_gate_zero(data_ctx)
    split_check = next(c for c in report.checks if c.name == "known_split_no_spurious_gap")
    assert split_check.passed
    # detail records a concrete measured gap far below the split magnitude
    assert "max |adjusted gap|" in split_check.detail
