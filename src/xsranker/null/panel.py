"""The Global Null Panel generator (seeded, reproducible, versioned, sliceable).

The null draws random long-k/short-k books through the SAME ``eligible_pools`` ->
(random selection) -> ``finalize`` path the signal uses (``build_book``). Only the
selection step differs, so the null endures every liquidity reality the signal does
(masks, circuit, sector cap, caps, truncation, gross-floor day-drop) — which is what
makes "beats random" measure selection skill and not fillability.
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


def _shuffled(symbols: list[str], rng: np.random.Generator) -> list[str]:
    """A seeded random permutation of ``symbols`` (the null's selection order)."""
    perm = rng.permutation(len(symbols))
    return [symbols[int(i)] for i in perm]


def build_random_book(
    panel: Sequence[SymbolInputs], cfg: ExecutionConfig, rng: np.random.Generator
) -> DrawOutcome:
    """One random draw: eligible pools -> RANDOM order (step 3) -> the shared finalize.

    Byte-identical to ``build_book`` except the ordering is a seeded random permutation
    instead of the signal rank.
    """
    long_pool, short_pool, by_symbol = eligible_pools(panel)
    long_ordered = _shuffled(list(long_pool), rng)
    short_ordered = _shuffled(list(short_pool), rng)
    return finalize(long_ordered, short_ordered, by_symbol, cfg)


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
