"""Verdict logic — corridor decision, contradiction detection, classify precedence."""

from __future__ import annotations

import pytest

from xsranker.gate.verdict import (
    ArmVerdict,
    CorridorOutcome,
    classify_arm,
    corridor_outcome,
    requires_operator_ruling,
)


def test_corridor_dead_when_optimistic_fails() -> None:
    assert (
        corridor_outcome(passed_optimistic=False, passed_pessimistic=False) is CorridorOutcome.DEAD
    )


def test_corridor_robust_when_pessimistic_survives() -> None:
    assert (
        corridor_outcome(passed_optimistic=True, passed_pessimistic=True) is CorridorOutcome.ROBUST
    )


def test_corridor_l2_trigger_between_the_bounds() -> None:
    assert (
        corridor_outcome(passed_optimistic=True, passed_pessimistic=False)
        is CorridorOutcome.L2_TRIGGER
    )


def test_corridor_contradiction_on_nonmonotonic_costs() -> None:
    # Pessimistic costs are strictly worse; surviving them while failing optimistic
    # is impossible and must surface as a bug, never a silent verdict.
    with pytest.raises(ValueError):
        corridor_outcome(passed_optimistic=False, passed_pessimistic=True)


def test_classify_pass_and_kill() -> None:
    assert (
        classify_arm(all_binding_passed=True, any_near_threshold=False, insufficient=False)
        is ArmVerdict.PASS_PROVISIONAL
    )
    assert (
        classify_arm(all_binding_passed=False, any_near_threshold=False, insufficient=False)
        is ArmVerdict.KILL
    )


def test_classify_precedence_contradiction_over_insufficient_over_near() -> None:
    # near-threshold outranks a bare pass/kill...
    assert (
        classify_arm(all_binding_passed=True, any_near_threshold=True, insufficient=False)
        is ArmVerdict.NEAR_THRESHOLD
    )
    # ...insufficient outranks near...
    assert (
        classify_arm(all_binding_passed=True, any_near_threshold=True, insufficient=True)
        is ArmVerdict.INSUFFICIENT
    )
    # ...and contradiction outranks everything.
    assert (
        classify_arm(
            all_binding_passed=True,
            any_near_threshold=True,
            insufficient=True,
            contradiction=True,
        )
        is ArmVerdict.CONTRADICTION
    )


def test_only_a_clean_kill_skips_the_operator_ruling() -> None:
    assert not requires_operator_ruling(ArmVerdict.KILL)
    for verdict in (
        ArmVerdict.PASS_PROVISIONAL,
        ArmVerdict.NEAR_THRESHOLD,
        ArmVerdict.INSUFFICIENT,
        ArmVerdict.CONTRADICTION,
    ):
        assert requires_operator_ruling(verdict)
