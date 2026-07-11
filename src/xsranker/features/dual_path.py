"""Dual-path harness — the train/serve-skew tripwire.

A trailing rolling statistic computed two ways that MUST agree bit-for-bit:

* **vectorized** — the whole series at once (the backfill path);
* **incremental** — one bar at a time, carrying only past state (the serve path).

Any divergence is train/serve skew (a vectorized backfill computing a feature
differently from the live incremental path), which the suite catches. The window is
TRAILING and EXCLUDES the current element, so the feature is also leakage-safe by
construction (uses only bars strictly before ``i``).
"""

from __future__ import annotations

from collections import deque

import numpy as np

from xsranker.core.types import FloatArray


def trailing_mean_vectorized(x: FloatArray, *, window: int) -> FloatArray:
    """``out[i] = mean(x[max(0, i-window) : i])`` (trailing, excludes ``i``; nan if empty)."""
    if window < 1:
        raise ValueError("window must be >= 1")
    n = x.shape[0]
    out = np.full(n, np.nan, dtype=np.float64)
    csum = np.concatenate([[0.0], np.cumsum(x)])
    for i in range(1, n):
        lo = max(0, i - window)
        count = i - lo
        out[i] = (csum[i] - csum[lo]) / count
    return out


def trailing_mean_incremental(x: FloatArray, *, window: int) -> FloatArray:
    """Same trailing mean, computed bar-by-bar carrying only a bounded past window."""
    if window < 1:
        raise ValueError("window must be >= 1")
    n = x.shape[0]
    out = np.full(n, np.nan, dtype=np.float64)
    past: deque[float] = deque(maxlen=window)
    for i in range(n):
        if past:
            out[i] = sum(past) / len(past)
        past.append(float(x[i]))  # only AFTER emitting -> excludes current
    return out
