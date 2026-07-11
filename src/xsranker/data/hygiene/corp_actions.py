"""Corporate-action back-adjustment (original Layer-1 code, not vendored).

Back-adjusts a raw OHLCV series for splits/bonuses/dividends so prices form a
continuous series across ex-dates. Raw is never mutated — the adjusted series is a
derived product, recomputed from raw + the action list, so the job is idempotent.

**Phase-1 reality:** the inherited Kite cache is ALREADY split/bonus back-adjusted
(empirically verified), and cash-dividend data is out-of-scope acquisition deferred
to Phase 4. So Phase 1 runs this with an EMPTY action list — adjusted == raw — and
the machinery is exercised for correctness with synthetic actions in tests. The
STAMP that rides every Phase-1 artifact: *split/bonus-adjusted; cash dividends
unadjusted — bounded ex-div residual accepted for the survivor upper bound;
dividend adjustment deferred to Phase 4.*

Convention: each action has a ``price_factor`` (<1 pushes pre-ex prices down onto
the post-ex scale) and a ``volume_factor``. A bar is scaled by the product of the
factors of every action whose ex-date is strictly AFTER the bar's IST trading date.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

import numpy as np

from xsranker.core.logging import get_logger
from xsranker.core.types import OHLCV

_log = get_logger("data.hygiene.corp_actions")

#: The stamp every Phase-1 artifact carries about corp-action handling.
PHASE1_ADJUSTMENT_STAMP = (
    "split/bonus-adjusted; cash dividends unadjusted — bounded ex-div residual "
    "accepted for the survivor upper bound; dividend adjustment deferred to Phase 4"
)


@dataclass(frozen=True, slots=True)
class CorporateAction:
    """An ex-date plus price/volume back-adjustment factors."""

    ex_date: date
    price_factor: float
    volume_factor: float = 1.0

    @classmethod
    def split(cls, ex_date: date, ratio: float) -> CorporateAction:
        """A ``ratio``-for-1 split (``ratio=10`` for a 10:1 split): price /= ratio."""
        if ratio <= 0:
            raise ValueError(f"split ratio must be positive; got {ratio}")
        return cls(ex_date=ex_date, price_factor=1.0 / ratio, volume_factor=ratio)

    @classmethod
    def bonus(cls, ex_date: date, held: int, received: int) -> CorporateAction:
        """A bonus of ``received`` new shares per ``held`` held."""
        if held <= 0 or received < 0:
            raise ValueError("bonus needs held > 0 and received >= 0")
        ratio = (held + received) / held
        return cls(ex_date=ex_date, price_factor=1.0 / ratio, volume_factor=ratio)

    @classmethod
    def dividend(cls, ex_date: date, dividend: float, reference_close: float) -> CorporateAction:
        """A cash dividend of ``dividend`` against the pre-ex ``reference_close``."""
        if reference_close <= 0:
            raise ValueError("reference_close must be positive")
        return cls(ex_date=ex_date, price_factor=1.0 - dividend / reference_close)


def adjust(ohlcv: OHLCV, actions: Sequence[CorporateAction]) -> OHLCV:
    """Return ``ohlcv`` back-adjusted for ``actions`` (input is not mutated).

    With no actions this returns an equivalent series (identity), which is the
    Phase-1 path over the already-Kite-adjusted cache.
    """
    n = len(ohlcv)
    price_factor = np.ones(n, dtype=np.float64)
    volume_factor = np.ones(n, dtype=np.float64)
    bar_dates = ohlcv.ist_dates()
    for action in actions:
        pre_ex = bar_dates < np.datetime64(action.ex_date, "D")
        price_factor[pre_ex] *= action.price_factor
        volume_factor[pre_ex] *= action.volume_factor
    adjusted = OHLCV(
        symbol=ohlcv.symbol,
        interval=ohlcv.interval,
        timestamp=ohlcv.timestamp,
        open=ohlcv.open * price_factor,
        high=ohlcv.high * price_factor,
        low=ohlcv.low * price_factor,
        close=ohlcv.close * price_factor,
        volume=np.rint(ohlcv.volume.astype(np.float64) * volume_factor).astype(np.int64),
    )
    if actions:
        _log.info("candles_adjusted", symbol=ohlcv.symbol, bars=n, actions=len(actions))
    return adjusted
