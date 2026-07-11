# mypy: disable-error-code="no-untyped-def, no-any-return, no-untyped-call"
"""Literal-N guard — behaviorally bound to the real DSR call site (sentinel-spy).

Re-added scoped to ``src/xsranker`` now that Layer 3 gives a real DSR call site (the
Phase-0 version was a brittle, vacuous source scan). Inviolable Rule 4: the DSR is
deflated by the ledger's EFFECTIVE trial count, never a literal. The spy replaces the
ledger's ``effective_trials`` with a sentinel and proves the gate's DSR was computed
from that sentinel — so hard-coding the trial count anywhere would turn this red.
"""

from __future__ import annotations

import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

from xsranker.core.config import load_settings
from xsranker.gate.arm import evaluate_arm
from xsranker.gate.config import GateThresholds
from xsranker.harness.adapter import HarnessAdapter

THRESH = GateThresholds(
    null_percentile=95.0,
    dsr_min=0.95,
    pbo_max=0.20,
    cpcv_median_min=0.0,
    positive_fraction_min=0.5,
    absolute_net_min=0.0,
    near_margin_percentile=2.0,
    near_margin_prob=0.02,
    near_margin_sharpe=0.02,
    near_margin_net=0.0002,
)


def _adapter() -> HarnessAdapter:
    return HarnessAdapter(load_settings())


def _fixture(signal_mean, noise, *, n_days=50, n_draws=120, seed=0):
    rng = np.random.default_rng(seed)
    days = [date(2024, 1, 1) + timedelta(days=i) for i in range(n_days)]
    null_by_day = {d: rng.normal(0.0, 0.01, n_draws).tolist() for d in days}
    signal_by_day = {d: float(signal_mean + rng.normal(0.0, noise)) for d in days}
    ent = [datetime(d.year, d.month, d.day, 9, 15) for d in days]
    exi = [datetime(d.year, d.month, d.day, 15, 30) for d in days]
    return signal_by_day, null_by_day, ent, exi


def _ledger(tmp, seed=0):
    rng = np.random.default_rng(seed)
    ledger = _adapter().trial_ledger(Path(tmp))
    for i in range(4):  # varied streams so trial_sharpe_std > 0 (a real DSR benchmark)
        ledger.log_trial(
            strategy=f"a{i}", params={}, returns=rng.normal(0.001 * i, 0.01, 60).tolist()
        )
    return ledger


def _evaluate(fixture, ledger):
    signal, null, ent, exi = fixture
    return evaluate_arm(
        signal,
        null,
        ent,
        exi,
        ledger=ledger,
        adapter=_adapter(),
        thresholds=THRESH,
        cpcv_groups=5,
        cpcv_k=2,
        periods_per_year=252.0,
    )


def test_dsr_is_computed_from_the_ledger_effective_n_not_a_literal(monkeypatch) -> None:
    """Sentinel-spy: the gate's DSR must be reconstructible from the sentinel N."""
    sentinel = 3.7  # not a plausible hard-coded arm count
    adapter = _adapter()
    with tempfile.TemporaryDirectory() as d:
        ledger = _ledger(d)
        monkeypatch.setattr(ledger, "effective_trials", lambda: sentinel)
        rep = evaluate_arm(
            *_fixture(0.02, 0.002),
            ledger=ledger,
            adapter=adapter,
            thresholds=THRESH,
            cpcv_groups=5,
            cpcv_k=2,
            periods_per_year=252.0,
        )
        # 1) the value flowed from the ledger into the report...
        assert rep.effective_trials == sentinel
        # 2) ...and the DSR was actually computed with it (a hard-coded N would differ).
        expected = adapter.deflated_sharpe_ratio(
            rep.observed_sharpe,
            rep.n_obs,
            rep.skew,
            rep.kurtosis,
            effective_trials=sentinel,
            trial_sharpe_std=rep.trial_sharpe_std,
        )
        assert rep.dsr == expected


def test_dsr_responds_to_the_effective_n(monkeypatch) -> None:
    """More (effective) trials raise the multiple-testing bar, so the DSR must fall."""
    with tempfile.TemporaryDirectory() as d:
        ledger = _ledger(d)
        moderate = _fixture(0.003, 0.008)  # a moderate edge so the DSR is in a sensitive range

        monkeypatch.setattr(ledger, "effective_trials", lambda: 1.0)
        dsr_one = _evaluate(moderate, ledger).dsr
        monkeypatch.setattr(ledger, "effective_trials", lambda: 1.0e6)
        dsr_many = _evaluate(moderate, ledger).dsr

    assert dsr_many < dsr_one  # a literal (constant) N could not produce this response
