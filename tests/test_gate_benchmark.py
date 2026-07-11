"""Beat-random-percentile — the ONE new gate criterion, hand-computed teeth.

Correctly PASSES a signal that clears the pre-registered null percentile and FAILS one
that does not; the threshold binds. Also pins the excess-over-null-median stream (the
operator-ruled quantity that feeds the imported CPCV/DSR/PBO).
"""

from __future__ import annotations

from datetime import date, timedelta

from xsranker.gate.benchmark import beat_random_percentile, excess_over_null_median


def _days(n: int) -> list[date]:
    return [date(2024, 1, 1) + timedelta(days=i) for i in range(n)]


def test_excess_over_null_median_is_net_minus_daily_median() -> None:
    days = _days(3)
    signal = {days[0]: 1.0, days[1]: 2.0, days[2]: 3.0}
    # per-day medians: 0.0, 2.0, 20.0  ->  excess: 1.0, 0.0, -17.0
    null = {days[0]: [0.0, 0.0, 0.0], days[1]: [1.0, 2.0, 3.0], days[2]: [10.0, 20.0, 30.0]}
    assert excess_over_null_median(signal, null) == [1.0, 0.0, -17.0]


def _ramp_null(days: list[date], n_draws: int = 100) -> dict[date, list[float]]:
    # draw j == j on every day, so null aggregate (mean over days) of strategy j is j:
    # the null aggregate distribution is exactly {0, 1, ..., n_draws-1}.
    return {d: [float(j) for j in range(n_draws)] for d in days}


def test_signal_above_the_bar_passes() -> None:
    days = _days(4)
    null = _ramp_null(days)
    # signal aggregate 95.5 beats draws 0..95 -> 96th percentile -> clears the 95th.
    res = beat_random_percentile(dict.fromkeys(days, 95.5), null, threshold=95.0)
    assert res.beat_percentile == 96.0
    assert res.passed


def test_signal_at_the_null_median_fails_the_95th() -> None:
    days = _days(4)
    null = _ramp_null(days)
    # aggregate 49.5 beats 0..49 -> 50th percentile -> nowhere near the 95th.
    res = beat_random_percentile(dict.fromkeys(days, 49.5), null, threshold=95.0)
    assert res.beat_percentile == 50.0
    assert not res.passed


def test_threshold_binds() -> None:
    days = _days(4)
    null = _ramp_null(days)
    # aggregate 91.5 -> 92nd percentile: clears the 90th bar, fails the 95th.
    signal = dict.fromkeys(days, 91.5)
    assert beat_random_percentile(signal, null, threshold=90.0).passed
    assert not beat_random_percentile(signal, null, threshold=95.0).passed


def test_percentile_is_shift_invariant_between_raw_and_excess() -> None:
    # The rank within the null is unchanged by subtracting the null median, so the
    # benchmark's pass/fail is identical whether read on raw net or on excess.
    days = _days(4)
    null = {d: [float(j) for j in range(100)] for d in days}  # median 49.5 each day
    res = beat_random_percentile(dict.fromkeys(days, 80.0), null, threshold=95.0)
    assert res.beat_percentile == 80.0  # beats 0..79
    # excess-over-median = 80 - 49.5 = 30.5 each day (a pure shift; rank unaffected)
    assert all(abs(e - 30.5) < 1e-9 for e in res.excess_stream)
