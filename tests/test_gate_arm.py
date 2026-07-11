# mypy: disable-error-code="no-untyped-def, no-any-return, no-untyped-call"
"""Per-arm gate evaluation — the composition (Ruling 1) and machinery-removal teeth.

The imported CPCV/DSR/path-positivity run on the EXCESS-over-null stream, never the raw
net. The standout: an arm with positive raw P&L that nonetheless loses to the null is
correctly KILLED — proof the gate measures selection alpha, not survivorship-banked P&L.
"""

from __future__ import annotations

import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest

from xsranker.core.config import load_settings
from xsranker.gate import benchmark as gate_benchmark
from xsranker.gate.arm import evaluate_arm
from xsranker.gate.config import GateThresholds
from xsranker.gate.verdict import ArmVerdict
from xsranker.harness.adapter import HarnessAdapter

THRESH = GateThresholds(
    null_percentile=95.0,
    dsr_min=0.95,
    pbo_max=0.20,
    cpcv_median_min=0.0,
    positive_fraction_min=0.5,
    near_margin_percentile=2.0,
    near_margin_prob=0.02,
    near_margin_sharpe=0.02,
)


def _adapter() -> HarnessAdapter:
    return HarnessAdapter(load_settings())


def _fixture(signal_val: float, null_center: float, *, n_days=50, n_draws=120, seed=0):
    """An arm's per-day net stream + null slice + aligned entry/exit times."""
    rng = np.random.default_rng(seed)
    days = [date(2024, 1, 1) + timedelta(days=i) for i in range(n_days)]
    null_by_day = {d: (null_center + rng.normal(0.0, 0.01, n_draws)).tolist() for d in days}
    signal_by_day = {d: float(signal_val + rng.normal(0.0, 0.002)) for d in days}
    ent = [datetime(d.year, d.month, d.day, 9, 15) for d in days]
    exi = [datetime(d.year, d.month, d.day, 15, 30) for d in days]
    return signal_by_day, null_by_day, ent, exi


def _ledger(tmp: str, seed=0):
    rng = np.random.default_rng(seed)
    ledger = _adapter().trial_ledger(Path(tmp))
    for i in range(4):
        ledger.log_trial(
            strategy=f"arm{i}", params={}, returns=rng.normal(0.001 * i, 0.01, 60).tolist()
        )
    return ledger


def _evaluate(fixture, ledger):
    signal_by_day, null_by_day, ent, exi = fixture
    return evaluate_arm(
        signal_by_day,
        null_by_day,
        ent,
        exi,
        ledger=ledger,
        adapter=_adapter(),
        thresholds=THRESH,
        cpcv_groups=5,
        cpcv_k=2,
        periods_per_year=252.0,
    )


def test_a_real_edge_clears_every_binding_criterion() -> None:
    with tempfile.TemporaryDirectory() as d:
        rep = _evaluate(_fixture(0.02, 0.0), _ledger(d))
    assert rep.beat_passed and rep.beat_random.beat_percentile == 100.0
    assert rep.dsr_passed and rep.dsr >= 0.95
    assert rep.cpcv_median > 0.0 and rep.cpcv_positive_fraction == 1.0
    assert rep.all_binding_passed and not rep.insufficient and not rep.any_near_threshold
    assert rep.verdict is ArmVerdict.PASS_PROVISIONAL


def test_no_edge_arm_is_killed() -> None:
    with tempfile.TemporaryDirectory() as d:
        rep = _evaluate(_fixture(-0.02, 0.0), _ledger(d))
    assert not rep.beat_passed and not rep.dsr_passed
    assert not rep.all_binding_passed
    assert rep.verdict is ArmVerdict.KILL


def test_positive_pnl_that_loses_to_the_null_is_killed() -> None:
    """Ruling 1 in one test: raw P&L is positive, but the arm loses to random selection.

    The gate deflates the excess-over-null (net - null median), not the raw net, so a
    strategy whose entire edge is the structural/survivorship subsidy the null also
    enjoys is correctly killed — it never banks that subsidy as alpha.
    """
    with tempfile.TemporaryDirectory() as d:
        rep = _evaluate(_fixture(0.04, 0.05), _ledger(d))
    # raw net P&L is unambiguously positive...
    assert rep.expectancy > 0.0
    assert rep.profit_factor > 1.0
    # ...but the selection alpha (excess over the null) is negative, and the arm dies.
    assert float(np.mean(rep.beat_random.excess_stream)) < 0.0
    assert not rep.beat_passed
    assert not rep.dsr_passed
    assert rep.verdict is ArmVerdict.KILL


def test_evaluate_arm_rejects_misaligned_times() -> None:
    with tempfile.TemporaryDirectory() as d:
        signal, null, ent, exi = _fixture(0.02, 0.0)
        with pytest.raises(ValueError):
            evaluate_arm(
                signal,
                null,
                ent[:-1],
                exi,
                ledger=_ledger(d),
                adapter=_adapter(),
                thresholds=THRESH,
                cpcv_groups=5,
                cpcv_k=2,
                periods_per_year=252.0,
            )


@pytest.mark.falsification
def test_evaluate_arm_goes_red_without_the_benchmark_machinery(monkeypatch) -> None:
    """Machinery-removal on the new criterion: stub the benchmark entry point → the
    evaluation (positive control: the PASS test above) goes red, proving beat-random is
    load-bearing, not a hard-coded pass."""

    class BenchmarkRemovedError(RuntimeError):
        pass

    def _removed(*_a, **_k):
        raise BenchmarkRemovedError("beat-random machinery removed")

    # arm.py calls ``_benchmark.beat_random_percentile`` module-qualified, so patching
    # the module attribute propagates into the evaluation (the vendored late-bind pattern).
    monkeypatch.setattr(gate_benchmark, "beat_random_percentile", _removed)
    with tempfile.TemporaryDirectory() as d, pytest.raises(BenchmarkRemovedError):
        _evaluate(_fixture(0.02, 0.0), _ledger(d))
