"""The single BLIND verdict run for V_resid (authorized 2026-07-12, after the frozen pre-reg).

V_resid = per-day cross-sectional OLS residual of raw V on the morning open->entry return, ranked
CONTINUATION (long the highest residual flow, short the lowest), through the frozen execution/null
machinery under the live FIXED_SPREAD cost corridor. Gated against the CUMULATIVE effective-N
ledger: candidate #1's 6 durably-committed arms + V_resid's 3 window-arms (the fail-closed guard
verifies candidate #1's streams are present). No verdict was seen when any parameter was pinned.

Charges to a TEMP copy of the durable ledger (candidate #1's 6 + V_resid's 3) for the DSR; the
verdict is reported, and V_resid's streams are saved to a scratch dir for durable persistence when
the operator records the verdict. Uses the panel pickle ($XSR_PANEL_PICKLE).
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
from xsranker.signals.volume_delta import VolumeDeltaArm, cross_sectional_residual
from xsranker.signals.volume_delta import signal_value_by_day as vd_signal

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


def _v_resid_by_symbol(
    series_by_symbol: SessionSeries, entry_minute: int
) -> dict[str, dict[date, float]]:
    """Cross-sectionally residualize raw V on the morning return (the frozen V_resid construction)."""
    v: dict[str, dict[date, float]] = {}
    mr: dict[str, dict[date, float]] = {}
    for sym, (series, _sector) in series_by_symbol.items():
        v[sym] = vd_signal(VolumeDeltaArm.V, series, entry_minute=entry_minute)
        mr[sym] = _morning_return(series, entry_minute)
    return cross_sectional_residual(v, mr)


def _arm_run_for_window(
    window: int,
    series_by_symbol: SessionSeries,
    *,
    adapter: HarnessAdapter,
    layer2: Layer2Config,
    circuit_cfg: CircuitConfig,
    seed: int,
) -> ArmRun:
    entry_minute = _REGULAR_START_MIN + window
    v_resid = _v_resid_by_symbol(series_by_symbol, entry_minute)
    cross_section: dict[date, list[SymbolDay]] = {}
    for sym, (series, sector) in series_by_symbol.items():
        if sym not in v_resid:
            continue
        status = SecurityStatus(sym, Series.EQ)
        sdays = build_symbol_days(
            sym,
            series,
            signal_override=v_resid[sym],  # the injected cross-sectional residual
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
        cost_cfg=layer2.cost,  # FIXED_SPREAD (fees + 5/18 bps)
        cost_model=adapter.load_cost_model(),
        draws_per_day=layer2.null.draws_per_day,
        rng=np.random.default_rng(seed),
        continuation=True,  # LONG the highest residual flow, SHORT the lowest
    )


def _temp_ledger_with_candidate1(durable_dir: Path) -> tuple[TrialLedger, Path]:
    """A scratch ledger seeded with candidate #1's 6 committed streams (cumulative charge base)."""
    tmp = Path(tempfile.mkdtemp(prefix="vresid_ledger_"))
    for j in durable_dir.glob("cand1__*.json"):
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

    print("V_resid VERDICT RUN (blind) | loading panel (pickle) ...", flush=True)
    series_by_symbol = cached_session_series(ctx)

    arm_runs: dict[str, ArmRun] = {}
    for w in _WINDOWS:
        print(f"  running V_resid w{w} (draws={layer2.null.draws_per_day}) ...", flush=True)
        arm_runs[f"V_resid__{w}"] = _arm_run_for_window(
            w,
            series_by_symbol,
            adapter=adapter,
            layer2=layer2,
            circuit_cfg=ctx.config.circuit,
            seed=settings.seed,
        )

    ledger, tmp_dir = _temp_ledger_with_candidate1(ledger_cfg.dir)
    manifest = load_manifest(ledger_cfg.manifest_path)  # requires candidate #1's 6 (fail-closed)
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

    # save V_resid's charged (pessimistic excess-over-null) streams so they can be durably
    # persisted to ledger/ when the operator records the verdict (deterministic trial-ids).
    out_dir = Path(tempfile.gettempdir()) / "vresid_streams"
    out_dir.mkdir(parents=True, exist_ok=True)
    for arm_id, ar in arm_runs.items():
        excess = excess_over_null_median(ar.pessimistic.signal_by_day, ar.pessimistic.null_by_day)
        tid = f"cand2r__{arm_id}"  # candidate-2-residual namespace
        (out_dir / f"{tid}.json").write_text(
            json.dumps(
                {
                    "trial_id": tid,
                    "strategy": tid,
                    "params": {
                        "candidate": "candidate-2r-vresid",
                        "arm": arm_id,
                        "charged_stream": "pessimistic excess-over-null",
                        "cost_model": "fixed_spread (fees + 5/18 bps)",
                        "seed": settings.seed,
                    },
                    "returns": excess,
                }
            ),
            encoding="utf-8",
        )

    print(
        f"\n=== V_resid VERDICT ===  cumulative effective-N (cand#1 6 + V_resid 3) = {prog.effective_trials:.4f}  |  PBO = {prog.pbo.pbo:.3f}"
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
        f"\n(V_resid streams saved to {out_dir}; durable persistence on record. tmp ledger {tmp_dir}.)"
    )


if __name__ == "__main__":
    main()
