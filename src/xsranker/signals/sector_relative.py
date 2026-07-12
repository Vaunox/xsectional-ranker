"""Candidate #3 — sector-relative intraday reversal (SR / SR-Z).

The **sector-relative morning move**: a stock's open->entry return minus the **leave-one-out**
equal-weight mean of its same-sector peers' returns -- its *idiosyncratic* divergence from its
sector. Ranked REVERSAL (long the lowest = underperformers expected to catch up, short the highest
= outperformers expected to revert): sector-spread mean-reversion, which accrues intraday.

Cross-sectional (couples same-sector names each day), so it is not computed one symbol at a time.
Point-in-time: the morning return is prefix-invariant and the sector mean is a same-day
cross-section, so appending post-entry bars / future days cannot change a day's value.

* **SR** = morning_return - leave-one-out sector-peer mean.
* **SR-Z** = SR / ATR% (the stock's ATR-20 in return units) -- the magnitude arm.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from datetime import date
from enum import StrEnum

#: Default minimum same-sector peers for a meaningful benchmark (a >=3-name sector).
DEFAULT_MIN_PEERS = 2


class SectorRelativeArm(StrEnum):
    """The two pre-registered arms (both charged; parallel to A / A-Z)."""

    SR = "SR"  # raw sector-relative move
    SR_Z = "SR-Z"  # ÷ ATR% (magnitude-normalised)


def sector_relative_move(
    morning_return: Mapping[str, Mapping[date, float]],
    sector: Mapping[str, str],
    *,
    min_peers: int = DEFAULT_MIN_PEERS,
) -> dict[str, dict[date, float]]:
    """Per day, SR = morning_return - leave-one-out mean of same-sector peers' morning returns.

    A name contributes on a day only if its sector has >= ``min_peers`` OTHER names that day (so the
    leave-one-out mean is over >= ``min_peers`` peers); names in smaller sectors are omitted. The
    stock is always excluded from its own benchmark (leave-one-out), so its move never biases it.
    """
    by_day: dict[date, dict[str, list[tuple[str, float]]]] = defaultdict(lambda: defaultdict(list))
    for sym, series in morning_return.items():
        sec = sector.get(sym)
        if sec is None:
            continue
        for d, val in series.items():
            by_day[d][sec].append((sym, val))
    out: dict[str, dict[date, float]] = {}
    for d, sectors in by_day.items():
        for members in sectors.values():
            n = len(members)
            if n < min_peers + 1:  # need the stock itself + at least min_peers peers
                continue
            total = sum(v for _, v in members)
            for sym, val in members:
                loo_mean = (total - val) / (n - 1)  # leave-one-out sector mean
                out.setdefault(sym, {})[d] = val - loo_mean
    return out


def sector_relative_z(
    sr: Mapping[str, Mapping[date, float]],
    atr_pct: Mapping[str, Mapping[date, float]],
) -> dict[str, dict[date, float]]:
    """SR-Z = SR / ATR% (the move in units of the stock's own normal volatility).

    A (symbol, day) is dropped where ATR% is absent or non-positive -- non-finite names are not
    rankable, exactly like A-Z's ATR-history requirement.
    """
    out: dict[str, dict[date, float]] = {}
    for sym, days in sr.items():
        a = atr_pct.get(sym, {})
        for d, val in days.items():
            av = a.get(d)
            if av is not None and av > 0.0:
                out.setdefault(sym, {})[d] = val / av
    return out
