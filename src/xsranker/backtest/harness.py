"""Run orchestration: assemble the daily cross-section, book it, net-return it, draw the null.

Kept modular and pure so it is testable on a tiny synthetic universe with a closed-form
answer BEFORE it runs on the cache:

* ``build_symbol_days`` turns one symbol's OHLCV into a per-day record (signal, hold
  return, entry-window value, ATR%, sector, eligibility, circuit-lock, spread).
* ``run_arm`` iterates the trading days shared across symbols: builds the signal book
  (or a DayDropped), net-returns it at both corridor bounds, and draws ``N`` random null
  books through the IDENTICAL execution, net-returning each. A DayDropped null draw is a
  flat book (0.0) — it keeps the per-day null panel rectangular for the benchmark.
* The frozen cost corridor sets each position's round-trip cost. In the live FIXED_SPREAD mode
  it is size-aware statutory fees (charged at the ₹10k per-name DEPLOYMENT notional, not the
  liquidity-max book notional) + a fixed NSE-anchored spread; in CS mode (regen) it is the
  Corwin-Schultz spread + participation impact. It is composed, never edited.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

import numpy as np

from xsranker.backtest.pnl import book_net_return
from xsranker.core.logging import get_logger
from xsranker.core.types import OHLCV
from xsranker.execution.book import Book, DayDropped
from xsranker.execution.config import FIXED_SPREAD, CostCorridorConfig, ExecutionConfig
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

_log = get_logger("backtest.harness")


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
    arm: SignalArm | None = None,
    signal_override: Mapping[date, float] | None = None,
    entry_minute: int,
    atr_period: int,
    sector: str,
    long_eligible: bool,
    short_eligible: bool,
    circuit_locked_by_day: Mapping[date, bool],
    adapter: HarnessAdapter,
    compute_spread: bool = True,
) -> dict[date, SymbolDay]:
    """Precompute one symbol's per-day record from its OHLCV (point-in-time throughout).

    The ranking signal is either computed from ``arm`` (gap A/A-Z) or injected via
    ``signal_override`` (a precomputed per-day value — used for V_resid, whose cross-sectional
    residual cannot be computed one symbol at a time). Exactly one must be given.

    ``compute_spread`` computes the Corwin-Schultz spread (``SymbolDay.spread``) — needed ONLY by
    the historical CS corridor (the candidate-#1 ledger regen). The live FIXED_SPREAD corridor
    ignores it, so candidate #2 passes ``compute_spread=False`` and the now-dead CS estimate is
    never computed (``spread`` = 0.0).
    """
    if signal_override is not None:
        signal: Mapping[date, float] = signal_override
    elif arm is not None:
        signal = signal_value_by_day(arm, series, adapter, atr_period=atr_period)
    else:
        raise ValueError("build_symbol_days needs either arm or signal_override")
    holds = hold_return(series, entry_minute=entry_minute)
    values = entry_window_value(series, entry_minute=entry_minute)
    atr = atr_pct_by_day(series, adapter, atr_period=atr_period)
    spreads = _spread_by_day(series) if compute_spread else {}

    out: dict[date, SymbolDay] = {}
    for d in signal:
        # a day contributes only if every point-in-time input it needs exists
        if d not in holds or d not in values or d not in atr:
            continue
        if compute_spread and d not in spreads:
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
            spread=spreads[d] if compute_spread else 0.0,
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
        # FIXED_SPREAD (live): charge the size-aware fees at the ACTUAL per-name deployment notional
        # (deployment capital / (2*k)), not the liquidity-max book notional the truncation sizes to.
        # The fee model is size-dependent via the per-order brokerage cap, so a small deployment pays
        # materially more (bps). CS mode (historical regen) keeps the book notional for stream fidelity.
        fee_notional = (
            cost_cfg.deployment_notional_inr if cost_cfg.mode == FIXED_SPREAD else p.notional_inr
        )
        bounds = cost_corridor(
            cost_model,
            cost_cfg,
            spread=sd.spread,
            notional=fee_notional,
            participation=participation,
            participation_cap=participation_cap,
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
class NullHealth:
    """Aggregate telemetry for the null's rejection-sampling loop (observability, not a gate).

    The early-warning for a regression in ``build_random_book`` — the loop whose silent failure
    once zero-padded ~half the draws and manufactured a false KILL. A healthy null accepts almost
    every draw first try (``mean_attempts`` ≈ 1, ``ceiling_hits`` = 0); a rising rejection rate or
    ceiling hits is the tell that the feasibility of a floor-clearing random book is degrading.
    """

    total_draws: int
    rejections: int  # draws that needed > 1 attempt
    mean_attempts: float
    max_attempts: int
    ceiling_hits: int  # draws that exhausted _MAX_SELECTION_ATTEMPTS -> DayDropped

    @property
    def rejection_rate(self) -> float:
        """Fraction of draws that needed more than one attempt."""
        return self.rejections / self.total_draws if self.total_draws else 0.0


@dataclass(frozen=True, slots=True)
class ArmRun:
    """The raw per-day net-return streams for one arm at both cost bounds + run counters."""

    optimistic: DayStreams
    pessimistic: DayStreams
    trading_days: int
    signal_day_drops: int
    null_draw_day_drops: int
    short_ban_fires: int  # short-ineligible names that were nonetheless shorted (expect 0)
    null_health: NullHealth


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
    continuation: bool = False,
) -> ArmRun:
    """Iterate the arm's days: signal book + N null books, each net-returned at both bounds.

    ``continuation`` is passed to ``build_book`` for the leg direction (V_resid: LONG the highest
    signal). The null is direction-agnostic (random), so only the SIGNAL book flips.
    """
    sig_opt: dict[date, float] = {}
    sig_pess: dict[date, float] = {}
    null_opt: dict[date, tuple[float, ...]] = {}
    null_pess: dict[date, tuple[float, ...]] = {}
    signal_drops = 0
    null_drops = 0
    short_ban_fires = 0
    null_total = 0
    null_attempts_sum = 0
    null_attempts_max = 0
    null_rejections = 0

    for d in days:
        panel = list(cross_section.get(d, ()))
        if not panel:
            continue
        by_symbol = {sd.inputs.symbol: sd for sd in panel}
        inputs = [sd.inputs for sd in panel]

        book = build_book(inputs, adapter, exec_cfg, continuation=continuation)
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
            nb, attempts = build_random_book(inputs, exec_cfg, rng)
            null_total += 1
            null_attempts_sum += attempts
            null_attempts_max = max(null_attempts_max, attempts)
            if attempts > 1:
                null_rejections += 1
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

    null_health = NullHealth(
        total_draws=null_total,
        rejections=null_rejections,
        mean_attempts=(null_attempts_sum / null_total) if null_total else 0.0,
        max_attempts=null_attempts_max,
        ceiling_hits=null_drops,  # a DayDropped draw exhausted the retry ceiling
    )
    # INFO aggregate (the per-attempt day_dropped spam is suppressed): the observable
    # early-warning for a regression in the null's rejection loop.
    _log.info(
        "null_health",
        total_draws=null_health.total_draws,
        rejections=null_health.rejections,
        rejection_rate=round(null_health.rejection_rate, 6),
        mean_attempts=round(null_health.mean_attempts, 4),
        max_attempts=null_health.max_attempts,
        ceiling_hits=null_health.ceiling_hits,
    )
    return ArmRun(
        optimistic=DayStreams(sig_opt, null_opt),
        pessimistic=DayStreams(sig_pess, null_pess),
        trading_days=len(days),
        signal_day_drops=signal_drops,
        null_draw_day_drops=null_drops,
        short_ban_fires=short_ban_fires,
        null_health=null_health,
    )
