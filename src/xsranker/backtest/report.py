"""Program report — charge the ledger, gate each arm at both cost bounds, corridor it.

Order matters (Inviolable Rule 4): every arm's stream is charged to the effective-N
ledger FIRST, so the DSR each arm computes is deflated by the honest cross-arm effective
count — never a raw 6. The charged stream is the arm's pessimistic **excess-over-null**
stream (the decision-relevant selection alpha at the binding bound); both bounds' DSRs
then read the same ledger. PBO is the cross-arm CSCV over those same excess streams.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, time

from xsranker.backtest.harness import ArmRun, DayStreams
from xsranker.gate.arm import ArmGateReport, evaluate_arm
from xsranker.gate.benchmark import excess_over_null_median
from xsranker.gate.config import GateThresholds
from xsranker.gate.program import ProgramPBOReport, program_pbo
from xsranker.gate.verdict import ArmVerdict, CorridorOutcome, classify_arm, corridor_outcome
from xsranker.harness.adapter import HarnessAdapter, TrialLedger
from xsranker.ledger.persistence import LedgerManifest, verify_ledger_integrity


@dataclass(frozen=True, slots=True)
class ArmReport:
    """One arm: the gate report at each cost bound, the corridor outcome, the verdict."""

    arm_id: str
    optimistic: ArmGateReport
    pessimistic: ArmGateReport
    corridor: CorridorOutcome
    verdict: ArmVerdict  # the corridor-aware STOP-and-flag verdict


@dataclass(frozen=True, slots=True)
class ProgramReport:
    """The whole smoke run: per-arm reports + the cross-arm PBO + effective-N."""

    arms: tuple[ArmReport, ...]
    pbo: ProgramPBOReport
    raw_arm_count: int
    effective_trials: float


def _entry_exit_times(days: list[date]) -> tuple[list[datetime], list[datetime]]:
    """Per surviving day, (entry instant, session close) for CPCV purging."""
    entry = [datetime.combine(d, time(9, 45)) for d in days]
    exit_ = [datetime.combine(d, time(15, 30)) for d in days]
    return entry, exit_


def _evaluate_bound(
    stream: DayStreams,
    *,
    ledger: TrialLedger,
    adapter: HarnessAdapter,
    thresholds: GateThresholds,
    cpcv_groups: int,
    cpcv_k: int,
    periods_per_year: float,
) -> ArmGateReport:
    days = sorted(stream.signal_by_day)
    entry, exit_ = _entry_exit_times(days)
    return evaluate_arm(
        stream.signal_by_day,
        stream.null_by_day,
        entry,
        exit_,
        ledger=ledger,
        adapter=adapter,
        thresholds=thresholds,
        cpcv_groups=cpcv_groups,
        cpcv_k=cpcv_k,
        periods_per_year=periods_per_year,
    )


def run_program(
    arm_runs: Mapping[str, ArmRun],
    *,
    ledger: TrialLedger,
    adapter: HarnessAdapter,
    thresholds: GateThresholds,
    cpcv_groups: int,
    cpcv_k: int,
    periods_per_year: float,
    pbo_splits: int,
    manifest: LedgerManifest | None = None,
) -> ProgramReport:
    """Charge all arms, gate each at both bounds, corridor, and run the cross-arm PBO.

    If ``manifest`` is given, the ledger is verified FAIL-CLOSED first (R2, Rule 4): any
    required prior-candidate stream that is missing/empty raises ``LedgerIntegrityError``
    before a single DSR is computed — never a silently-undercounted effective-N.

    Raises:
        LedgerIntegrityError: if ``manifest`` is given and a required prior stream is absent.
    """
    # 0. FAIL CLOSED before anything else: prior candidates' streams must be durably present.
    if manifest is not None:
        verify_ledger_integrity(ledger, manifest)

    # 1. charge every arm's pessimistic excess stream to the ledger (before any DSR).
    excess_by_arm: dict[str, list[float]] = {}
    for arm_id, ar in arm_runs.items():
        excess = excess_over_null_median(ar.pessimistic.signal_by_day, ar.pessimistic.null_by_day)
        excess_by_arm[arm_id] = excess
        ledger.log_trial(strategy=arm_id, params={}, returns=excess)

    # 2. cross-arm PBO over the common surviving days (aligned excess matrix).
    common = sorted(
        set.intersection(*(set(ar.pessimistic.signal_by_day) for ar in arm_runs.values()))
    )
    pbo_streams = {
        arm_id: [
            ar.pessimistic.signal_by_day[d] - _median(ar.pessimistic.null_by_day[d]) for d in common
        ]
        for arm_id, ar in arm_runs.items()
    }
    pbo_entry, pbo_exit = _entry_exit_times(common)
    pbo = program_pbo(
        pbo_streams,
        pbo_entry,
        pbo_exit,
        adapter=adapter,
        pbo_max=thresholds.pbo_max,
        n_splits=pbo_splits,
    )

    # 3. gate each arm at both bounds; corridor + verdict.
    reports: list[ArmReport] = []
    for arm_id, ar in arm_runs.items():
        opt = _evaluate_bound(
            ar.optimistic,
            ledger=ledger,
            adapter=adapter,
            thresholds=thresholds,
            cpcv_groups=cpcv_groups,
            cpcv_k=cpcv_k,
            periods_per_year=periods_per_year,
        )
        pess = _evaluate_bound(
            ar.pessimistic,
            ledger=ledger,
            adapter=adapter,
            thresholds=thresholds,
            cpcv_groups=cpcv_groups,
            cpcv_k=cpcv_k,
            periods_per_year=periods_per_year,
        )
        pass_opt = opt.all_binding_passed and pbo.passed
        pass_pess = pess.all_binding_passed and pbo.passed
        corridor = corridor_outcome(passed_optimistic=pass_opt, passed_pessimistic=pass_pess)
        verdict = classify_arm(
            all_binding_passed=pass_pess,
            any_near_threshold=opt.any_near_threshold or pess.any_near_threshold,
            insufficient=opt.insufficient or pess.insufficient,
        )
        reports.append(ArmReport(arm_id, opt, pess, corridor, verdict))

    return ProgramReport(
        arms=tuple(reports),
        pbo=pbo,
        raw_arm_count=len(arm_runs),
        effective_trials=float(ledger.effective_trials()),
    )


def _median(values: tuple[float, ...]) -> float:
    import numpy as np

    return float(np.median(np.asarray(values, dtype=np.float64)))
