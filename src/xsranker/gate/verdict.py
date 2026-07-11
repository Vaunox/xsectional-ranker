"""Verdict logic — the cost-corridor decision and the phased KILL/PASS semantics.

Pure policy over the computed criteria. Phase-1 (survivor cache) semantics: a KILL is
hyper-trustworthy (walk away for the cost of a branch); a PASS is provisional-only —
it earns nothing but the right to the Phase-2 point-in-time crucible, never a
production greenlight. STOP-and-flag: everything except a clean KILL stops for the
operator's ruling before anything is recorded.
"""

from __future__ import annotations

from enum import StrEnum


class CorridorOutcome(StrEnum):
    """The cost-corridor decision for one arm (Deep Dive 02)."""

    DEAD = "dead"  # dies under the friendliest (optimistic) costs → dead
    L2_TRIGGER = "l2_trigger"  # survives optimistic, dies pessimistic → buy Level-2 depth
    ROBUST = "robust"  # survives even the pessimistic bound → robust to cost


def corridor_outcome(*, passed_optimistic: bool, passed_pessimistic: bool) -> CorridorOutcome:
    """Map the two cost-bound pass flags to the corridor decision.

    Pessimistic costs are strictly worse than optimistic, so surviving pessimistic
    while failing optimistic is impossible.

    Raises:
        ValueError: on that impossible (non-monotonic) combination — a contradiction
            the caller must surface, never silently resolve.
    """
    if passed_pessimistic and not passed_optimistic:
        raise ValueError(
            "corridor contradiction: passed pessimistic but failed optimistic "
            "(pessimistic costs are strictly worse — this is a bug, not a verdict)"
        )
    if not passed_optimistic:
        return CorridorOutcome.DEAD
    return CorridorOutcome.ROBUST if passed_pessimistic else CorridorOutcome.L2_TRIGGER


class ArmVerdict(StrEnum):
    """The per-arm verdict; only a clean KILL may skip the operator ruling."""

    KILL = "kill"  # fails a binding criterion clearly — the expected, valuable outcome
    PASS_PROVISIONAL = "pass_provisional"  # noqa: S105 - enum value, not a secret
    """Clears every binding criterion (survivorship-inflated; provisional only)."""
    NEAR_THRESHOLD = "near_threshold"  # a binding criterion sits within the margin band
    INSUFFICIENT = "insufficient"  # not enough scorable data to decide
    CONTRADICTION = "contradiction"  # criteria disagree in an impossible way (a bug tell)


def classify_arm(
    *,
    all_binding_passed: bool,
    any_near_threshold: bool,
    insufficient: bool,
    contradiction: bool = False,
) -> ArmVerdict:
    """Combine the per-criterion flags into a verdict, in strict precedence.

    ``contradiction`` (a bug tell) outranks everything; then ``insufficient`` data;
    then ``near_threshold`` (any binding criterion within its pre-registered band —
    the verdict is untrustworthy at the margin, so the operator rules); only a clear
    result far from every bar yields a plain PASS or KILL.
    """
    if contradiction:
        return ArmVerdict.CONTRADICTION
    if insufficient:
        return ArmVerdict.INSUFFICIENT
    if any_near_threshold:
        return ArmVerdict.NEAR_THRESHOLD
    return ArmVerdict.PASS_PROVISIONAL if all_binding_passed else ArmVerdict.KILL


def requires_operator_ruling(verdict: ArmVerdict) -> bool:
    """STOP-and-flag: anything other than a clean KILL stops for the operator.

    A KILL across the board may be cleared to record directly; every other verdict —
    PASS, near-threshold, insufficient, contradiction — is brought first.
    """
    return verdict is not ArmVerdict.KILL
