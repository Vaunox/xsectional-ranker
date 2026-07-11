"""Program-level gate — the CROSS-arm criteria: PBO/CSCV and the effective-N charge.

PBO needs the whole config matrix (one column per arm), so it is a program criterion,
not a per-arm one: a high PBO means the *sweep* is overfit and no arm's PASS is
trustworthy. The effective-N charge is Ruling 3 in action — the 6 signalxwindow arms
are logged to the ledger and their **effective** (cluster-adjusted) count comes from the
actual return streams via the correlation participation ratio, never a raw 6.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np

from xsranker.harness.adapter import HarnessAdapter, TrialLedger


@dataclass(frozen=True, slots=True)
class ProgramPBOReport:
    """The cross-arm PBO estimate and its pass flag."""

    pbo: float
    passed: bool
    arm_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LedgerCharge:
    """The raw vs effective (cluster-adjusted) trial count after charging the arms."""

    raw_trials: int
    effective_trials: float


def program_pbo(
    arm_streams: Mapping[str, Sequence[float]],
    entry_times: Sequence[datetime],
    exit_times: Sequence[datetime],
    *,
    adapter: HarnessAdapter,
    pbo_max: float,
    n_splits: int,
) -> ProgramPBOReport:
    """PBO across arms (each column an arm's excess stream), aligned on common days.

    Raises:
        ValueError: if fewer than two arms, or the streams are ragged.
    """
    ids = sorted(arm_streams)
    if len(ids) < 2:
        raise ValueError("PBO needs at least two arms (a one-column matrix is degenerate)")
    columns = [np.asarray(arm_streams[i], dtype=np.float64) for i in ids]
    lengths = {c.size for c in columns}
    if len(lengths) != 1:
        raise ValueError(f"arm streams must share one length (got {sorted(lengths)})")
    matrix = np.column_stack(columns)
    result = adapter.probability_of_backtest_overfitting(
        matrix, entry_times, exit_times, n_splits=n_splits
    )
    return ProgramPBOReport(pbo=float(result.pbo), passed=result.pbo < pbo_max, arm_ids=tuple(ids))


def charge_arms(
    ledger: TrialLedger,
    arm_streams: Mapping[str, Sequence[float]],
    *,
    params_by_arm: Mapping[str, Mapping[str, Any]] | None = None,
) -> LedgerCharge:
    """Log each arm's return stream to the ledger; return the raw vs effective count.

    This is the honest charge (Ruling 3): every arm is logged, and the DSR later pulls
    ``effective_trials`` from these streams — the three windows of one signal cluster
    tightly, so the effective count lands materially below the raw arm count.
    """
    params = params_by_arm or {}
    for arm_id in sorted(arm_streams):
        ledger.log_trial(
            strategy=arm_id,
            params=dict(params.get(arm_id, {})),
            returns=arm_streams[arm_id],
        )
    return LedgerCharge(
        raw_trials=ledger.count(), effective_trials=float(ledger.effective_trials())
    )
