"""Cross-sectional ranking of a single day's panel via the frozen primitive."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from xsranker.harness.adapter import HarnessAdapter


def rank_panel(signal_by_symbol: Mapping[str, float], adapter: HarnessAdapter) -> list[str]:
    """Symbols ordered by ascending signal (biggest gap-downs first) via cross_sectional_rank.

    Uses the frozen ``cross_sectional_rank`` on the single-timestamp cross-section, so
    the ordering is the harness's, not a re-implementation. Non-finite signals are
    dropped (a name we cannot rank is not tradeable).
    """
    finite = {s: v for s, v in signal_by_symbol.items() if np.isfinite(v)}
    if len(finite) < 2:
        return list(finite)
    panel = {s: np.array([v], dtype=np.float64) for s, v in finite.items()}
    ranks = adapter.cross_sectional_rank(panel)
    return sorted(finite, key=lambda s: (float(ranks[s][0]), s))
