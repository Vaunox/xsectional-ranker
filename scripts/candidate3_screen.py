"""Candidate #3 independence screen (blind, pre-verdict; pre-registration §7).

Reuses the D8-style screen machinery. Reports, per window, the pre-registered DISTINCTNESS gate --
corr(SR, candidate #1 gap) and corr(SR-Z, gap/ATR) against the band pinned BLIND in the pre-reg
(rank-corr >= 0.8 re-skin / < 0.5 distinct / 0.5-0.8 STOP) -- plus the diagnostic corr(SR, morning
return) (candidate #3 openly IS a price signal, so a high value is expected and NOT a gate; it
quantifies how much the sector-demeaning moves the ranking). No P&L, no verdict. Panel pickle.
"""

from __future__ import annotations

from datetime import date

from xsranker.backtest.independence_screen import FeatureByDay, band, corr_summary
from xsranker.backtest.universe_panel import SessionSeries, cached_session_series
from xsranker.core.config import load_settings
from xsranker.core.logging import configure_logging
from xsranker.data.factory import build_data_context
from xsranker.execution.config import load_layer2_config
from xsranker.features.point_in_time import entry_window_return
from xsranker.harness.adapter import HarnessAdapter
from xsranker.signals.sector_relative import (
    DEFAULT_MIN_PEERS,
    sector_relative_move,
    sector_relative_z,
)
from xsranker.signals.spec import SignalArm, atr_pct_by_day, gap_pct_by_day
from xsranker.signals.spec import signal_value_by_day as gap_signal_by_day

_WINDOWS = (15, 30, 45)
_REGULAR_START_MIN = 555


def _morning_return(series_by_symbol: SessionSeries, entry_minute: int) -> FeatureByDay:
    out: FeatureByDay = {}
    for sym, (series, _sector) in series_by_symbol.items():
        days, vals = entry_window_return(series, entry_minute=entry_minute)
        out[sym] = {
            d.astype("datetime64[D]").astype(date): float(v)
            for d, v in zip(days, vals, strict=True)
        }
    return out


def _features(
    series_by_symbol: SessionSeries, adapter: HarnessAdapter, entry_minute: int, atr_period: int
) -> dict[str, FeatureByDay]:
    atr: FeatureByDay = {}
    gap: FeatureByDay = {}
    gaz: FeatureByDay = {}
    sector: dict[str, str] = {}
    for sym, (series, sec) in series_by_symbol.items():
        sector[sym] = sec
        atr[sym] = atr_pct_by_day(series, adapter, atr_period=atr_period)
        gap[sym] = gap_pct_by_day(series, adapter)
        gaz[sym] = gap_signal_by_day(SignalArm.A_Z, series, adapter, atr_period=atr_period)
    mr = _morning_return(series_by_symbol, entry_minute)
    sr = sector_relative_move(mr, sector, min_peers=DEFAULT_MIN_PEERS)
    srz = sector_relative_z(sr, atr)
    return {"SR": sr, "SR-Z": srz, "gap": gap, "gap/ATR": gaz, "morning_return": mr}


def main() -> None:
    configure_logging(level="WARNING", renderer="console")
    settings = load_settings()
    adapter = HarnessAdapter(settings)
    atr_period = load_layer2_config(settings).signal.atr_period
    ctx = build_data_context(settings)
    print("candidate #3 independence screen | loading panel (pickle) ...", flush=True)
    series_by_symbol = cached_session_series(ctx)

    # D1 diagnostic: names excluded from SR because their sector has < 3 names (>= 2 peers).
    feats = _features(series_by_symbol, adapter, _REGULAR_START_MIN + _WINDOWS[0], atr_period)
    with_sr = set(feats["SR"])
    excluded = sorted(set(series_by_symbol) - with_sr)
    print(
        f"\nD1 diagnostic — SR defined for {len(with_sr)}/{len(series_by_symbol)} names; "
        f"{len(excluded)} excluded (<3-name sectors): {excluded}"
    )

    comparisons = [
        ("SR", "gap", "vs cand#1 gap  [DISTINCTNESS GATE]"),
        ("SR-Z", "gap/ATR", "vs cand#1 gap  [DISTINCTNESS GATE]"),
        ("SR", "morning_return", "vs morning return  [diagnostic]"),
    ]
    print(
        f"\n{'window':>6} {'comparison':>40} {'n_days':>7} "
        f"{'xs_Pearson':>11} {'xs_Spearman':>12} {'pooled_S':>9}  verdict (xs-Spearman)"
    )
    for w in _WINDOWS:
        feats = _features(series_by_symbol, adapter, _REGULAR_START_MIN + w, atr_period)
        for xk, yk, label in comparisons:
            s = corr_summary(feats[xk], feats[yk])
            verdict = band(s["xs_spearman_mean"]) if "GATE" in label else "(diagnostic)"
            print(
                f"{w:>6} {f'{xk} {label}':>40} {int(s['n_days']):>7} "
                f"{s['xs_pearson_mean']:>11.3f} {s['xs_spearman_mean']:>12.3f} "
                f"{s['pooled_spearman']:>9.3f}  {verdict}"
            )


if __name__ == "__main__":
    main()
