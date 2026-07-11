"""Check-1 port of the predecessor's effective-trial ledger tests (P2.3).

Ported from ``intraday-strategy-lab`` ``tests/unit/test_ledger.py`` at pinned
commit ``0c5c592`` (see ``src/vendored/VENDORED_FROM.md``). The five hand-computed
effective-N / DSR-deflation tests below are **byte-identical** to the source.

OMITTED (documented, not silent): ``test_no_caller_passes_a_literal_trial_count``
— a source-scan guard asserting the predecessor's *business* code never hard-codes
the trial count. It scans ``src/lab/**`` and is not a harness-math test; in this
harness-only Phase 0 there are no DSR business call sites yet. The equivalent
guard, scoped to ``src/xsranker``, is re-added in Phase 2 when the gate acquires
real DSR call sites (docs/PROGRESS.md).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from lab.research.trials.ledger import TrialLedger


def _ledger(tmp_path: Path, name: str = "trials") -> TrialLedger:
    return TrialLedger(tmp_path / name)


def test_effective_trials_collapses_identical_variants(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path)
    base = np.random.default_rng(0).normal(0.0, 0.01, 120).tolist()
    for i in range(10):
        ledger.log_trial("S", {"i": i}, base)  # 10 identical streams
    assert ledger.count() == 10
    assert ledger.effective_trials() == pytest.approx(1.0, abs=0.01)  # ~1 effective


def test_effective_trials_approx_n_for_independent(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path)
    rng = np.random.default_rng(1)
    for i in range(5):
        ledger.log_trial("S", {"i": i}, rng.normal(0.0, 0.01, 400).tolist())
    assert 3.5 < ledger.effective_trials() <= 5.0  # ~5 for independent trials


def test_correlated_cluster_yields_effective_n_below_raw_count(tmp_path: Path) -> None:
    # THE P2.3 acceptance test: a sweep of near-duplicate variants must not count
    # as that many independent trials.
    ledger = _ledger(tmp_path)
    rng = np.random.default_rng(2)
    base_a = rng.normal(0.0, 0.01, 300)
    base_b = rng.normal(0.0, 0.01, 300)
    for i in range(5):
        ledger.log_trial("A", {"i": i}, (base_a + rng.normal(0, 1e-5, 300)).tolist())
    for i in range(5):
        ledger.log_trial("B", {"i": i}, (base_b + rng.normal(0, 1e-5, 300)).tolist())
    assert ledger.count() == 10
    assert ledger.effective_trials() < 3.0  # ~2 clusters, well below the raw 10


def test_ledger_persists_across_instances(tmp_path: Path) -> None:
    directory = tmp_path / "trials"
    TrialLedger(directory).log_trial("S", {"a": 1}, [0.1, 0.2, -0.1])
    # A fresh ledger on the same durable directory sees the trial.
    assert TrialLedger(directory).count() == 1
    assert TrialLedger(directory).trials()[0].strategy == "S"


def test_deflated_sharpe_higher_with_fewer_effective_trials(tmp_path: Path) -> None:
    rng = np.random.default_rng(7)
    few = _ledger(tmp_path, "few")
    many = _ledger(tmp_path, "many")
    for i in range(2):
        few.log_trial("S", {"i": i}, rng.normal(0.0, 0.01, 300).tolist())
    for i in range(60):
        many.log_trial("S", {"i": i}, rng.normal(0.0, 0.01, 300).tolist())
    assert few.deflated_sharpe(0.15, 300, 0.0, 3.0) > many.deflated_sharpe(0.15, 300, 0.0, 3.0)
