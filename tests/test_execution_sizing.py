"""Risk-parity (inverse-ATR) sizing tests."""

from __future__ import annotations

import pytest

from xsranker.execution.sizing import risk_parity_weights


def test_inverse_atr_weights_sum_to_one() -> None:
    w = risk_parity_weights({"A": 1.0, "B": 2.0})  # inverse 1.0, 0.5 -> 2/3, 1/3
    assert w["A"] == pytest.approx(2 / 3) and w["B"] == pytest.approx(1 / 3)
    assert sum(w.values()) == pytest.approx(1.0)


def test_equal_atr_gives_equal_weight() -> None:
    w = risk_parity_weights({"A": 2.0, "B": 2.0, "C": 2.0})
    assert all(v == pytest.approx(1 / 3) for v in w.values())


def test_nonpositive_atr_cannot_be_sized() -> None:
    with pytest.raises(ValueError, match="positive ATR"):
        risk_parity_weights({"A": 0.0, "B": float("nan")})
