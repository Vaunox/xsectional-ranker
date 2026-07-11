"""Bid-ask spread estimators from OHLC — NEW Layer-2 code (absent from the pin).

Confirmed not present in the predecessor harness (a grep of ``src/lab`` at the pin
found no Corwin-Schultz / Abdi-Ranaldo), so these are original Layer-2 code with
**hand-computed tests**, not golden reconciliation. They feed the cost corridor's
spread input, which then composes the *frozen* ``round_trip_cost``.

* **Corwin-Schultz (2012)** — proportional spread from consecutive two-day high/low
  ranges. Trends inflate the two-day range and can drive the per-pair estimate
  negative; negatives are floored at 0 (standard convention).
* **Abdi-Ranaldo (2017)** — a close/high/low cross-check estimator.
"""

from __future__ import annotations

import math

import numpy as np

from xsranker.core.types import FloatArray

_K = 3.0 - 2.0 * math.sqrt(2.0)  # 3 - 2*sqrt(2) ≈ 0.1715729


def corwin_schultz_pairwise(high: FloatArray, low: FloatArray) -> FloatArray:
    """Per-consecutive-pair Corwin-Schultz proportional spread (negatives floored at 0)."""
    if high.shape != low.shape or high.shape[0] < 2:
        raise ValueError("need aligned high/low with >= 2 observations")
    h, low_ = high.astype(np.float64), low.astype(np.float64)
    beta = np.log(h[:-1] / low_[:-1]) ** 2 + np.log(h[1:] / low_[1:]) ** 2
    hi2 = np.maximum(h[:-1], h[1:])
    lo2 = np.minimum(low_[:-1], low_[1:])
    gamma = np.log(hi2 / lo2) ** 2
    alpha = (np.sqrt(2.0 * beta) - np.sqrt(beta)) / _K - np.sqrt(gamma / _K)
    spread = 2.0 * (np.exp(alpha) - 1.0) / (1.0 + np.exp(alpha))
    out: FloatArray = np.maximum(spread, 0.0)
    return out


def corwin_schultz_spread(high: FloatArray, low: FloatArray) -> float:
    """Symbol-level Corwin-Schultz proportional spread — the median across pairs (robust)."""
    return float(np.median(corwin_schultz_pairwise(high, low)))


def abdi_ranaldo_spread(high: FloatArray, low: FloatArray, close: FloatArray) -> float:
    """Abdi-Ranaldo (2017) proportional spread from close vs the log mid-range."""
    if not (high.shape == low.shape == close.shape) or high.shape[0] < 2:
        raise ValueError("need aligned high/low/close with >= 2 observations")
    eta = (np.log(high.astype(np.float64)) + np.log(low.astype(np.float64))) / 2.0
    c = np.log(close.astype(np.float64))
    s2 = 4.0 * (c[:-1] - eta[:-1]) * (c[:-1] - eta[1:])
    return float(np.sqrt(max(float(np.mean(s2)), 0.0)))
