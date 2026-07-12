"""The single BLIND verdict runner for the Gap Regime-Abstention Study (frozen pre-reg
`gap-abstention-preregistration`).

*** STOOD DOWN 2026-07-12 -- NEVER RUN TO A VERDICT (RESEARCH_FINDINGS section 7.6). ***
Built and smoke-validated, then stood down when the smoke exposed a cost-unit error: the study's
premise compared the one-leg GROSS (12.6-23 bps) to the PER-NAME cost (11.6/15.6), but the book is
5 long + 5 short and both legs round-trip, so the BOOK break-even is 2x per-name = 23.2/31.2 bps.
The best conditioned gross never clears it; the gated book nets -9.13/-17.13 (absolute-net kills it
deterministically). Preserved for provenance; NOT executed, nothing charged to the ledger.

A REFINEMENT of the banked candidate #1 -- gate the A-Z_15 gap book to trade only above-normal-
dislocation days; test whether the gated book nets > 0 where the un-gated one only breaks even.
Four components, all frozen-pinned:

1. Mechanism gate: cross-sectional dispersion of raw gap% > its trailing-60d median (point-in-time).
2. The full 3-axis x 4-level + exit search charged to the durable ledger (`cand1abs__*`).
3. Survivorship-interaction decomposition: long- vs short-leg gross by dislocation tercile.
4. Block-bootstrap CI (5-day blocks, 10,000 resamples, seed 20260711) on gated net -- a BINDING gate.

Nothing was seen when any parameter was pinned. Uses the panel pickle ($XSR_PANEL_PICKLE).
"""

from __future__ import annotations

import dataclasses
import json
import shutil
import tempfile
from datetime import date
from pathlib import Path
from typing import cast

import numpy as np

from xsranker.backtest.harness import (
    ArmRun,
    DayStreams,
    SymbolDay,
    build_symbol_days,
    run_arm,
)
from xsranker.backtest.pnl import book_net_return  # noqa: F401  (convention reference)
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
from xsranker.execution.book import DayDropped
from xsranker.execution.config import Layer2Config, load_layer2_config
from xsranker.execution.pipeline import build_book
from xsranker.gate.benchmark import excess_over_null_median
from xsranker.gate.config import load_gate_structural, load_gate_thresholds
from xsranker.harness.adapter import HarnessAdapter, TrialLedger
from xsranker.ledger.config import load_ledger_config
from xsranker.ledger.persistence import load_manifest
from xsranker.signals.spec import SignalArm, atr_pct_by_day, gap_pct_by_day

ENTRY = 570  # 09:30 (A-Z_15)
EXITS = {"1100": 660, "1230": 750, "1400": 840}  # close is the base arm
L = 60  # trailing-median lookback (trading days), pinned
_BOOT_N = 10_000
_BOOT_BLOCK = 5
_BOOT_SEED = 20260711


def _d(dt: np.datetime64) -> date:
    return cast(date, dt.astype("datetime64[D]").astype(date))


def _circuit(series: OHLCV, cfg: CircuitConfig) -> dict[date, bool]:
    dates = series.ist_dates()
    return {
        _d(dates[i]): is_circuit_locked_at(series, int(i), cfg)
        for i in entry_bar_indices(series, entry_minute=ENTRY)
    }


def _hold_to(series: OHLCV, exit_min: int) -> dict[date, float]:
    dates, close = series.ist_dates(), series.close
    e = {_d(dates[i]): float(close[i]) for i in entry_bar_indices(series, entry_minute=ENTRY)}
    x = {_d(dates[i]): float(close[i]) for i in entry_bar_indices(series, entry_minute=exit_min)}
    return {d: x[d] / e[d] - 1.0 for d in e if d in x and e[d] > 0}


def _build_cross(
    panel: SessionSeries, adapter: HarnessAdapter, layer2: Layer2Config, circuit: CircuitConfig
) -> dict[date, list[SymbolDay]]:
    cross: dict[date, list[SymbolDay]] = {}
    for sym, (series, sec) in panel.items():
        st = SecurityStatus(sym, Series.EQ)
        sd = build_symbol_days(
            sym,
            series,
            arm=SignalArm.A_Z,
            entry_minute=ENTRY,
            atr_period=layer2.signal.atr_period,
            sector=sec,
            long_eligible=long_eligible(st),
            short_eligible=short_eligible(st),
            circuit_locked_by_day=_circuit(series, circuit),
            adapter=adapter,
            compute_spread=False,
        )
        for d, x in sd.items():
            cross.setdefault(d, []).append(x)
    return cross


def _run(
    cross: dict[date, list[SymbolDay]], adapter: HarnessAdapter, layer2: Layer2Config
) -> ArmRun:
    days = sorted(cross)
    return run_arm(
        days,
        cross,
        adapter=adapter,
        exec_cfg=layer2.execution,
        cost_cfg=layer2.cost,
        cost_model=adapter.load_cost_model(),
        draws_per_day=layer2.null.draws_per_day,
        rng=np.random.default_rng(load_settings().seed),
        continuation=False,
    )


def _subset(ar: ArmRun, days: set[date]) -> ArmRun:
    def sub(ds: DayStreams) -> DayStreams:
        return DayStreams(
            {d: v for d, v in ds.signal_by_day.items() if d in days},
            {d: v for d, v in ds.null_by_day.items() if d in days},
        )

    return dataclasses.replace(ar, optimistic=sub(ar.optimistic), pessimistic=sub(ar.pessimistic))


def _per_leg_gross(
    cross: dict[date, list[SymbolDay]], adapter: HarnessAdapter, layer2: Layer2Config
) -> dict[date, tuple[float, float]]:
    """Per day (long-leg gross, short-leg gross), cost-free (pnl convention: long +hold, short -hold)."""
    out: dict[date, tuple[float, float]] = {}
    for d, sds in cross.items():
        book = build_book([x.inputs for x in sds], adapter, layer2.execution, continuation=False)
        if isinstance(book, DayDropped):
            continue
        holds = {x.inputs.symbol: x.hold for x in sds}
        lg = sum(p.weight * holds[p.symbol] for p in book.longs)
        sg = sum(p.weight * (-holds[p.symbol]) for p in book.shorts)
        out[d] = (lg, sg)
    return out


def _dispersion_and_axes(
    panel: SessionSeries, adapter: HarnessAdapter, atr_period: int, days: list[date]
) -> tuple[dict[date, float], dict[date, float], dict[date, float]]:
    """Per-day cross-sectional dispersion of raw gap% (primary axis), market vol, gap magnitude."""
    gap: dict[str, dict[date, float]] = {}
    atr: dict[str, dict[date, float]] = {}
    for sym, (series, _sec) in panel.items():
        gap[sym] = gap_pct_by_day(series, adapter)
        atr[sym] = atr_pct_by_day(series, adapter, atr_period=atr_period)
    disp, vol, mag = {}, {}, {}
    for d in days:
        gaps = [gap[s][d] for s in gap if d in gap[s]]
        atrs = [atr[s][d] for s in atr if d in atr[s]]
        if len(gaps) >= 10:
            disp[d] = float(np.std(gaps))
            mag[d] = float(np.mean(np.abs(gaps)))
        if len(atrs) >= 10:
            vol[d] = float(np.mean(atrs))
    return disp, vol, mag


def _primary_gate_days(disp: dict[date, float], days: list[date]) -> set[date]:
    """Trade day t iff dispersion_t > trailing-L median of dispersion (strictly-prior L days)."""
    ds = [d for d in days if d in disp]
    gated: set[date] = set()
    for i in range(L, len(ds)):
        window = [disp[ds[j]] for j in range(i - L, i)]
        if disp[ds[i]] > float(np.median(window)):
            gated.add(ds[i])
    return gated


def _top_pct_days(axis: dict[date, float], days: list[date], keep_pct: int) -> set[date]:
    """Fixed full-sample percentile gate: trade the top ``keep_pct``% of days by ``axis`` (the search)."""
    vals = [axis[d] for d in days if d in axis]
    thr = float(np.percentile(vals, 100 - keep_pct))
    return {d for d in days if d in axis and axis[d] >= thr}


def _excess(ar: ArmRun) -> list[float]:
    return excess_over_null_median(ar.pessimistic.signal_by_day, ar.pessimistic.null_by_day)


def _block_bootstrap_ci(vals: list[float]) -> tuple[float, float]:
    """95% CI on the MEDIAN via a 5-day block bootstrap (respects daily-return autocorrelation)."""
    a = np.asarray(vals, dtype=np.float64)
    n = a.size
    if n < _BOOT_BLOCK:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(_BOOT_SEED)
    n_blocks = int(np.ceil(n / _BOOT_BLOCK))
    meds = np.empty(_BOOT_N)
    starts_max = n - _BOOT_BLOCK + 1
    for b in range(_BOOT_N):
        starts = rng.integers(0, starts_max, size=n_blocks)
        idx = (starts[:, None] + np.arange(_BOOT_BLOCK)[None, :]).ravel()[:n]
        meds[b] = np.median(a[idx])
    return (float(np.percentile(meds, 2.5)) * 1e4, float(np.percentile(meds, 97.5)) * 1e4)


def _med_bps(sig: dict[date, float], days: set[date] | None = None) -> float:
    xs = [v for d, v in sig.items() if days is None or d in days]
    return float(np.median(xs)) * 1e4 if xs else float("nan")


def main() -> None:
    configure_logging(level="INFO", renderer="console")
    settings = load_settings()
    adapter = HarnessAdapter(settings)
    layer2 = load_layer2_config(settings)
    thresholds = load_gate_thresholds(settings)
    struct = load_gate_structural(settings)
    ledger_cfg = load_ledger_config(settings)
    ctx = build_data_context(settings)

    print("gap-abstention VERDICT (blind) | loading panel (pickle) ...", flush=True)
    panel = cached_session_series(ctx)

    # --- base book + its per-leg gross + per-day dislocation axes ---
    cross = _build_cross(panel, adapter, layer2, ctx.config.circuit)
    days = sorted(cross)
    print(f"  base book: {len(days)} days | running the un-gated null (close) ...", flush=True)
    base = _run(cross, adapter, layer2)
    leg = _per_leg_gross(cross, adapter, layer2)
    disp, vol, mag = _dispersion_and_axes(panel, adapter, layer2.signal.atr_period, days)

    gated = _primary_gate_days(disp, days) & set(base.pessimistic.signal_by_day)
    print(
        f"  PRIMARY gate: dispersion > trailing-{L}d median -> {len(gated)} gated days", flush=True
    )

    # --- exit-sweep arms (11:00/12:30/14:00): rebuild holds, own null ---
    exit_arms: dict[str, ArmRun] = {}
    for lab, xm in EXITS.items():
        holds_by = {sym: _hold_to(series, xm) for sym, (series, _s) in panel.items()}
        cross_x = {
            d: [
                dataclasses.replace(x, hold=holds_by[x.inputs.symbol][d])
                for x in sds
                if d in holds_by[x.inputs.symbol]
            ]
            for d, sds in cross.items()
        }
        cross_x = {d: xs for d, xs in cross_x.items() if xs}
        print(f"  running exit arm {lab} null ...", flush=True)
        exit_arms[lab] = _run(cross_x, adapter, layer2)

    # --- assemble the charged search (14 DISTINCT streams; the 3 trade-all cells + close-exit
    #     collapse to `base`, so 14 of the nominal 3x4+exit=17 grid) ---
    search: dict[str, list[float]] = {"cand1abs__base": _excess(base)}
    for axis_name, axis in (("gapdisp", disp), ("mktvol", vol), ("gapmag", mag)):
        for keep in (75, 50, 25):
            cell = _top_pct_days(axis, days, keep) & set(base.pessimistic.signal_by_day)
            search[f"cand1abs__{axis_name}_{keep}"] = _excess(_subset(base, cell))
    for lab, ar in exit_arms.items():
        search[f"cand1abs__exit_{lab}"] = _excess(ar)
    primary_arm = _subset(base, gated)

    # --- charge to a temp ledger (priors + the 12 non-{base,primary} search) and gate the primary ---
    tmp = Path(tempfile.mkdtemp(prefix="cand1abs_ledger_"))
    for pat in ("cand1__*.json", "cand2r__*.json", "cand3__*.json"):
        for j in ledger_cfg.dir.glob(pat):
            shutil.copy(j, tmp / j.name)
    ledger = TrialLedger(tmp)
    for tid, stream in search.items():
        if tid == "cand1abs__base":
            continue  # charged via run_program (passed as an arm for PBO)
        ledger.log_trial(strategy=tid, params={"charged": "search"}, returns=stream)
    manifest = load_manifest(ledger_cfg.manifest_path)  # requires the 15 priors (fail-closed)
    prog = run_program(
        {"cand1abs__primary": primary_arm, "cand1abs__base": base},
        ledger=ledger,
        adapter=adapter,
        thresholds=thresholds,
        cpcv_groups=struct.cpcv_n_groups,
        cpcv_k=struct.cpcv_k_test,
        periods_per_year=struct.periods_per_year,
        pbo_splits=struct.pbo_n_splits,
        manifest=manifest,
    )
    primary = next(r for r in prog.arms if r.arm_id == "cand1abs__primary")

    # --- SURVIVORSHIP DECOMPOSITION (the make-or-break; reported FIRST) ---
    # long-leg share of book gross, by dislocation tercile (all days with a book + dispersion).
    ld = [d for d in leg if d in disp]
    q1, q2 = np.percentile([disp[d] for d in ld], [33.333, 66.667])
    terc = {
        "LOW": [d for d in ld if disp[d] <= q1],
        "MID": [d for d in ld if q1 < disp[d] <= q2],
        "HIGH": [d for d in ld if disp[d] > q2],
    }
    surv = {}
    for name, ds in terc.items():
        lg = sum(leg[d][0] for d in ds)
        sg = sum(leg[d][1] for d in ds)
        tot = lg + sg
        surv[name] = (100 * lg / tot if tot else float("nan"), len(ds))
    # gated-days long share (the HOLD-rule quantity)
    gl = sum(leg[d][0] for d in gated if d in leg)
    gs = sum(leg[d][1] for d in gated if d in leg)
    gated_long_share = 100 * gl / (gl + gs) if (gl + gs) else float("nan")

    # --- CI on the gated NET (both bounds), block bootstrap ---
    gnet_opt = [base.optimistic.signal_by_day[d] for d in gated]
    gnet_pess = [base.pessimistic.signal_by_day[d] for d in gated]
    ci_opt = _block_bootstrap_ci(gnet_opt)
    ci_pess = _block_bootstrap_ci(gnet_pess)
    ungated_med_opt = _med_bps(base.optimistic.signal_by_day)
    ungated_med_pess = _med_bps(base.pessimistic.signal_by_day)

    # ================= REPORT (make-or-break FIRST; point estimate LAST) =================
    print("\n" + "=" * 78)
    print("GAP REGIME-ABSTENTION STUDY -- VERDICT")
    print("=" * 78)

    print("\n[1] SURVIVORSHIP DECOMPOSITION (the make-or-break -- reported before the headline)")
    print(
        "    long-leg share of book GROSS, by dislocation tercile (0=short-driven, 100=long-driven):"
    )
    for name in ("LOW", "MID", "HIGH"):
        share, n = surv[name]
        print(f"        {name:>4} dispersion: long-leg share {share:>6.1f}%   (n={n})")
    rising = surv["LOW"][0] <= surv["MID"][0] <= surv["HIGH"][0]
    print(f"    gated-days long-leg share: {gated_long_share:.1f}%")
    hold_triggered = gated_long_share > 60.0 and rising
    print(
        f"    HOLD rule (long-leg > 60% AND rising with dislocation): "
        f"{'TRIGGERED -> HOLD' if hold_triggered else 'not triggered'} "
        f"(>60%={gated_long_share > 60.0}, rising={rising})"
    )

    print("\n[2] GATED vs UN-GATED net (median bps) with block-bootstrap 95% CI [both bounds]")
    print(f"    {'':>10} {'un-gated':>12} {'gated':>12} {'gated 95% CI':>22}")
    print(
        f"    {'optimistic':>10} {ungated_med_opt:>12.2f} {_med_bps(base.optimistic.signal_by_day, gated):>12.2f}"
        f"   [{ci_opt[0]:>7.2f}, {ci_opt[1]:>7.2f}]"
    )
    print(
        f"    {'pessimistic':>10} {ungated_med_pess:>12.2f} {_med_bps(base.pessimistic.signal_by_day, gated):>12.2f}"
        f"   [{ci_pess[0]:>7.2f}, {ci_pess[1]:>7.2f}]"
    )
    ci_excludes_0 = ci_opt[0] > 0 and ci_pess[0] > 0

    print("\n[3] EFFECTIVE-N and deflated DSR")
    print(
        f"    cumulative effective-N (15 priors + 14 search incl. base/primary) = "
        f"{prog.effective_trials:.4f}  |  PBO = {prog.pbo.pbo:.3f}"
    )
    print(
        f"    PRIMARY DSR opt/pess = {primary.optimistic.dsr:.3f} / {primary.pessimistic.dsr:.3f}"
    )

    print(f"\n[4] GATED DAY-COUNT: {len(gated)} traded / {len(days)} total")

    print("\n[5] VERDICT against the three gates (stated separately):")
    ci_ok = ci_excludes_0
    absnet_ok = (
        primary.optimistic.absolute_net_median > 0 and primary.pessimistic.absolute_net_median > 0
    )
    print(f"    - CI gate (95% CI excludes 0, both bounds): {'PASS' if ci_ok else 'KILL'}")
    print(f"    - survivorship-HOLD gate: {'HOLD' if hold_triggered else 'PASS'}")
    print(
        f"    - absolute-net gate (median net > 0 both bounds): {'PASS' if absnet_ok else 'KILL'}  "
        f"(opt {primary.optimistic.absolute_net_median * 1e4:.2f} / "
        f"pess {primary.pessimistic.absolute_net_median * 1e4:.2f} bps)"
    )
    if hold_triggered:
        overall = "HOLD (survivorship-indistinguishable)"
    elif ci_ok and absnet_ok and primary.verdict.value == "pass":
        overall = "PASS (reclassify cand#1 -> conditionally tradeable, survivorship-asterisked; Phase-4-gated)"
    else:
        overall = "KILL"
    print(f"\n    >>> OVERALL: {overall}")
    print(
        f"    (point estimate -- least trustworthy, reported last: primary verdict = {primary.verdict.value})"
    )

    # --- persist the 14 charged streams for durable recording on the operator's go ---
    out = Path(tempfile.gettempdir()) / "cand1abs_streams"
    out.mkdir(parents=True, exist_ok=True)
    all_streams = dict(search)
    all_streams["cand1abs__primary"] = _excess(primary_arm)
    for tid, stream in all_streams.items():
        (out / f"{tid}.json").write_text(
            json.dumps(
                {
                    "trial_id": tid,
                    "strategy": tid,
                    "params": {
                        "candidate": "candidate-1-gap-abstention",
                        "charged_stream": "pess excess-over-null",
                    },
                    "returns": stream,
                }
            ),
            encoding="utf-8",
        )
    print(
        f"\n(14 charged streams saved to {out}; durable persistence on the operator's go. tmp {tmp}.)"
    )


if __name__ == "__main__":
    main()
