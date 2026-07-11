# mypy: disable-error-code="no-untyped-def, no-any-return, no-untyped-call"
"""Program-level gate — PBO wiring and the effective-N charge (Ruling 3).

Effective-N clusters the arms from the actual streams: the tightly-correlated windows
of one signal collapse well below the raw arm count — never a raw 6 (here, never a raw 4).
"""

from __future__ import annotations

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from xsranker.core.config import load_settings
from xsranker.gate.program import charge_arms, program_pbo
from xsranker.harness.adapter import HarnessAdapter


def _adapter() -> HarnessAdapter:
    return HarnessAdapter(load_settings())


def _times(n):
    ent = [datetime(2024, 1, 1, 9, 15) + timedelta(days=i) for i in range(n)]
    exi = [datetime(2024, 1, 1, 15, 30) + timedelta(days=i) for i in range(n)]
    return ent, exi


def test_effective_n_clusters_correlated_windows_below_the_raw_count() -> None:
    with tempfile.TemporaryDirectory() as d:
        ledger = _adapter().trial_ledger(Path(d))
        rng = np.random.default_rng(0)
        base = rng.normal(0.0, 1.0, 250)
        # three near-identical windows of ONE signal (tight correlation) + a distinct arm
        arms = {
            "A_15": (base + 0.01 * rng.normal(0.0, 1.0, 250)).tolist(),
            "A_30": (base + 0.01 * rng.normal(0.0, 1.0, 250)).tolist(),
            "A_45": (base + 0.01 * rng.normal(0.0, 1.0, 250)).tolist(),
            "AZ_30": rng.normal(0.0, 1.0, 250).tolist(),
        }
        charge = charge_arms(ledger, arms)
        assert charge.raw_trials == 4
        # the three windows collapse toward ~1; plus the distinct arm -> ~2, never 4.
        assert 1.0 < charge.effective_trials < 3.0
        assert charge.effective_trials < charge.raw_trials


def test_program_pbo_wires_the_frozen_estimator() -> None:
    n = 48
    rng = np.random.default_rng(1)
    arms = {f"arm_{j}": rng.normal(0.0, 1.0, n).tolist() for j in range(4)}
    ent, exi = _times(n)
    report = program_pbo(arms, ent, exi, adapter=_adapter(), pbo_max=0.20, n_splits=6)
    assert 0.0 <= report.pbo <= 1.0
    assert report.arm_ids == tuple(sorted(arms))
    assert report.passed == (report.pbo < 0.20)


def test_program_pbo_rejects_a_single_arm() -> None:
    import pytest

    ent, exi = _times(10)
    with pytest.raises(ValueError):
        program_pbo({"only": [0.0] * 10}, ent, exi, adapter=_adapter(), pbo_max=0.20, n_splits=4)
