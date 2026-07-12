"""Candidate #2 — Proxy Cumulative Volume Delta (abnormal directional participation).

Signal (pre-registration `candidate-2-preregistration`, §2): slice the 09:15→entry morning
window into its 5-minute bars; classify each bar up/down/flat by its **own close-vs-open** (a
volume-direction proxy — never a cross-sectional price signal); then

* **V (raw)**  = ``(ΣV_up - ΣV_down) / ΣV_total``  — the within-day net directional fraction.
* **V-A (abnormal)** = ``(ΣV_up - ΣV_down) / V_baseline`` — net directional volume in units of the
  name's own trailing baseline, where ``V_baseline`` is the **median** of the same window's total
  volume over the **prior 20 trading days** (point-in-time; never full-sample, never forward).

Flat bars (``close == open``) add their volume to ``ΣV_total`` (the V denominator) but 0 to the
signed numerator — genuine no-conviction participation dilutes toward 0. HARD CONSTRAINT: the sign
comes ONLY from ``ΣV_up - ΣV_down`` (flow), never from a price move.

**Window convention.** The window is every bar of the day with IST-minute ≤ ``entry_minute``
(= 09:15 + W), i.e. through the entry bar whose close IS the entry instant — identical to the
frozen ``entry_window_value`` / ``hold_return`` machinery, so V is measured on exactly the window
the trade observes and enters on. Point-in-time / prefix-invariant: appending any bar after the
entry bar, or any future day, cannot change a day's value (the load-bearing D8/leakage property).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from datetime import date
from enum import StrEnum

import numpy as np

from xsranker.core.types import OHLCV

#: Trailing per-name baseline horizon for V-A (frozen: 20 trading days — the ATR-20 horizon).
DEFAULT_BASELINE_LOOKBACK = 20


class VolumeDeltaArm(StrEnum):
    """The two pre-registered arms (both charged to the ledger; parallel to A / A-Z)."""

    V = "V"  # raw directional participation fraction
    V_A = "V-A"  # abnormal (trailing-baseline-normalized) directional participation


def _window_signed_and_total(
    series: OHLCV, entry_minute: int
) -> tuple[list[date], dict[date, float], dict[date, float]]:
    """Per IST day with an entry bar: (ascending days, signed = ΣV_up-ΣV_down, total = ΣV_total).

    A day contributes only if it has a bar stamped exactly ``entry_minute`` (consistent with the
    other point-in-time features); the window is that day's bars with minute ≤ ``entry_minute``.
    """
    minutes = series.ist_minutes()
    dates = series.ist_dates()
    vol = series.volume.astype(np.float64)
    up = series.close > series.open
    down = series.close < series.open
    days: list[date] = []
    signed: dict[date, float] = {}
    total: dict[date, float] = {}
    for d in np.unique(dates):
        day = dates == d
        if not np.any(day & (minutes == entry_minute)):
            continue  # no entry bar this day -> excluded (same rule as hold_return/entry value)
        window = day & (minutes <= entry_minute)
        tot = float(vol[window].sum())
        py_d = d.astype("datetime64[D]").astype(date)
        days.append(py_d)
        signed[py_d] = float(vol[window & up].sum() - vol[window & down].sum())
        total[py_d] = tot
    return days, signed, total


def signal_value_by_day(
    arm: VolumeDeltaArm,
    series: OHLCV,
    *,
    entry_minute: int,
    baseline_lookback: int = DEFAULT_BASELINE_LOOKBACK,
) -> dict[date, float]:
    """Per-day V (raw) or V-A (abnormal) for ``series`` over the 09:15→``entry_minute`` window.

    V-A requires ``baseline_lookback`` complete prior trading days of the same window's total
    volume; a day with fewer (or a non-positive baseline / total) is omitted — non-finite names
    are not rankable and are dropped downstream, exactly like A-Z's ATR-history requirement.
    """
    days, signed, total = _window_signed_and_total(series, entry_minute)
    out: dict[date, float] = {}
    if arm is VolumeDeltaArm.V:
        for d in days:
            if total[d] > 0.0:
                out[d] = signed[d] / total[d]
        return out
    totals = [total[d] for d in days]
    for i, d in enumerate(days):
        if i < baseline_lookback:
            continue  # insufficient trailing history for the abnormal baseline
        baseline = float(np.median(totals[i - baseline_lookback : i]))  # strictly prior days
        if baseline > 0.0:
            out[d] = signed[d] / baseline
    return out


def cross_sectional_residual(
    signal: Mapping[str, Mapping[date, float]],
    control: Mapping[str, Mapping[date, float]],
    *,
    min_names: int = 10,
) -> dict[str, dict[date, float]]:
    """Residualize ``signal`` on ``control`` across each day's cross-section (OLS) — for V_resid.

    On each day, fit ``signal ~ a + b·control`` across the names present in both, and return the
    per-name **residual** ``signal - (a + b·control)``. The residual is orthogonal (least-squares)
    to the control BY CONSTRUCTION, so ranking on it isolates the part of ``signal`` the control
    does not explain — here, directional flow orthogonal to the morning price move (the leak D8
    found in raw V). Days with fewer than ``min_names`` names are omitted; a constant control on a
    day degenerates to a simple demean. Point-in-time: uses only that day's cross-section, so it
    inherits ``signal``/``control``'s own prefix-invariance (no new look-ahead across days).
    """
    by_day: dict[date, list[str]] = defaultdict(list)
    for s in signal.keys() & control.keys():
        for d in signal[s].keys() & control[s].keys():
            by_day[d].append(s)
    out: dict[str, dict[date, float]] = {}
    for d, names in by_day.items():
        if len(names) < min_names:
            continue
        y = np.array([signal[s][d] for s in names], dtype=np.float64)
        x = np.array([control[s][d] for s in names], dtype=np.float64)
        if float(np.std(x)) > 0.0:
            resid = y - np.polyval(np.polyfit(x, y, 1), x)  # y - (a + b·x)
        else:
            resid = y - float(np.mean(y))  # constant control that day -> just demean
        for s, r in zip(names, resid, strict=True):
            out.setdefault(s, {})[d] = float(r)
    return out
