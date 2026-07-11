"""Run orchestration: assemble the daily cross-section, book it, net-return it, draw the null.

Kept modular and pure so it is testable on a tiny synthetic universe with a closed-form
answer BEFORE it runs on the cache:

* ``build_symbol_days`` turns one symbol's OHLCV into a per-day record (signal, hold
  return, entry-window value, ATR%, sector, eligibility, circuit-lock, spread).
* ``run_arm`` iterates the trading days shared across symbols: builds the signal book
  (or a DayDropped), net-returns it at both corridor bounds, and draws ``N`` random null
  books through the IDENTICAL execution, net-returning each. A DayDropped null draw is a
  flat book (0.0) — it keeps the per-day null panel rectangular for the benchmark.
* The frozen cost corridor sets each position's round-trip cost from its Corwin-Schultz
  spread and its participation; it is composed, never edited.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

import numpy as np

from xsranker.backtest.pnl import book_net_return
from xsranker.core.types import OHLCV
from xsranker.execution.book import Book, DayDropped
from xsranker.execution.config import CostCorridorConfig, ExecutionConfig
from xsranker.execution.pipeline import SymbolInputs, build_book
from xsranker.execution.spread import corwin_schultz_spread
from xsranker.features.point_in_time import entry_window_value, hold_return
from xsranker.harness.adapter import CostModel, HarnessAdapter
from xsranker.null.panel import build_random_book
from xsranker.signals.spec import (
    SignalArm,
    atr_pct_by_day,
    resample_daily,
    signal_value_by_day,
)


@dataclass(frozen=True, slots=True)
class SymbolDay:
    """Everything one symbol contributes on one day (all point-in-time)."""

    inputs: SymbolInputs  # for selection/sizing (signal, sector, atr, entry value, masks, circuit)
    hold: float  # entry->close hold return
    spread: float  # Corwin-Schultz implied spread (for the cost corridor)


@dataclass(frozen=True, slots=True)
class DayStreams:
    """One arm's per-day net returns under one cost bound: signal + the N null draws."""

    signal_by_day: dict[date, float]
    null_by_day: dict[date, tuple[float, ...]]


def _spread_by_day(series: OHLCV, *, lookback: int = 20) -> dict[date, float]:
    """Point-in-time Corwin-Schultz implied spread per day (a cost input).

    Day D's spread uses the daily high/low of the ``lookback`` days STRICTLY BEFORE D
    (day D's own daily range isn't known at the morning entry instant), so it never
    looks ahead. Needs >= 2 prior days.
    """
    days, highs, lows, _closes = resample_daily(series)
    out: dict[date, float] = {}
    for i in range(2, len(days)):
        lo = max(0, i - lookback)
        out[days[i]] = corwin_schultz_spread(highs[lo:i], lows[lo:i])
    return out


def build_symbol_days(
    symbol: str,
    series: OHLCV,
    *,
    arm: SignalArm,
    entry_minute: int,
    atr_period: int,
    sector: str,
    long_eligible: bool,
    short_eligible: bool,
    circuit_locked_by_day: Mapping[date, bool],
    adapter: HarnessAdapter,
) -> dict[date, SymbolDay]:
    """Precompute one symbol's per-day record from its OHLCV (point-in-time throughout)."""
    signal = signal_value_by_day(arm, series, adapter, atr_period=atr_period)
    holds = hold_return(series, entry_minute=entry_minute)
    values = entry_window_value(series, entry_minute=entry_minute)
    atr = atr_pct_by_day(series, adapter, atr_period=atr_period)
    spreads = _spread_by_day(series)

    out: dict[date, SymbolDay] = {}
    for d in signal:
        # a day contributes only if every point-in-time input it needs exists
        if d not in holds or d not in values or d not in atr or d not in spreads:
            continue
        out[d] = SymbolDay(
            inputs=SymbolInputs(
                symbol=symbol,
                signal=signal[d],
                sector=sector,
                atr=atr[d],
                entry_window_value_inr=values[d],
                long_eligible=long_eligible,
                short_eligible=short_eligible,
                circuit_locked=bool(circuit_locked_by_day.get(d, False)),
            ),
            hold=holds[d],
            spread=spreads[d],
        )
    return out


def _position_costs(
    book: Book,
    by_symbol: Mapping[str, SymbolDay],
    cost_model: CostModel,
    cost_cfg: CostCorridorConfig,
    participation_cap: float,
) -> tuple[dict[str, float], dict[str, float]]:
    """Round-trip cost fraction per held name at both corridor bounds (frozen corridor)."""
    from xsranker.execution.cost import cost_corridor

    opt: dict[str, float] = {}
    pess: dict[str, float] = {}
    for p in (*book.longs, *book.shorts):
        sd = by_symbol[p.symbol]
        participation = min(p.notional_inr / sd.inputs.entry_window_value_inr, participation_cap)
        bounds = cost_corridor(
            cost_model,
            sd.spread,
            notional=p.notional_inr,
            participation=participation,
            participation_cap=participation_cap,
            optimistic_multiplier=cost_cfg.optimistic_spread_multiplier,
            pessimistic_multiplier=cost_cfg.pessimistic_spread_multiplier,
        )
        opt[p.symbol] = bounds.optimistic_fraction
        pess[p.symbol] = bounds.pessimistic_fraction
    return opt, pess


def _book_returns(
    book: Book,
    by_symbol: Mapping[str, SymbolDay],
    cost_model: CostModel,
    cost_cfg: CostCorridorConfig,
    participation_cap: float,
) -> tuple[float, float]:
    """(optimistic, pessimistic) net return of a book, cost applied per position."""
    holds = {s: sd.hold for s, sd in by_symbol.items()}
    opt_cost, pess_cost = _position_costs(book, by_symbol, cost_model, cost_cfg, participation_cap)
    return book_net_return(book, holds, opt_cost), book_net_return(book, holds, pess_cost)


@dataclass(frozen=True, slots=True)
class ArmRun:
    """The raw per-day net-return streams for one arm at both cost bounds + run counters."""

    optimistic: DayStreams
    pessimistic: DayStreams
    trading_days: int
    signal_day_drops: int
    null_draw_day_drops: int
    short_ban_fires: int  # short-ineligible names that were nonetheless shorted (expect 0)


def run_arm(
    days: Sequence[date],
    cross_section: Mapping[date, Sequence[SymbolDay]],
    *,
    adapter: HarnessAdapter,
    exec_cfg: ExecutionConfig,
    cost_cfg: CostCorridorConfig,
    cost_model: CostModel,
    draws_per_day: int,
    rng: np.random.Generator,
) -> ArmRun:
    """Iterate the arm's days: signal book + N null books, each net-returned at both bounds."""
    sig_opt: dict[date, float] = {}
    sig_pess: dict[date, float] = {}
    null_opt: dict[date, tuple[float, ...]] = {}
    null_pess: dict[date, tuple[float, ...]] = {}
    signal_drops = 0
    null_drops = 0
    short_ban_fires = 0

    for d in days:
        panel = list(cross_section.get(d, ()))
        if not panel:
            continue
        by_symbol = {sd.inputs.symbol: sd for sd in panel}
        inputs = [sd.inputs for sd in panel]

        book = build_book(inputs, adapter, exec_cfg)
        if isinstance(book, DayDropped):
            signal_drops += 1
            continue  # not a surviving day; the null is sliced to surviving days only

        o, p = _book_returns(book, by_symbol, cost_model, cost_cfg, exec_cfg.participation_cap)
        sig_opt[d] = o
        sig_pess[d] = p

        # N random null books through the IDENTICAL execution; DayDropped draw -> flat 0.0
        day_null_opt: list[float] = []
        day_null_pess: list[float] = []
        for _ in range(draws_per_day):
            nb = build_random_book(inputs, exec_cfg, rng)
            if isinstance(nb, DayDropped):
                null_drops += 1
                day_null_opt.append(0.0)
                day_null_pess.append(0.0)
                continue
            no, np_ = _book_returns(nb, by_symbol, cost_model, cost_cfg, exec_cfg.participation_cap)
            day_null_opt.append(no)
            day_null_pess.append(np_)
            short_ban_fires += sum(
                1 for pos in nb.shorts if not by_symbol[pos.symbol].inputs.short_eligible
            )
        null_opt[d] = tuple(day_null_opt)
        null_pess[d] = tuple(day_null_pess)

    return ArmRun(
        optimistic=DayStreams(sig_opt, null_opt),
        pessimistic=DayStreams(sig_pess, null_pess),
        trading_days=len(days),
        signal_day_drops=signal_drops,
        null_draw_day_drops=null_drops,
        short_ban_fires=short_ban_fires,
    )
