"""Reusable independence-screen correlation machinery (the D8-style pre-verdict screen).

A candidate signal is screened BLIND, before any verdict run, by correlating its per-day
cross-sectional ranking against a control (momentum, a prior candidate's signal, ...). Because the
strategy ranks the cross-section each day, the decision-relevant statistic is the **per-day
cross-sectional** correlation averaged over days; the **pooled** correlation over all (symbol, day)
observations is reported as a secondary read. First used for candidate #2 (D8: V/V-A vs momentum &
gap); reused for every later candidate's distinctness screen.
"""

from __future__ import annotations

from datetime import date

import numpy as np
from scipy import stats

#: symbol -> {day -> value} for one feature.
FeatureByDay = dict[str, dict[date, float]]

#: Minimum names in a day's cross-section for a meaningful correlation.
DEFAULT_MIN_XS = 10


def cross_sections(
    x: FeatureByDay, y: FeatureByDay, *, min_xs: int = DEFAULT_MIN_XS
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Per-day aligned (x, y) arrays over the symbols present in BOTH, for days with >= min_xs."""
    days: set[date] = set()
    for sym in x.keys() & y.keys():
        days |= x[sym].keys() & y[sym].keys()
    out: list[tuple[np.ndarray, np.ndarray]] = []
    for d in sorted(days):
        pairs = [(x[s][d], y[s][d]) for s in x.keys() & y.keys() if d in x[s] and d in y[s]]
        if len(pairs) >= min_xs:
            arr = np.asarray(pairs, dtype=np.float64)
            out.append((arr[:, 0], arr[:, 1]))
    return out


def corr_summary(
    x: FeatureByDay, y: FeatureByDay, *, min_xs: int = DEFAULT_MIN_XS
) -> dict[str, float]:
    """Per-day cross-sectional (mean) + pooled Pearson/Spearman between features x and y."""
    xs = cross_sections(x, y, min_xs=min_xs)
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


def band(rank_corr: float) -> str:
    """The pre-registered independence band on |rank-corr| (>=0.8 re-skin / <0.5 distinct / STOP)."""
    a = abs(rank_corr)
    if a >= 0.8:
        return "PROXY/RE-SKIN (>=0.8)"
    if a < 0.5:
        return "distinct (<0.5)"
    return "STOP 0.5-0.8"
