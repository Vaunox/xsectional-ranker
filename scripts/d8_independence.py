"""D8 — momentum-proxy / gap-re-skin independence gate (blind, pre-run; pre-registration §10.1).

V classifies bars by close-vs-open (a price measure), so it MIGHT be volume-weighted morning
momentum, or a re-skin of candidate #1's gap, in disguise. This computes the pre-committed
correlations of the SIGNAL VALUES (no P&L, no verdict) so the operator can adjudicate against the
frozen bands BEFORE anything runs to a candidate-#2 verdict:

* vs **morning return** (open→entry): is V just intraday momentum?
* vs candidate #1's **gap** (V vs gap%, V-A vs gap%÷ATR%): is V a gap re-skin?

The gate is the **Spearman (rank)** correlation because the strategy acts on the cross-sectional
rank; Pearson is reported alongside. Bands (rank-corr): ≥ 0.8 → proxy/re-skin (record as a
finding; revise independence + D6); < 0.5 → independence stands; 0.5-0.8 → STOP, bring to operator.

Because the strategy ranks the cross-section each day, the decision-relevant statistic is the
**per-day cross-sectional** correlation averaged over days; the **pooled** correlation over all
(symbol, day) observations is reported as a secondary read. Uses the machine-local panel pickle
(``$XSR_PANEL_PICKLE``) — never reloads Parquet.
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
from xsranker.signals.spec import SignalArm, gap_pct_by_day
from xsranker.signals.spec import signal_value_by_day as gap_signal_by_day
from xsranker.signals.volume_delta import VolumeDeltaArm, cross_sectional_residual
from xsranker.signals.volume_delta import signal_value_by_day as vd_signal_by_day

_WINDOWS = (15, 30, 45)
_REGULAR_START_MIN = 555  # 09:15 IST


def _morning_return_by_day(series_by_symbol: SessionSeries, entry_minute: int) -> FeatureByDay:
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
    """Per-window features keyed feature -> symbol -> {day -> value}."""
    v: FeatureByDay = {}
    va: FeatureByDay = {}
    gap: FeatureByDay = {}
    gaz: FeatureByDay = {}
    for sym, (series, _sector) in series_by_symbol.items():
        v[sym] = vd_signal_by_day(VolumeDeltaArm.V, series, entry_minute=entry_minute)
        va[sym] = vd_signal_by_day(VolumeDeltaArm.V_A, series, entry_minute=entry_minute)
        gap[sym] = gap_pct_by_day(series, adapter)
        gaz[sym] = gap_signal_by_day(SignalArm.A_Z, series, adapter, atr_period=atr_period)
    mr = _morning_return_by_day(series_by_symbol, entry_minute)
    # V_resid: per-day cross-sectional residual of V on the morning return (the D8-STOP fix) —
    # directional flow orthogonal to the morning price move by construction.
    v_resid = cross_sectional_residual(v, mr)
    return {
        "V": v,
        "V-A": va,
        "V_resid": v_resid,
        "gap": gap,
        "gap/ATR": gaz,
        "morning_return": mr,
    }


def main() -> None:
    configure_logging(level="WARNING", renderer="console")
    settings = load_settings()
    adapter = HarnessAdapter(settings)
    atr_period = load_layer2_config(settings).signal.atr_period
    ctx = build_data_context(settings)
    print("loading panel (pickle) ...", flush=True)
    series_by_symbol = cached_session_series(ctx)

    comparisons = [
        ("V", "morning_return", "vs morning return"),
        ("V-A", "morning_return", "vs morning return"),
        ("V_resid", "morning_return", "vs morning return"),  # the fix: expect ~0 by construction
        ("V", "gap", "vs candidate #1 gap"),
        ("V-A", "gap/ATR", "vs candidate #1 gap"),
        ("V_resid", "gap", "vs candidate #1 gap"),  # expect to stay low
    ]
    print(
        f"\n{'window':>6} {'comparison':>34} {'n_days':>7} "
        f"{'xs_Pearson':>11} {'xs_Spearman':>12} {'pooled_P':>9} {'pooled_S':>9}  band (xs-Spearman)"
    )
    for w in _WINDOWS:
        feats = _features(series_by_symbol, adapter, _REGULAR_START_MIN + w, atr_period)
        for xk, yk, label in comparisons:
            s = corr_summary(feats[xk], feats[yk])
            print(
                f"{w:>6} {f'{xk} {label}':>34} {int(s['n_days']):>7} "
                f"{s['xs_pearson_mean']:>11.3f} {s['xs_spearman_mean']:>12.3f} "
                f"{s['pooled_pearson']:>9.3f} {s['pooled_spearman']:>9.3f}  {band(s['xs_spearman_mean'])}"
            )


if __name__ == "__main__":
    main()
