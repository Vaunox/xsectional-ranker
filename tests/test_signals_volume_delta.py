"""Proxy CVD (candidate #2) — correctness, the trailing baseline, and prefix-invariance.

Prefix-invariance is the load-bearing D8/leakage property: a day's V / V-A must use ONLY bars
with minute ≤ entry, so appending post-entry bars or future days cannot change it. Plus the
flat-bar rule, the 20-day baseline, its min-history guard, and teeth (a boundary/lookahead leak
is caught).
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from xsranker.core.types import OHLCV
from xsranker.signals.volume_delta import VolumeDeltaArm, signal_value_by_day

# 09:15..09:35 IST; entry_minute 570 (09:30) -> window = {555,560,565,570}, 575 is POST-entry.
_MINUTES = (555, 560, 565, 570, 575)
_ENTRY = 570
_UTC_MIN = tuple(m - 330 for m in _MINUTES)  # IST = UTC + 05:30
_START = date(2024, 1, 1)


def _bar_prices(kind: str) -> tuple[float, float, float, float]:
    """(open, high, low, close) for an up / down / flat bar."""
    if kind == "u":
        return 100.0, 100.6, 99.9, 100.5
    if kind == "d":
        return 100.0, 100.1, 99.4, 99.5
    return 100.0, 100.2, 99.8, 100.0  # flat: close == open


def _series(kinds: list[str], vols: list[int], *, ndays: int) -> OHLCV:
    """A synthetic multi-day series; each day repeats the same per-bar kinds + volumes."""
    ts: list[np.datetime64] = []
    o, h, low, c, v = [], [], [], [], []
    for di in range(ndays):
        d0 = np.datetime64(_START + timedelta(days=di), "ns")
        for bi, um in enumerate(_UTC_MIN):
            ts.append(d0 + np.timedelta64(um * 60, "s"))
            oo, hh, ll, cc = _bar_prices(kinds[bi])
            o.append(oo)
            h.append(hh)
            low.append(ll)
            c.append(cc)
            v.append(vols[bi])
    return OHLCV(
        "X",
        "5minute",
        np.array(ts, dtype="datetime64[ns]"),
        np.array(o),
        np.array(h),
        np.array(low),
        np.array(c),
        np.array(v, dtype=np.int64),
    )


# window bars {555,560,565,570} are kinds[0:4]; the 575 bar (kinds[4]) is post-entry.
_KINDS = ["u", "d", "u", "d", "u"]  # window up/down/up/down; post-entry 'u' must be ignored
_VOLS = [10, 20, 30, 40, 999]  # ΣV_up=10+30=40, ΣV_down=20+40=60, ΣV_total=100 -> V=-0.2


def test_v_raw_value_and_flat_and_post_entry_exclusion() -> None:
    v = signal_value_by_day(VolumeDeltaArm.V, _series(_KINDS, _VOLS, ndays=3), entry_minute=_ENTRY)
    assert v  # every day has a value
    for val in v.values():
        assert abs(val - (-0.2)) < 1e-12  # (40-60)/100; the 999-volume post-entry 'u' is excluded


def test_flat_bar_adds_to_denominator_not_numerator() -> None:
    # 3rd window bar flat (vol 30): ΣV_up=10, ΣV_down=20+40=60, ΣV_total=100 -> (10-60)/100 = -0.5.
    # The flat bar's 30 is in the denominator (total) but contributes 0 to the signed numerator.
    v = signal_value_by_day(
        VolumeDeltaArm.V, _series(["u", "d", "f", "d", "u"], _VOLS, ndays=2), entry_minute=_ENTRY
    )
    for val in v.values():
        assert abs(val - (-0.5)) < 1e-12


def test_prefix_invariant_to_post_entry_bar() -> None:
    """The post-entry (575) bar's kind/volume must NOT change V or V-A (it is outside the window)."""
    base = _series(_KINDS, _VOLS, ndays=25)
    perturbed = _series(["u", "d", "u", "d", "d"], [10, 20, 30, 40, 1], ndays=25)  # 575 bar changed
    for arm in (VolumeDeltaArm.V, VolumeDeltaArm.V_A):
        a = signal_value_by_day(arm, base, entry_minute=_ENTRY)
        b = signal_value_by_day(arm, perturbed, entry_minute=_ENTRY)
        assert a and a.keys() == b.keys()
        for d in a:
            assert a[d] == b[d]


def test_prefix_invariant_to_future_days() -> None:
    """Truncating future days leaves each retained day's V / V-A unchanged (no lookahead)."""
    full = _series(_KINDS, _VOLS, ndays=25)
    trunc = _series(_KINDS, _VOLS, ndays=23)
    for arm in (VolumeDeltaArm.V, VolumeDeltaArm.V_A):
        f = signal_value_by_day(arm, full, entry_minute=_ENTRY)
        t = signal_value_by_day(arm, trunc, entry_minute=_ENTRY)
        assert t
        for d, val in t.items():
            assert f[d] == val


def test_v_abnormal_baseline_and_min_history_guard() -> None:
    """V-A needs 20 prior days; with constant volumes the baseline is 100 -> V-A = -20/100 = -0.2."""
    va = signal_value_by_day(
        VolumeDeltaArm.V_A, _series(_KINDS, _VOLS, ndays=25), entry_minute=_ENTRY
    )
    days = sorted(
        signal_value_by_day(VolumeDeltaArm.V, _series(_KINDS, _VOLS, ndays=25), entry_minute=_ENTRY)
    )
    assert set(va) == set(days[20:])  # first 20 days omitted (insufficient trailing history)
    for val in va.values():
        assert abs(val - (-0.2)) < 1e-12


def test_teeth_including_the_post_entry_bar_would_change_v() -> None:
    """Teeth: if the window WRONGLY reached the post-entry bar, V would differ — proving the
    minute<=entry boundary is what makes the exclusion (and prefix-invariance) real."""
    windowed = signal_value_by_day(
        VolumeDeltaArm.V, _series(_KINDS, _VOLS, ndays=2), entry_minute=_ENTRY
    )
    reached_past = signal_value_by_day(
        VolumeDeltaArm.V, _series(_KINDS, _VOLS, ndays=2), entry_minute=575
    )  # includes the 999-volume 'u' bar
    d = next(iter(windowed))
    assert windowed[d] != reached_past[d]
