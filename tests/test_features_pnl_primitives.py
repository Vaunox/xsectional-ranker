"""Hold return (entry->close) + entry-window value — the P&L primitives, with teeth.

The hold-return NO-LOOKAHEAD test is load-bearing (same status as the signal's
prefix-invariance): a hold return that reaches even one bar past its own session close
is leakage. The test proves the correct impl is prefix-invariant AND that a leaky exit
is NOT — so the invariance has teeth, it is not vacuous.
"""

from __future__ import annotations

from datetime import date

import numpy as np

from xsranker.core.types import IST_OFFSET_NS, OHLCV
from xsranker.features.point_in_time import entry_window_value, hold_return

# IST minutes-since-midnight: 09:15 = 555 (open), 09:45 = 585 (entry), 15:25 = 925 (last bar).
_OPEN, _ENTRY, _LAST = 555, 585, 925


def _series(days: list[tuple[date, list[tuple[int, float, int]]]]) -> OHLCV:
    """Build an OHLCV from (date, [(ist_minute, close, volume), ...]) — close==O==H==L."""
    ts: list[np.datetime64] = []
    closes: list[float] = []
    vols: list[int] = []
    for d, bars in days:
        base = np.datetime64(d, "ns")
        for minute, close, vol in bars:
            utc = (
                base
                + np.timedelta64(minute * 60, "s").astype("timedelta64[ns]")
                - np.timedelta64(IST_OFFSET_NS, "ns")
            )
            ts.append(utc)
            closes.append(close)
            vols.append(vol)
    t = np.array(ts, dtype="datetime64[ns]")
    c = np.array(closes, dtype=np.float64)
    return OHLCV("X", "5minute", t, c, c, c, c, np.array(vols, dtype=np.int64))


D1, D2 = date(2024, 1, 2), date(2024, 1, 3)


def test_hold_return_hand_worked() -> None:
    # entry close 110, day close 121 -> 121/110 - 1 = 0.10
    s = _series([(D1, [(_OPEN, 100.0, 1), (_ENTRY, 110.0, 1), (_LAST, 121.0, 1)])])
    assert hold_return(s, entry_minute=_ENTRY)[D1] == 121.0 / 110.0 - 1.0


def test_hold_return_no_lookahead_ignores_future_days() -> None:
    """Appending a wild future day must not change day 1's hold return; a leaky exit would."""
    day1 = (D1, [(_OPEN, 100.0, 1), (_ENTRY, 110.0, 1), (_LAST, 121.0, 1)])
    day2_wild = (D2, [(_OPEN, 200.0, 1), (_ENTRY, 300.0, 1), (_LAST, 999.0, 1)])
    full = _series([day1, day2_wild])
    truncated = _series([day1])

    # correct impl: day 1 is invariant to the appended future day
    assert (
        hold_return(full, entry_minute=_ENTRY)[D1]
        == hold_return(truncated, entry_minute=_ENTRY)[D1]
    )

    # teeth: a LEAKY exit (the whole-series last close) is NOT invariant -> the guarantee
    # above is real. day-1 entry close is 110 in both series.
    leaky_full = float(full.close[-1]) / 110.0 - 1.0  # peeks day 2's 999
    leaky_trunc = float(truncated.close[-1]) / 110.0 - 1.0  # day 1's 121
    assert leaky_full != leaky_trunc


def test_hold_return_skips_a_day_without_an_entry_bar() -> None:
    s = _series([(D1, [(_OPEN, 100.0, 1), (_LAST, 121.0, 1)])])  # no 09:45 bar
    assert D1 not in hold_return(s, entry_minute=_ENTRY)


def test_entry_window_value_sums_only_the_morning_window() -> None:
    # traded_value = close*volume: [100*10, 110*20, 121*5] = [1000, 2200, 605];
    # window [open..entry] = the 555 and 585 bars -> 1000 + 2200 = 3200 (excludes 15:25).
    s = _series([(D1, [(_OPEN, 100.0, 10), (_ENTRY, 110.0, 20), (_LAST, 121.0, 5)])])
    assert entry_window_value(s, entry_minute=_ENTRY)[D1] == 3200.0
