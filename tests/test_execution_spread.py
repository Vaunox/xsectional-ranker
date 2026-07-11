"""Corwin-Schultz / Abdi-Ranaldo spread estimators — hand-computed tests (new Layer-2)."""

from __future__ import annotations

import numpy as np
import pytest

from xsranker.execution.spread import (
    abdi_ranaldo_spread,
    corwin_schultz_spread,
)


def test_corwin_schultz_bouncing_case_hand_worked() -> None:
    # H=[101,101], L=[99,99]: single-day and two-day ranges coincide.
    # beta=2*ln(101/99)^2, gamma=ln(101/99)^2 -> alpha=0.02000, S=2(e^a-1)/(1+e^a)=0.02000
    high = np.array([101.0, 101.0])
    low = np.array([99.0, 99.0])
    assert corwin_schultz_spread(high, low) == pytest.approx(0.0200, abs=1e-3)


def test_corwin_schultz_trend_floored_at_zero() -> None:
    # a trend inflates the two-day range -> alpha < 0 -> spread floored at 0
    high = np.array([102.0, 103.0])
    low = np.array([100.0, 101.0])
    assert corwin_schultz_spread(high, low) == 0.0


def test_abdi_ranaldo_nonnegative() -> None:
    high = np.array([101.0, 101.5, 100.8])
    low = np.array([99.0, 99.5, 98.8])
    close = np.array([100.0, 100.5, 99.8])
    assert abdi_ranaldo_spread(high, low, close) >= 0.0
