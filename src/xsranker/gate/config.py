"""Typed gate thresholds — the pre-registered bars the verdict is measured against.

``null_percentile`` is one of the FOUR blind values frozen at the Phase 2→3 boundary
(Checkpoint B → Step 2); it lives here and is committed with its a-priori rationale.
The remaining bars are the inherited kill-gate criteria, pre-registered with the
provenance noted per field — they are NOT new policy:

* ``pbo_max = 0.20`` — documented verbatim in the vendored ``pbo.py`` ("criterion 3
  pins PBO < 0.20").
* ``dsr_min = 0.95`` — the DSR is ``P(true Sharpe > the multiple-testing-inflated
  benchmark)``; 0.95 is the 95%-confidence bar, the natural companion to an alpha = 0.05
  per-arm false-positive tolerance (the null-percentile derivation).
* ``cpcv_median_min = 0.0`` / ``positive_fraction_min = 0.5`` — sign criteria (the
  median path positive; a majority of finite paths positive).
* ``absolute_net_min = 0.0`` — the absolute-economics bar (added 2026-07-12, post the
  World-B ruling). Beat-random is NECESSARY BUT NOT SUFFICIENT: an arm can beat a
  cost-bled random book on the excess-over-null stream (real selection alpha) yet still
  LOSE money net of cost. This bar requires the arm's median daily ABSOLUTE net return
  (per cost bound) to clear zero — it must make money net of cost, not merely beat
  random. Zero is the un-arguable break-even line, not outcome-tuned; and because Phase-1
  results are survivorship-inflated UPPER bounds, clearing it is necessary-not-sufficient
  (true OOS net is lower). It is a per-bound binding criterion, so it participates in the
  cost corridor exactly like the others (net-negative optimistic ⇒ DEAD; positive
  optimistic / negative pessimistic ⇒ L2_TRIGGER).

The ``near_margin_*`` bands drive STOP-and-flag: a binding criterion within its band
of the bar is NEAR_THRESHOLD (operator rules), never a silent PASS/KILL at the margin.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from xsranker.core.config import Settings


@dataclass(frozen=True, slots=True)
class GateThresholds:
    """The pre-registered gate bars + the STOP-and-flag near-threshold bands."""

    null_percentile: float  # BLIND value (Step 2); the per-arm beat-random bar
    dsr_min: float
    pbo_max: float
    cpcv_median_min: float
    positive_fraction_min: float
    absolute_net_min: float  # beat-random is necessary; this real-economics bar makes it sufficient
    near_margin_percentile: float
    near_margin_prob: float
    near_margin_sharpe: float
    near_margin_net: float


def _req(m: Mapping[str, Any], key: str) -> Any:
    if key not in m:
        raise ValueError(f"config: missing '{key}' under 'gate'")
    return m[key]


def load_gate_thresholds(settings: Settings) -> GateThresholds:
    """Build :class:`GateThresholds` from the ``gate:`` block of the merged config.

    The block is added at Step 2 (the blind freeze); until then callers construct the
    thresholds directly (Step-1 synthetic tests pass them explicitly).

    Raises:
        ValueError: if the ``gate`` block or any required key is absent.
    """
    raw = settings.raw
    if "gate" not in raw:
        raise ValueError("config: missing 'gate' block (frozen at the Phase 2->3 boundary)")
    g = raw["gate"]
    return GateThresholds(
        null_percentile=float(_req(g, "null_percentile")),
        dsr_min=float(_req(g, "dsr_min")),
        pbo_max=float(_req(g, "pbo_max")),
        cpcv_median_min=float(_req(g, "cpcv_median_min")),
        positive_fraction_min=float(_req(g, "positive_fraction_min")),
        absolute_net_min=float(_req(g, "absolute_net_min")),
        near_margin_percentile=float(_req(g, "near_margin_percentile")),
        near_margin_prob=float(_req(g, "near_margin_prob")),
        near_margin_sharpe=float(_req(g, "near_margin_sharpe")),
        near_margin_net=float(_req(g, "near_margin_net")),
    )


@dataclass(frozen=True, slots=True)
class GateStructuralConfig:
    """CPCV/PBO structural params — pinned PRE-RUN (Step 3a addendum).

    Not among the four blind values, but they shape the gate, so they carry the same
    "fixed before the result" guarantee; none is outcome-derived.
    """

    cpcv_n_groups: int
    cpcv_k_test: int
    pbo_n_splits: int
    periods_per_year: float


def load_gate_structural(settings: Settings) -> GateStructuralConfig:
    """Build the pinned CPCV/PBO structural params from the ``gate:`` block.

    Raises:
        ValueError: if the ``gate`` block or any required key is absent.
    """
    raw = settings.raw
    if "gate" not in raw:
        raise ValueError("config: missing 'gate' block")
    g = raw["gate"]
    return GateStructuralConfig(
        cpcv_n_groups=int(_req(g, "cpcv_n_groups")),
        cpcv_k_test=int(_req(g, "cpcv_k_test")),
        pbo_n_splits=int(_req(g, "pbo_n_splits")),
        periods_per_year=float(_req(g, "periods_per_year")),
    )
