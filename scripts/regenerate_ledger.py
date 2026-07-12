"""Regenerate candidate #1's six trial streams and durably persist them (R2 fix, 1B).

The candidate-#1 smoke run wrote its ledger streams to an ephemeral dir and lost them — a
silent Rule-4 violation (see ``ledger/README.md``). This script is the durable, reproducible
replacement: it reruns the SIX candidate-#1 arms (A / A-Z x {15,30,45}) through the frozen
pipeline and writes each arm's **pessimistic excess-over-null** stream (the stream the ledger
charges) to the committed ``ledger/`` directory, then arms the manifest.

Ledger-composition ruling (operator 2026-07-12): the ledger counts independent LOOKS, not
RE-PRICINGS. Candidate #1 is SIX streams (six selections), each once, under the ORIGINAL
Corwin-Schultz corridor (the cost model in force when they were run). The cost-realism
re-runs (fees-only / fees+5bps / fees+AR) were re-pricings of these same six selections, not
new trials — recorded in each stream's provenance, never as their own rows.

Determinism: a fresh ``default_rng(seed)`` per arm (fixed arm order). Effective-N depends on
the excess streams (signal - null MEDIAN over N draws), which is rng-threading-insensitive at
N=1000 — so the run reproduces regardless of the (lost) ad-hoc threading. The regenerated
effective-N is reported exactly; a MATERIAL divergence from the historically-reported ~5.98 is
an integrity finding (ad-hoc vs reproducible disagreeing) and must be escalated, not smoothed.

Usage::

    python scripts/regenerate_ledger.py --validate   # small-N dry run: diagnostics only
    python scripts/regenerate_ledger.py              # full N=1000: write ledger + manifest

Requires the survivor cache (``XSR_DATA_CACHE_PATH``).
"""

from __future__ import annotations

import argparse
import tempfile
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np

from xsranker.backtest.harness import ArmRun, SymbolDay, build_symbol_days, run_arm
from xsranker.core.config import Settings, load_settings
from xsranker.core.logging import configure_logging
from xsranker.core.types import OHLCV
from xsranker.data.calendar import entry_bar_indices, regular_session
from xsranker.data.config import CircuitConfig
from xsranker.data.factory import DataContext, build_data_context
from xsranker.data.universe.circuit import is_circuit_locked_at
from xsranker.data.universe.eligibility import SecurityStatus, Series, long_eligible, short_eligible
from xsranker.data.universe.sector_map import sector_of
from xsranker.execution.config import CostCorridorConfig, ExecutionConfig, load_layer2_config
from xsranker.gate.benchmark import excess_over_null_median
from xsranker.harness.adapter import HarnessAdapter, TrialLedger
from xsranker.ledger.config import load_ledger_config
from xsranker.ledger.persistence import (
    LedgerManifest,
    arm_trial_id,
    verify_ledger_integrity,
    write_manifest,
)
from xsranker.signals.spec import SignalArm

_CANDIDATE = "candidate-1-gap-reversal"
_CANDIDATE_SHORT = "cand1"
_WINDOWS = (15, 30, 45)
_ARMS = (SignalArm.A, SignalArm.A_Z)
#: Fixed arm order for deterministic regeneration (a fresh rng per arm).
_ARM_ORDER: tuple[tuple[SignalArm, int], ...] = tuple((a, w) for a in _ARMS for w in _WINDOWS)

_COST_REALISM_NOTE = (
    "cost-realism re-runs (fees-only / fees+5bps / fees+AR) were RE-PRICINGS of this same "
    "selection, not independent looks (R1) — recorded here, NOT as separate ledger rows "
    "(operator ruling 2026-07-12; the ledger counts looks, not re-pricings)."
)


@dataclass(frozen=True, slots=True)
class _ArmResult:
    """One regenerated arm: its charged stream + the diagnostics that validate the run."""

    arm: SignalArm
    window: int
    trial_id: str
    excess: list[float]
    draws: int
    surviving_days: int
    trading_days: int
    signal_day_drops: int
    null_draw_day_drops: int
    null_median_pess_bps: float
    short_ban_fires: int


def _session_series(ctx: DataContext) -> dict[str, tuple[OHLCV, str]]:
    """symbol -> (adjusted + regular-session-filtered OHLCV, sector) for every survivor."""
    start = ctx.config.calendar.regular_start_min
    end = ctx.config.calendar.regular_end_min
    out: dict[str, tuple[OHLCV, str]] = {}
    for sym in ctx.universe.symbols:
        series = regular_session(ctx.repository.adjusted(sym), start_min=start, end_min=end)
        out[sym] = (series, sector_of(ctx.sector_map, sym))
    return out


def _circuit_by_day(
    series: OHLCV, entry_minute: int, circuit_cfg: CircuitConfig
) -> dict[date, bool]:
    """Per-day circuit-lock flag at the entry bar (trailing, point-in-time)."""
    dates = series.ist_dates()
    return {
        dates[i]
        .astype("datetime64[D]")
        .astype(date): is_circuit_locked_at(series, int(i), circuit_cfg)
        for i in entry_bar_indices(series, entry_minute=entry_minute)
    }


def _run_one_arm(
    arm: SignalArm,
    window: int,
    series_by_symbol: dict[str, tuple[OHLCV, str]],
    *,
    adapter: HarnessAdapter,
    exec_cfg: ExecutionConfig,
    cost_cfg: CostCorridorConfig,
    atr_period: int,
    entry_start_min: int,
    circuit_cfg: CircuitConfig,
    draws: int,
    seed: int,
) -> _ArmResult:
    """Run one arm through the frozen pipeline; return its charged (pessimistic excess) stream."""
    entry_minute = entry_start_min + window
    cross_section: dict[date, list[SymbolDay]] = defaultdict(list)
    for sym, (series, sector) in series_by_symbol.items():
        status = SecurityStatus(sym, Series.EQ)  # survivors: EQ, non-surveillance, shortable
        sdays = build_symbol_days(
            sym,
            series,
            arm=arm,
            entry_minute=entry_minute,
            atr_period=atr_period,
            sector=sector,
            long_eligible=long_eligible(status),
            short_eligible=short_eligible(status),
            circuit_locked_by_day=_circuit_by_day(series, entry_minute, circuit_cfg),
            adapter=adapter,
        )
        for d, sd in sdays.items():
            cross_section[d].append(sd)

    days = sorted(cross_section)
    run: ArmRun = run_arm(
        days,
        cross_section,
        adapter=adapter,
        exec_cfg=exec_cfg,
        cost_cfg=cost_cfg,
        cost_model=adapter.load_cost_model(),
        draws_per_day=draws,
        rng=np.random.default_rng(seed),
    )
    excess = excess_over_null_median(run.pessimistic.signal_by_day, run.pessimistic.null_by_day)
    all_null_pess = [v for tup in run.pessimistic.null_by_day.values() for v in tup]
    null_med_bps = float(np.median(all_null_pess)) * 1e4 if all_null_pess else float("nan")
    return _ArmResult(
        arm=arm,
        window=window,
        trial_id=arm_trial_id(_CANDIDATE_SHORT, arm.value, window),
        excess=excess,
        draws=draws,
        surviving_days=len(run.pessimistic.signal_by_day),
        trading_days=run.trading_days,
        signal_day_drops=run.signal_day_drops,
        null_draw_day_drops=run.null_draw_day_drops,
        null_median_pess_bps=null_med_bps,
        short_ban_fires=run.short_ban_fires,
    )


def _effective_trials(results: list[_ArmResult]) -> tuple[int, float]:
    """Charge the six excess streams to a scratch ledger; return (raw, effective) counts."""
    with tempfile.TemporaryDirectory() as d:
        led = TrialLedger(Path(d))
        for r in results:
            led.log_trial(strategy=r.trial_id, params={}, returns=r.excess, trial_id=r.trial_id)
        return led.count(), float(led.effective_trials())


def _print_diagnostics(results: list[_ArmResult], raw: int, eff: float) -> None:
    print("\n=== candidate #1 regeneration — diagnostics (validate vs RESEARCH_FINDINGS §8) ===")
    header = (
        f"{'arm':>6} {'win':>4} {'surv_days':>10} {'sig_drop%':>10} "
        f"{'null_drop%':>11} {'null_med_pess_bps':>18} {'short_ban':>10}"
    )
    print(header)
    for r in results:
        sig_drop = 100.0 * r.signal_day_drops / r.trading_days if r.trading_days else 0.0
        denom = r.surviving_days * r.draws  # total null draws attempted on surviving days
        null_drop = 100.0 * r.null_draw_day_drops / denom if denom else 0.0
        print(
            f"{r.arm.value:>6} {r.window:>4} {r.surviving_days:>10} {sig_drop:>9.1f}% "
            f"{null_drop:>10.4f}% {r.null_median_pess_bps:>18.1f} {r.short_ban_fires:>10}"
        )
    print(f"\neffective-N over the 6 excess streams: raw={raw}  effective={eff:.4f}")
    print(
        "(RESEARCH_FINDINGS reported effective-N ~= 5.98; a MATERIAL divergence is an "
        "integrity finding -> escalate, do not smooth.)"
    )


def _persist(results: list[_ArmResult], settings: Settings) -> None:
    """Write the six streams to the durable ledger and arm the manifest (append-only)."""
    cfg = load_ledger_config(settings)
    cfg.dir.mkdir(parents=True, exist_ok=True)
    ledger = TrialLedger(cfg.dir)
    existing = {r.trial_id for r in ledger.trials()}
    for r in results:
        if r.trial_id in existing:
            raise SystemExit(f"refusing to overwrite existing trial {r.trial_id} (append-only)")
        ledger.log_trial(
            strategy=r.trial_id,
            params={
                "candidate": _CANDIDATE,
                "arm": r.arm.value,
                "window_min": r.window,
                "charged_stream": "pessimistic excess-over-null",
                "cost_model": "corwin-schultz corridor (optimistic x1 / pessimistic x3)",
                "seed": settings.seed,
                "surviving_days": r.surviving_days,
                "cost_realism_reruns": _COST_REALISM_NOTE,
            },
            returns=r.excess,
            trial_id=r.trial_id,
        )
    manifest = LedgerManifest(candidates={_CANDIDATE: tuple(r.trial_id for r in results)})
    write_manifest(cfg.manifest_path, manifest)
    verify_ledger_integrity(ledger, manifest)  # fail closed if anything did not land
    print(
        f"\npersisted {len(results)} streams to {cfg.dir} and armed {cfg.manifest_path.name}; "
        "integrity verified."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate candidate #1's six ledger streams.")
    parser.add_argument("--validate", action="store_true", help="small-N dry run: diagnostics only")
    parser.add_argument(
        "--draws", type=int, default=None, help="null draws/day (default: config N)"
    )
    parser.add_argument("--dry-run", action="store_true", help="compute + report but do not write")
    args = parser.parse_args()

    # WARNING level: the frozen pipeline INFO-logs `day_dropped` inside build_random_book's
    # rejection loop, so at N=1000 unfiltered logging renders ~500k lines in the hot path.
    # Suppressing it does not change any stream (print() diagnostics are unaffected).
    configure_logging(level="WARNING", renderer="console")

    settings = load_settings()
    layer2 = load_layer2_config(settings)
    adapter = HarnessAdapter(settings)
    ctx = build_data_context(settings)
    draws = args.draws if args.draws is not None else layer2.null.draws_per_day
    if args.validate and args.draws is None:
        draws = 50  # fast reconstruction check (surviving-days/drops are ~N-independent)

    print(f"loading {len(ctx.universe.symbols)} survivors from cache ...", flush=True)
    series_by_symbol = _session_series(ctx)

    results: list[_ArmResult] = []
    for arm, window in _ARM_ORDER:
        print(f"  running {arm.value} w{window} (draws={draws}) ...", flush=True)
        t0 = time.monotonic()
        results.append(
            _run_one_arm(
                arm,
                window,
                series_by_symbol,
                adapter=adapter,
                exec_cfg=layer2.execution,
                cost_cfg=layer2.cost,
                atr_period=layer2.signal.atr_period,
                entry_start_min=ctx.config.calendar.regular_start_min,
                circuit_cfg=ctx.config.circuit,
                draws=draws,
                seed=settings.seed,
            )
        )
        print(f"    ... {arm.value} w{window} done in {time.monotonic() - t0:.0f}s", flush=True)

    raw, eff = _effective_trials(results)
    _print_diagnostics(results, raw, eff)

    if args.validate or args.dry_run:
        print("\n(validate/dry-run: nothing written.)")
        return
    _persist(results, settings)


if __name__ == "__main__":
    main()
