"""Point-in-time universe — Phase-1 survivor-cache STUB.

STAMP: survivorship-inflated upper bound. On every historical date this stub
returns the same present-day survivor set (no reconstitution history, no delisted
names). Because the signal longs the biggest gap-downs, survivor-only data deletes
exactly the catastrophic longs and inflates the long leg — a Phase-1 KILL is
hyper-trustworthy, a Phase-1 PASS is provisional. The real reconstruction (replay
NSE change-lists + backfill delisted/suspended names) is Phase 4.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class PointInTimeUniverse:
    """A stamped point-in-time universe (Phase 1: the survivor-cache stub)."""

    symbols: tuple[str, ...]
    stamp: str
    is_survivor_stub: bool = True

    def as_of(self, _d: date) -> tuple[str, ...]:
        """Constituents known on date ``_d``.

        STUB: returns the full survivor set on every date (no reconstitution). The
        date is accepted so the Phase-4 point-in-time implementation is a drop-in
        replacement behind the same call.
        """
        return self.symbols


def load_survivor_universe(universe_file: Path) -> PointInTimeUniverse:
    """Load the survivor-cache universe (symbols + survivorship stamp) from YAML."""
    data: Any = yaml.safe_load(universe_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "symbols" not in data:
        raise ValueError(f"{universe_file} must contain a 'symbols' list")
    symbols = tuple(str(s) for s in data["symbols"])
    if not symbols:
        raise ValueError(f"{universe_file}: empty symbol list")
    stamp = str(data.get("stamp", "survivorship-inflated upper bound (survivor-cache stub)"))
    return PointInTimeUniverse(symbols=symbols, stamp=stamp)
