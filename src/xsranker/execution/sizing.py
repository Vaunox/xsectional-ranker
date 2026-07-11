"""Risk-parity (inverse-vol / inverse-ATR) sizing — mandatory hygiene (Concession #5).

Each name is sized to contribute EQUAL RISK within its leg: weight ∝ 1/ATR, normalized
so a leg's weights sum to 1. Equal-*dollar* weighting is structurally FORBIDDEN — it
hands the P&L to the highest-variance name and measures idiosyncratic noise, not
ranking skill. Gap *magnitude* is tested in the signal (A-Z), never the sizing.
"""

from __future__ import annotations

from collections.abc import Mapping


def risk_parity_weights(atr_by_symbol: Mapping[str, float]) -> dict[str, float]:
    """Inverse-ATR weights within a leg, normalized to sum to 1.

    A name with non-positive or non-finite ATR cannot be risk-sized and is excluded
    (fail closed — never rank/size a name whose volatility you cannot measure).
    """
    inverse = {s: 1.0 / a for s, a in atr_by_symbol.items() if a > 0.0 and a == a}
    total = sum(inverse.values())
    if total <= 0.0:
        raise ValueError("no name has a positive ATR; cannot risk-parity size")
    return {s: w / total for s, w in inverse.items()}
