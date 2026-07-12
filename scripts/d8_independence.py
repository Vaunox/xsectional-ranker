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

import numpy as np
from scipy import stats

from xsranker.backtest.universe_panel import SessionSeries, cached_session_series
from xsranker.core.config import load_settings
from xsranker.core.logging import configure_logging
from xsranker.data.factory import build_data_context
from xsranker.execution.config import load_layer2_config
from xsranker.features.point_in_time import entry_window_return
from xsranker.harness.adapter import HarnessAdapter
from xsranker.signals.spec import SignalArm, gap_pct_by_day
from xsranker.signals.spec import signal_value_by_day as gap_signal_by_day
from xsranker.signals.volume_delta import VolumeDeltaArm
from xsranker.signals.volume_delta import signal_value_by_day as vd_signal_by_day

_WINDOWS = (15, 30, 45)
_REGULAR_START_MIN = 555  # 09:15 IST
_MIN_XS = 10  # minimum names in a day's cross-section for a meaningful correlation

FeatureByDay = dict[str, dict[date, float]]  # symbol -> {day -> value}


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
    return {
        "V": v,
        "V-A": va,
        "gap": gap,
        "gap/ATR": gaz,
        "morning_return": _morning_return_by_day(series_by_symbol, entry_minute),
    }


def _cross_sections(x: FeatureByDay, y: FeatureByDay) -> list[tuple[np.ndarray, np.ndarray]]:
    """Per-day aligned (x, y) arrays over the symbols present in BOTH, for days with >= _MIN_XS."""
    days: set[date] = set()
    for sym in x.keys() & y.keys():
        days |= x[sym].keys() & y[sym].keys()
    out: list[tuple[np.ndarray, np.ndarray]] = []
    for d in sorted(days):
        pairs = [(x[s][d], y[s][d]) for s in x.keys() & y.keys() if d in x[s] and d in y[s]]
        if len(pairs) >= _MIN_XS:
            arr = np.asarray(pairs, dtype=np.float64)
            out.append((arr[:, 0], arr[:, 1]))
    return out


def _corr_summary(x: FeatureByDay, y: FeatureByDay) -> dict[str, float]:
    """Per-day cross-sectional (mean) + pooled Pearson/Spearman between features x and y."""
    xs = _cross_sections(x, y)
    per_day_p, per_day_s = [], []
    pooled_x, pooled_y = [], []
    for xi, yi in xs:
        pooled_x.append(xi)
        pooled_y.append(yi)
        if np.std(xi) > 0 and np.std(yi) > 0:
            per_day_p.append(float(stats.pearsonr(xi, yi)[0]))
            per_day_s.append(float(stats.spearmanr(xi, yi)[0]))
    px, py = np.concatenate(pooled_x), np.concatenate(pooled_y)
    return {
        "n_days": float(len(xs)),
        "n_obs": float(px.size),
        "xs_pearson_mean": float(np.mean(per_day_p)) if per_day_p else float("nan"),
        "xs_spearman_mean": float(np.mean(per_day_s)) if per_day_s else float("nan"),
        "pooled_pearson": float(stats.pearsonr(px, py)[0]),
        "pooled_spearman": float(stats.spearmanr(px, py)[0]),
    }


def _band(rank_corr: float) -> str:
    a = abs(rank_corr)
    if a >= 0.8:
        return "PROXY/RE-SKIN (>=0.8)"
    if a < 0.5:
        return "independent (<0.5)"
    return "STOP 0.5-0.8"


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
        ("V", "gap", "vs candidate #1 gap"),
        ("V-A", "gap/ATR", "vs candidate #1 gap"),
    ]
    print(
        f"\n{'window':>6} {'comparison':>34} {'n_days':>7} "
        f"{'xs_Pearson':>11} {'xs_Spearman':>12} {'pooled_P':>9} {'pooled_S':>9}  band (xs-Spearman)"
    )
    for w in _WINDOWS:
        feats = _features(series_by_symbol, adapter, _REGULAR_START_MIN + w, atr_period)
        for xk, yk, label in comparisons:
            s = _corr_summary(feats[xk], feats[yk])
            print(
                f"{w:>6} {f'{xk} {label}':>34} {int(s['n_days']):>7} "
                f"{s['xs_pearson_mean']:>11.3f} {s['xs_spearman_mean']:>12.3f} "
                f"{s['pooled_pearson']:>9.3f} {s['pooled_spearman']:>9.3f}  {_band(s['xs_spearman_mean'])}"
            )


if __name__ == "__main__":
    main()
