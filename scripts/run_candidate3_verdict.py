"""The single BLIND verdict run for candidate #3 (sector-relative intraday reversal).

Authorized 2026-07-12 after (a) the frozen pre-reg (`candidate-3-preregistration`), (b) the
independence screen CLEARING the distinctness gate, and (c) the cost-corridor re-pin
(`cost-corridor-repin`). Two signals x three windows = SIX charged arms (pre-reg SS8):

* **SR**   = morning open->entry return - leave-one-out same-sector-peer mean (raw).
* **SR-Z** = SR / ATR% (magnitude-normalised).

Ranked REVERSAL (long the lowest = sector underperformers, short the highest = outperformers),
through the frozen execution/null machinery under the RE-PINNED live FIXED_SPREAD corridor
(size-aware fees @ Rs10k deployment notional + NSE-impact spread 1/5 bps). Gated against the
CUMULATIVE effective-N ledger: candidate #1's 6 + candidate #2r's 3 + candidate #3's 6 = 15 arms
(the fail-closed guard verifies the 9 prior streams are present). No verdict was seen when any
parameter was pinned. Uses the panel pickle ($XSR_PANEL_PICKLE).
"""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import date
from pathlib import Path

import numpy as np

from xsranker.backtest.harness import ArmRun, SymbolDay, build_symbol_days, run_arm
from xsranker.backtest.report import run_program
from xsranker.backtest.universe_panel import SessionSeries, cached_session_series
from xsranker.core.config import load_settings
from xsranker.core.logging import configure_logging
from xsranker.core.types import OHLCV
from xsranker.data.calendar import entry_bar_indices
from xsranker.data.config import CircuitConfig
from xsranker.data.factory import build_data_context
from xsranker.data.universe.circuit import is_circuit_locked_at
from xsranker.data.universe.eligibility import SecurityStatus, Series, long_eligible, short_eligible
from xsranker.execution.config import Layer2Config, load_layer2_config
from xsranker.features.point_in_time import entry_window_return
from xsranker.gate.benchmark import excess_over_null_median
from xsranker.gate.config import load_gate_structural, load_gate_thresholds
from xsranker.harness.adapter import HarnessAdapter, TrialLedger
from xsranker.ledger.config import load_ledger_config
from xsranker.ledger.persistence import load_manifest
from xsranker.signals.sector_relative import (
    DEFAULT_MIN_PEERS,
    SectorRelativeArm,
    sector_relative_move,
    sector_relative_z,
)
from xsranker.signals.spec import atr_pct_by_day

_WINDOWS = (15, 30, 45)
_REGULAR_START_MIN = 555


def _morning_return(series: OHLCV, entry_minute: int) -> dict[date, float]:
    days, vals = entry_window_return(series, entry_minute=entry_minute)
    return {
        d.astype("datetime64[D]").astype(date): float(v) for d, v in zip(days, vals, strict=True)
    }


def _circuit_by_day(series: OHLCV, entry_minute: int, cfg: CircuitConfig) -> dict[date, bool]:
    dates = series.ist_dates()
    return {
        dates[i].astype("datetime64[D]").astype(date): is_circuit_locked_at(series, int(i), cfg)
        for i in entry_bar_indices(series, entry_minute=entry_minute)
    }


def _signals_by_window(
    series_by_symbol: SessionSeries, entry_minute: int, *, adapter: HarnessAdapter, atr_period: int
) -> dict[SectorRelativeArm, dict[str, dict[date, float]]]:
    """SR and SR-Z per symbol/day for one window (SR is cross-sectional over same-sector peers)."""
    mr: dict[str, dict[date, float]] = {}
    atr: dict[str, dict[date, float]] = {}
    sector: dict[str, str] = {}
    for sym, (series, sec) in series_by_symbol.items():
        sector[sym] = sec
        mr[sym] = _morning_return(series, entry_minute)
        atr[sym] = atr_pct_by_day(series, adapter, atr_period=atr_period)
    sr = sector_relative_move(mr, sector, min_peers=DEFAULT_MIN_PEERS)
    srz = sector_relative_z(sr, atr)
    return {SectorRelativeArm.SR: sr, SectorRelativeArm.SR_Z: srz}


def _arm_run(
    signal_by_symbol: dict[str, dict[date, float]],
    window: int,
    series_by_symbol: SessionSeries,
    *,
    adapter: HarnessAdapter,
    layer2: Layer2Config,
    circuit_cfg: CircuitConfig,
    seed: int,
) -> ArmRun:
    entry_minute = _REGULAR_START_MIN + window
    cross_section: dict[date, list[SymbolDay]] = {}
    for sym, (series, sector) in series_by_symbol.items():
        if sym not in signal_by_symbol:
            continue  # name excluded from SR (its sector has < 3 names)
        status = SecurityStatus(sym, Series.EQ)
        sdays = build_symbol_days(
            sym,
            series,
            signal_override=signal_by_symbol[sym],  # injected cross-sectional SR / SR-Z
            entry_minute=entry_minute,
            atr_period=layer2.signal.atr_period,
            sector=sector,
            long_eligible=long_eligible(status),
            short_eligible=short_eligible(status),
            circuit_locked_by_day=_circuit_by_day(series, entry_minute, circuit_cfg),
            adapter=adapter,
            compute_spread=False,  # live FIXED corridor -> no Corwin-Schultz
        )
        for d, sd in sdays.items():
            cross_section.setdefault(d, []).append(sd)
    days = sorted(cross_section)
    return run_arm(
        days,
        cross_section,
        adapter=adapter,
        exec_cfg=layer2.execution,
        cost_cfg=layer2.cost,  # RE-PINNED FIXED_SPREAD (fees @ Rs10k + 1/5 bps)
        cost_model=adapter.load_cost_model(),
        draws_per_day=layer2.null.draws_per_day,
        rng=np.random.default_rng(seed),
        continuation=False,  # REVERSAL: long the lowest SR, short the highest
    )


def _temp_ledger_with_priors(durable_dir: Path) -> tuple[TrialLedger, Path]:
    """Scratch ledger seeded with the 9 committed prior streams (cand#1 6 + cand#2r 3)."""
    tmp = Path(tempfile.mkdtemp(prefix="cand3_ledger_"))
    for pattern in ("cand1__*.json", "cand2r__*.json"):
        for j in durable_dir.glob(pattern):
            shutil.copy(j, tmp / j.name)
    return TrialLedger(tmp), tmp


def main() -> None:
    configure_logging(level="INFO", renderer="console")
    settings = load_settings()
    adapter = HarnessAdapter(settings)
    layer2 = load_layer2_config(settings)
    thresholds = load_gate_thresholds(settings)
    struct = load_gate_structural(settings)
    ledger_cfg = load_ledger_config(settings)
    ctx = build_data_context(settings)

    print("candidate #3 VERDICT RUN (blind) | loading panel (pickle) ...", flush=True)
    series_by_symbol = cached_session_series(ctx)

    arm_runs: dict[str, ArmRun] = {}
    for w in _WINDOWS:
        signals = _signals_by_window(
            series_by_symbol,
            _REGULAR_START_MIN + w,
            adapter=adapter,
            atr_period=layer2.signal.atr_period,
        )
        for arm, sig in signals.items():
            arm_id = f"{arm.value}__{w}"
            print(f"  running {arm_id} (draws={layer2.null.draws_per_day}) ...", flush=True)
            arm_runs[arm_id] = _arm_run(
                sig,
                w,
                series_by_symbol,
                adapter=adapter,
                layer2=layer2,
                circuit_cfg=ctx.config.circuit,
                seed=settings.seed,
            )

    ledger, tmp_dir = _temp_ledger_with_priors(ledger_cfg.dir)
    manifest = load_manifest(ledger_cfg.manifest_path)  # requires the 9 priors (fail-closed)
    prog = run_program(
        arm_runs,
        ledger=ledger,
        adapter=adapter,
        thresholds=thresholds,
        cpcv_groups=struct.cpcv_n_groups,
        cpcv_k=struct.cpcv_k_test,
        periods_per_year=struct.periods_per_year,
        pbo_splits=struct.pbo_n_splits,
        manifest=manifest,
    )

    # save candidate #3's charged (pessimistic excess-over-null) streams for durable persistence
    # when the operator records the verdict (deterministic trial-ids: cand3__SR/SR-Z__window).
    out_dir = Path(tempfile.gettempdir()) / "cand3_streams"
    out_dir.mkdir(parents=True, exist_ok=True)
    for arm_id, ar in arm_runs.items():
        excess = excess_over_null_median(ar.pessimistic.signal_by_day, ar.pessimistic.null_by_day)
        tid = f"cand3__{arm_id}"
        (out_dir / f"{tid}.json").write_text(
            json.dumps(
                {
                    "trial_id": tid,
                    "strategy": tid,
                    "params": {
                        "candidate": "candidate-3-sector-relative",
                        "arm": arm_id,
                        "direction": "reversal",
                        "charged_stream": "pessimistic excess-over-null",
                        "cost_model": "fixed_spread (fees @ Rs10k deployment + 1/5 bps; NSE impact)",
                        "seed": settings.seed,
                    },
                    "returns": excess,
                }
            ),
            encoding="utf-8",
        )

    print(
        f"\n=== candidate #3 VERDICT ===  cumulative effective-N "
        f"(cand#1 6 + cand#2r 3 + cand#3 6 = 15 raw) = {prog.effective_trials:.4f}  "
        f"|  PBO = {prog.pbo.pbo:.3f}"
    )
    print(
        f"{'arm':>12} {'verdict':>14} {'beat%(o/p)':>12} {'DSR(o/p)':>13} "
        f"{'CPCVmed(o/p)':>15} {'absNet_bps(o/p)':>18} {'corridor':>14}"
    )
    for r in prog.arms:
        o, p = r.optimistic, r.pessimistic
        print(
            f"{r.arm_id:>12} {r.verdict.value:>14} "
            f"{o.beat_random.beat_percentile:>5.0f}/{p.beat_random.beat_percentile:<5.0f} "
            f"{o.dsr:>6.2f}/{p.dsr:<6.2f} "
            f"{o.cpcv_median:>7.2f}/{p.cpcv_median:<7.2f} "
            f"{o.absolute_net_median * 1e4:>8.1f}/{p.absolute_net_median * 1e4:<8.1f} "
            f"{r.corridor.value:>14}"
        )
    print(
        f"\n(candidate #3 streams saved to {out_dir}; durable persistence on record. tmp {tmp_dir}.)"
    )


if __name__ == "__main__":
    main()
