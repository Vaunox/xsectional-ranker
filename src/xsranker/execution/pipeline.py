"""The FROZEN order-of-operations — one explicit pipeline (Deep Dive 02).

    dual masks -> circuit filter -> rank within mask -> ceil(k/2) sector cap
      -> risk-parity sizing -> Execution-Aware truncation -> gross-floor day-drop

Each step is a separately-tested function; this module wires them in the one frozen
order. The Global Null Panel (Step 3) reuses THIS pipeline unchanged, swapping only
the selection step (ranked -> random) — which is what makes the symmetric-execution
proof mechanical.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from xsranker.execution.book import Book, Candidate, DayDropped, Side
from xsranker.execution.config import ExecutionConfig
from xsranker.execution.sector_cap import apply_sector_cap
from xsranker.execution.sizing import risk_parity_weights
from xsranker.execution.truncation import truncate
from xsranker.harness.adapter import HarnessAdapter
from xsranker.signals.ranker import rank_panel


@dataclass(frozen=True, slots=True)
class SymbolInputs:
    """Everything the pipeline needs for one symbol on one day (all point-in-time)."""

    symbol: str
    signal: float  # the ranking feature value (gap% or gap%/ATR%)
    sector: str
    atr: float  # for risk-parity (inverse-ATR) sizing
    entry_window_value_inr: float  # traded value in the entry window (for the 1% cap)
    long_eligible: bool
    short_eligible: bool
    circuit_locked: bool


def _select(
    ranked_desc: list[str], by_symbol: dict[str, SymbolInputs], cfg: ExecutionConfig
) -> list[str]:
    pairs = [(s, by_symbol[s].sector) for s in ranked_desc]
    return apply_sector_cap(pairs, k=cfg.k_per_leg, per_sector_cap=cfg.sector_cap)


def eligible_pools(
    panel: Sequence[SymbolInputs],
) -> tuple[dict[str, float], dict[str, float], dict[str, SymbolInputs]]:
    """Steps 1-2 (dual masks + circuit filter) -> the per-leg eligible pools.

    Shared by BOTH the signal and the null: a circuit-locked or ineligible name is
    excluded from both identically. Only step 3 (selection) differs downstream.
    """
    by_symbol = {s.symbol: s for s in panel}
    tradeable = [s for s in panel if not s.circuit_locked]
    short_pool = {s.symbol: s.signal for s in tradeable if s.short_eligible}
    long_pool = {s.symbol: s.signal for s in tradeable if s.long_eligible}
    return long_pool, short_pool, by_symbol


def finalize(
    long_ordered: list[str],
    short_ordered: list[str],
    by_symbol: dict[str, SymbolInputs],
    cfg: ExecutionConfig,
) -> Book | DayDropped:
    """Steps 4-7 (sector cap -> risk-parity sizing -> truncation -> gross-floor drop).

    The SHARED execution path. Given the SAME ordered candidate lists it produces the
    SAME book whether they came from the ranked signal or a random draw — that is what
    makes 'beats random' measure selection skill and nothing else.
    """
    short_syms = _select(short_ordered, by_symbol, cfg)
    long_syms = [s for s in _select(long_ordered, by_symbol, cfg) if s not in set(short_syms)]
    if len(short_syms) < cfg.k_per_leg or len(long_syms) < cfg.k_per_leg:
        return DayDropped("insufficient eligible names after masks/circuit/sector cap")
    short_syms, long_syms = short_syms[: cfg.k_per_leg], long_syms[: cfg.k_per_leg]

    long_w = risk_parity_weights({s: by_symbol[s].atr for s in long_syms})
    short_w = risk_parity_weights({s: by_symbol[s].atr for s in short_syms})

    def _cands(syms: list[str], weights: dict[str, float], side: Side) -> list[Candidate]:
        return [
            Candidate(
                s,
                side,
                by_symbol[s].sector,
                weights[s],
                cfg.participation_cap * by_symbol[s].entry_window_value_inr,
            )
            for s in syms
        ]

    return truncate(
        _cands(long_syms, long_w, Side.LONG),
        _cands(short_syms, short_w, Side.SHORT),
        gross_floor_inr=cfg.gross_floor_inr,
    )


def build_book(
    panel: Sequence[SymbolInputs],
    adapter: HarnessAdapter,
    cfg: ExecutionConfig,
    *,
    continuation: bool = False,
) -> Book | DayDropped:
    """Signal book: eligible pools -> rank by the signal (step 3) -> shared finalize.

    ``continuation`` sets the leg direction. REVERSAL (default, candidate #1 gap): LONG the
    lowest-signal names (biggest gap-downs), SHORT the highest (gap-ups). CONTINUATION (V_resid):
    LONG the **highest**-signal names (most residual net-buying flow), SHORT the lowest. Only the
    long/short ordering flips; the shared ``finalize`` and the null are unchanged.
    """
    long_pool, short_pool, by_symbol = eligible_pools(panel)
    long_asc = rank_panel(long_pool, adapter)  # ascending signal
    short_asc = rank_panel(short_pool, adapter)
    if continuation:
        long_ordered = list(reversed(long_asc))  # descending: highest signal first (long the top)
        short_ordered = short_asc  # ascending: lowest signal first (short the bottom)
    else:
        long_ordered = long_asc  # ascending: lowest signal first (long the biggest gap-downs)
        short_ordered = list(reversed(short_asc))  # descending: highest first (short the gap-ups)
    return finalize(long_ordered, short_ordered, by_symbol, cfg)
