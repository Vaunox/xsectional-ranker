"""Per-arm gate evaluation — the imported criteria plus the two new bars.

The imported CPCV/DSR/path-positivity are reached UNEDITED through the adapter and run
on the operator-ruled EXCESS-over-null stream (net minus per-day null median), never the
raw net. The DSR pulls its effective (cluster-adjusted) trial count from the ledger —
never a literal — which is what the re-added literal-N guard binds against
(``tests/test_gate_literal_n_guard.py``). ``beat_random_percentile`` is called
module-qualified (late-bound) so the machinery-removal falsification can stub it and
watch this evaluation go red.

The **absolute-net bar** (added 2026-07-12) is the second binding criterion computed
here: the arm's median ABSOLUTE net return (the raw net stream, per bound) must clear
``thresholds.absolute_net_min``. Beat-random is necessary but not sufficient — the
retired gap-reversal ranker beat a cost-bled null on the excess stream yet lost money net
of cost; this bar refuses that World-B pass. It is a plain per-bound binding flag, so it
rides the cost corridor exactly like the excess-stream criteria.

PBO is a CROSS-arm criterion (it needs the whole config matrix) and lives in
``program.py``; this module reports the per-arm criteria and the per-arm verdict.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime

import numpy as np
from scipy import stats

from xsranker.gate import benchmark as _benchmark  # late-bound (machinery-removal)
from xsranker.gate.benchmark import BeatRandomResult
from xsranker.gate.config import GateThresholds
from xsranker.gate.diagnostics import expectancy, profit_factor
from xsranker.gate.verdict import ArmVerdict, classify_arm
from xsranker.harness.adapter import HarnessAdapter, TrialLedger

#: Minimums below which the arm is INSUFFICIENT rather than decided.
_MIN_OBS = 2
_MIN_FINITE_PATHS = 2


@dataclass(frozen=True, slots=True)
class ArmGateReport:
    """Every computed criterion for one arm under one cost bound, plus the verdict."""

    # -- the one new benchmark --
    beat_random: BeatRandomResult
    # -- DSR + its inputs (exposed so the literal-N guard can reconstruct it) --
    observed_sharpe: float
    n_obs: int
    skew: float
    kurtosis: float
    effective_trials: float
    trial_sharpe_std: float
    dsr: float
    # -- CPCV (on the excess stream) --
    cpcv_median: float
    cpcv_positive_fraction: float
    cpcv_tenth: float
    cpcv_n_finite_paths: int
    # -- absolute-economics bar (the raw net stream, NOT the excess) --
    absolute_net_median: float
    # -- logged diagnostics (never gates) --
    profit_factor: float
    expectancy: float
    # -- per-criterion pass flags (PBO is program-level, folded in there) --
    beat_passed: bool
    dsr_passed: bool
    cpcv_median_passed: bool
    positive_fraction_passed: bool
    absolute_net_passed: bool
    all_binding_passed: bool
    any_near_threshold: bool
    insufficient: bool
    verdict: ArmVerdict


def evaluate_arm(
    signal_by_day: Mapping[date, float],
    null_by_day: Mapping[date, Sequence[float]],
    entry_times: Sequence[datetime],
    exit_times: Sequence[datetime],
    *,
    ledger: TrialLedger,
    adapter: HarnessAdapter,
    thresholds: GateThresholds,
    cpcv_groups: int,
    cpcv_k: int,
    periods_per_year: float,
) -> ArmGateReport:
    """Evaluate one arm under one cost bound (its per-day net stream).

    Raises:
        ValueError: if ``entry_times`` / ``exit_times`` do not align with the surviving
            days, or the null slice is empty/ragged (surfaced by the benchmark).
    """
    days = sorted(signal_by_day)
    if not (len(entry_times) == len(exit_times) == len(days)):
        raise ValueError(
            f"entry/exit times ({len(entry_times)}/{len(exit_times)}) must align with "
            f"the {len(days)} surviving days"
        )

    # One new criterion + the operator-ruled excess stream it produces (Ruling 1).
    beat = _benchmark.beat_random_percentile(
        signal_by_day, null_by_day, threshold=thresholds.null_percentile
    )
    excess_seq = beat.excess_stream  # tuple[float, ...] — a Sequence for the adapter
    excess_arr = np.asarray(excess_seq, dtype=np.float64)
    net_seq = [signal_by_day[d] for d in days]

    # DSR on the EXCESS stream, deflated by the ledger's effective-N (never a literal).
    observed_sharpe = float(adapter.per_period_sharpe(excess_seq))
    n_obs = int(excess_arr.size)
    skew = float(stats.skew(excess_arr))
    kurtosis = float(stats.kurtosis(excess_arr, fisher=False))  # non-excess (normal == 3)
    effective_trials = float(ledger.effective_trials())
    trial_sharpe_std = float(ledger.trial_sharpe_std())
    dsr = float(
        adapter.deflated_sharpe_ratio(
            observed_sharpe,
            n_obs,
            skew,
            kurtosis,
            effective_trials=effective_trials,
            trial_sharpe_std=trial_sharpe_std,
        )
    )

    # CPCV on the EXCESS stream (median + path-positivity + 10th percentile).
    cpcv = adapter.combinatorial_purged_cv(
        excess_seq,
        entry_times,
        exit_times,
        n_groups=cpcv_groups,
        k_test_groups=cpcv_k,
        periods_per_year=periods_per_year,
    ).summary

    # The absolute-economics bar runs on the RAW net stream (not the excess): the arm must
    # make money net of cost, not merely beat a cost-bled null. Median for robustness.
    absolute_net_median = float(np.median(net_seq))

    # Logged diagnostics — on the raw NET stream, never gates (Ruling 2).
    pf = profit_factor(net_seq)
    exp = expectancy(net_seq)

    # Per-criterion pass flags (PBO folded in at program level).
    beat_passed = beat.passed
    dsr_passed = dsr >= thresholds.dsr_min
    cpcv_median_passed = cpcv.median_path_sharpe > thresholds.cpcv_median_min
    positive_fraction_passed = cpcv.positive_fraction > thresholds.positive_fraction_min
    absolute_net_passed = absolute_net_median > thresholds.absolute_net_min
    all_binding_passed = (
        beat_passed
        and dsr_passed
        and cpcv_median_passed
        and positive_fraction_passed
        and absolute_net_passed
    )

    insufficient = (
        n_obs < _MIN_OBS
        or cpcv.n_finite_paths < _MIN_FINITE_PATHS
        or not np.isfinite(observed_sharpe)
        or not np.isfinite(dsr)
        or not np.isfinite(absolute_net_median)
    )

    any_near_threshold = (
        abs(beat.beat_percentile - thresholds.null_percentile) <= thresholds.near_margin_percentile
        or abs(dsr - thresholds.dsr_min) <= thresholds.near_margin_prob
        or abs(cpcv.median_path_sharpe - thresholds.cpcv_median_min)
        <= thresholds.near_margin_sharpe
        or abs(cpcv.positive_fraction - thresholds.positive_fraction_min)
        <= thresholds.near_margin_prob
        or abs(absolute_net_median - thresholds.absolute_net_min) <= thresholds.near_margin_net
    )

    verdict = classify_arm(
        all_binding_passed=all_binding_passed,
        any_near_threshold=any_near_threshold,
        insufficient=insufficient,
    )

    return ArmGateReport(
        beat_random=beat,
        observed_sharpe=observed_sharpe,
        n_obs=n_obs,
        skew=skew,
        kurtosis=kurtosis,
        effective_trials=effective_trials,
        trial_sharpe_std=trial_sharpe_std,
        dsr=dsr,
        cpcv_median=cpcv.median_path_sharpe,
        cpcv_positive_fraction=cpcv.positive_fraction,
        cpcv_tenth=cpcv.tenth_percentile,
        cpcv_n_finite_paths=cpcv.n_finite_paths,
        absolute_net_median=absolute_net_median,
        profit_factor=pf,
        expectancy=exp,
        beat_passed=beat_passed,
        dsr_passed=dsr_passed,
        cpcv_median_passed=cpcv_median_passed,
        positive_fraction_passed=positive_fraction_passed,
        absolute_net_passed=absolute_net_passed,
        all_binding_passed=all_binding_passed,
        any_near_threshold=any_near_threshold,
        insufficient=insufficient,
        verdict=verdict,
    )
