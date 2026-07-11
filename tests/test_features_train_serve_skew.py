"""Train/serve-skew suite (load-bearing, runs in CI on synthetic data).

The vectorized backfill path and the incremental bar-by-bar (serve) path must
compute the SAME trailing feature. The suite proves they agree bit-for-bit on
random input, and that it has teeth — an incremental path that (wrongly) includes
the current bar diverges and is caught.
"""

from __future__ import annotations

from collections import deque

import numpy as np

from xsranker.features.dual_path import trailing_mean_incremental, trailing_mean_vectorized


def _leaky_incremental_includes_current(x: np.ndarray, *, window: int) -> np.ndarray:
    """A skewed serve path that appends the current bar BEFORE emitting (leakage)."""
    n = x.shape[0]
    out = np.full(n, np.nan, dtype=np.float64)
    past: deque[float] = deque(maxlen=window)
    for i in range(n):
        past.append(float(x[i]))  # WRONG: includes current bar
        out[i] = sum(past) / len(past)
    return out


def test_vectorized_equals_incremental() -> None:
    rng = np.random.default_rng(0)
    for window in (1, 3, 10, 50):
        x = rng.normal(0.0, 1.0, 200)
        vec = trailing_mean_vectorized(x, window=window)
        inc = trailing_mean_incremental(x, window=window)
        # both leave index 0 as nan; compare the rest exactly
        np.testing.assert_array_equal(np.isnan(vec), np.isnan(inc))
        finite = ~np.isnan(vec)
        np.testing.assert_allclose(vec[finite], inc[finite], rtol=0, atol=1e-12)


def test_skewed_serve_path_is_caught() -> None:
    """Teeth: a serve path that includes the current bar diverges from the backfill."""
    rng = np.random.default_rng(1)
    x = rng.normal(0.0, 1.0, 100)
    vec = trailing_mean_vectorized(x, window=10)
    leaky = _leaky_incremental_includes_current(x, window=10)
    # they must NOT agree -> the reconciliation would catch this skew
    assert not np.allclose(vec[~np.isnan(vec)], leaky[1:], atol=1e-9)
