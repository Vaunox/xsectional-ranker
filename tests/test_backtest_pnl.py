"""Book -> net-return engine — hand-worked teeth (the sign-error / wrong-notional minefield).

Numbers are checkable by hand. The short-leg sign is pinned two ways (a flipped sign
must fail); a uniform common-factor move must cancel to ~0 (market-neutrality); the
pessimistic cost bound must return strictly less than the optimistic.
"""

from __future__ import annotations

import pytest

from xsranker.backtest.pnl import book_net_return
from xsranker.execution.book import Book, Position, Side

_G = 1_000_000.0


def _pos(symbol: str, side: Side, weight: float) -> Position:
    return Position(symbol, side, "IT", weight, weight * _G)


def _book(longs: list[tuple[str, float]], shorts: list[tuple[str, float]]) -> Book:
    return Book(
        longs=tuple(_pos(s, Side.LONG, w) for s, w in longs),
        shorts=tuple(_pos(s, Side.SHORT, w) for s, w in shorts),
        gross_inr=_G,
    )


# Longs rise, shorts fall -> the book profits.
_BOOK = _book([("L1", 0.5), ("L2", 0.5)], [("S1", 0.5), ("S2", 0.5)])
_HOLDS = {"L1": 0.02, "L2": 0.04, "S1": -0.03, "S2": -0.01}
_NO_COST = dict.fromkeys(_HOLDS, 0.0)


def test_hand_worked_profit() -> None:
    # long_ret = .5*.02 + .5*.04 = .03 ; short_ret = .5*(-.03)+.5*(-.01) = -.02
    # net = long_ret - short_ret = .03 - (-.02) = .05
    assert book_net_return(_BOOK, _HOLDS, _NO_COST) == pytest.approx(0.05)


def test_short_leg_sign_is_correct() -> None:
    # A flipped short sign would compute long_ret + short_ret = .03 + (-.02) = .01.
    # Pinning 0.05 (not 0.01) is what catches a sign error in the short leg.
    net = book_net_return(_BOOK, _HOLDS, _NO_COST)
    assert net == pytest.approx(0.05)
    assert net != pytest.approx(0.01)


def test_uniform_move_is_market_neutral() -> None:
    # A common-factor move (every name +3%) cancels in the spread -> ~0 before cost.
    uniform = dict.fromkeys(_HOLDS, 0.03)
    assert book_net_return(_BOOK, uniform, _NO_COST) == pytest.approx(0.0)


def test_cost_subtracts_on_both_legs_and_pessimistic_is_worse() -> None:
    # neutral holds so only cost remains: net = -(Σ_long w*c + Σ_short w*c)
    uniform = dict.fromkeys(_HOLDS, 0.0)
    opt = dict.fromkeys(_HOLDS, 0.001)
    pess = dict.fromkeys(_HOLDS, 0.003)
    net_opt = book_net_return(_BOOK, uniform, opt)
    net_pess = book_net_return(_BOOK, uniform, pess)
    assert net_opt == pytest.approx(-0.002)  # 0.5*.001*2 legs *2 names... = .001(long)+.001(short)
    assert net_pess == pytest.approx(-0.006)
    assert net_pess < net_opt  # the pessimistic corridor bound is strictly worse


def test_missing_hold_or_cost_fails_closed() -> None:
    with pytest.raises(KeyError):
        book_net_return(_BOOK, {"L1": 0.02, "L2": 0.04, "S1": -0.03}, _NO_COST)  # S2 missing
    with pytest.raises(KeyError):
        book_net_return(_BOOK, _HOLDS, {"L1": 0.0})  # costs missing
