"""The Global Null Panel generator (seeded, reproducible, versioned, sliceable).

The null draws random long-k/short-k books under constraints IDENTICAL to the signal book
(``build_book``): same eligibility, ⌈k/2⌉ sector cap, disjoint legs, risk-parity sizing,
Execution-Aware truncation, and the SAME gross floor. The ONLY difference is ranked-vs-
random selection, so "beats random" measures selection skill and nothing else.

**Feasible, floor-clearing draw on every retained day (fixed + corrected 2026-07-11).**
A naive shuffle-then-``finalize`` drew an *infeasible* pair (< k per leg after the cap +
disjoint exclusion) on ~half of draws and zero-padded them with ``0.0`` — which pulled the
null benchmark UP toward 0 (0 beats a real random book, which pays cost with worthless
selection) and manufactured a false KILL. The selection is now CONSTRUCTED
(``_draw_selection``) and re-drawn until it forms a valid book that CLEARS THE SAME FLOOR
the signal must clear. No relaxation (an earlier fix wrongly set the null floor to 0, which
leaked thin sub-floor books and inflated the signal's alpha), no zero-pad. ``DayDropped`` is
returned only when no floor-clearing valid book can be drawn at all — a genuinely infeasible
day the signal shares (shared day-drop). Sanity tell for the whole error class: the true
null median net return must be slightly NEGATIVE (~ -15 to -25 bps).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

import numpy as np

from xsranker.core.logging import get_logger
from xsranker.execution.book import Book, DayDropped
from xsranker.execution.config import ExecutionConfig
from xsranker.execution.pipeline import SymbolInputs, eligible_pools, finalize

_log = get_logger("null.panel")

DrawOutcome = Book | DayDropped

#: Fresh random draws tried before a day is declared genuinely infeasible for the null. A
#: floor-clearing random book is the common case (most random books clear the ₹-floor), so
#: this succeeds in ~1 draw; it only backstops thin days a floor-clearing book barely exists.
_MAX_SELECTION_ATTEMPTS = 128


def _shuffled(symbols: list[str], rng: np.random.Generator) -> list[str]:
    """A seeded random permutation of ``symbols`` (the null's selection order)."""
    perm = rng.permutation(len(symbols))
    return [symbols[int(i)] for i in perm]


def _draw_selection(
    long_pool: set[str],
    short_pool: set[str],
    by_symbol: dict[str, SymbolInputs],
    cfg: ExecutionConfig,
    rng: np.random.Generator,
) -> tuple[list[str], list[str]] | None:
    """One random disjoint k-long / k-short selection under the ⌈k/2⌉ sector cap.

    Shuffled eligible names are assigned greedily to whichever leg can still take them
    (disjoint by construction; ≤ ``cfg.sector_cap`` per sector per leg; ``k`` per leg), the
    leg chosen at random when both are open. Returns ``None`` if this shuffle cannot fill
    both legs (the caller re-draws).
    """
    k, cap = cfg.k_per_leg, cfg.sector_cap
    longs: list[str] = []
    shorts: list[str] = []
    long_sec: dict[str, int] = {}
    short_sec: dict[str, int] = {}
    for s in _shuffled(list(long_pool | short_pool), rng):
        if len(longs) == k and len(shorts) == k:
            break
        sector = by_symbol[s].sector
        can_long = s in long_pool and len(longs) < k and long_sec.get(sector, 0) < cap
        can_short = s in short_pool and len(shorts) < k and short_sec.get(sector, 0) < cap
        if can_long and (not can_short or rng.random() < 0.5):
            longs.append(s)
            long_sec[sector] = long_sec.get(sector, 0) + 1
        elif can_short:
            shorts.append(s)
            short_sec[sector] = short_sec.get(sector, 0) + 1
    if len(longs) == k and len(shorts) == k:
        return longs, shorts
    return None


def build_random_book(
    panel: Sequence[SymbolInputs], cfg: ExecutionConfig, rng: np.random.Generator
) -> DrawOutcome:
    """One random draw: a valid, FLOOR-CLEARING, disjoint k-long/k-short capped book.

    Every constraint is IDENTICAL to the signal book — same eligibility, ⌈k/2⌉ sector cap,
    disjoint legs, risk-parity sizing, Execution-Aware truncation, and the SAME gross floor
    (``cfg``, unmodified). Only the selection differs (random vs ranked). A draw that is
    infeasible OR below the floor is rejected and re-drawn; ``DayDropped`` is returned only
    when no floor-clearing valid book can be drawn at all — a genuinely infeasible day the
    signal shares (shared day-drop, never a zero-pad).
    """
    long_pool, short_pool, by_symbol = eligible_pools(panel)
    lp, sp = set(long_pool), set(short_pool)
    for _ in range(_MAX_SELECTION_ATTEMPTS):
        selection = _draw_selection(lp, sp, by_symbol, cfg, rng)
        if selection is None:
            continue
        longs, shorts = selection
        book = finalize(longs, shorts, by_symbol, cfg)  # the SAME floor the signal clears
        if isinstance(book, Book):
            return book
    return DayDropped("no feasible floor-clearing random capped disjoint book")


@dataclass(frozen=True, slots=True)
class NullPanel:
    """An immutable, versioned per-day distribution of N random book draws."""

    version: str
    seed: int
    draws_per_day: int
    draws: dict[date, tuple[DrawOutcome, ...]]

    def days(self) -> tuple[date, ...]:
        """The days covered, ascending."""
        return tuple(sorted(self.draws))

    def slice_to(self, surviving_days: set[date]) -> NullPanel:
        """Slice to the signal's surviving days (shared day-drop by construction)."""
        return NullPanel(
            version=self.version,
            seed=self.seed,
            draws_per_day=self.draws_per_day,
            draws={d: v for d, v in self.draws.items() if d in surviving_days},
        )


def generate_null_panel(
    day_panels: Mapping[date, Sequence[SymbolInputs]],
    cfg: ExecutionConfig,
    *,
    seed: int,
    draws_per_day: int,
    version: str = "v1",
) -> NullPanel:
    """Generate ONCE globally: N random books per day, from a single seeded RNG stream.

    Two runs with the same seed produce a byte-identical panel (the RNG stream is
    consumed deterministically, day by day, draw by draw).
    """
    rng = np.random.default_rng(seed)
    draws: dict[date, tuple[DrawOutcome, ...]] = {}
    for day in sorted(day_panels):
        draws[day] = tuple(
            build_random_book(day_panels[day], cfg, rng) for _ in range(draws_per_day)
        )
    _log.info("null_panel_generated", days=len(draws), draws_per_day=draws_per_day, seed=seed)
    return NullPanel(version=version, seed=seed, draws_per_day=draws_per_day, draws=draws)
