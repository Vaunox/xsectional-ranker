"""Static point-in-time sector classification (a label map, not a price series).

Feeds the Phase-2 ceil(k/2)-per-sector cap. Phase 1 only loads it and validates
full coverage of the universe (its Phase-1 call site is the gate-zero check).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_sector_map(path: Path) -> dict[str, str]:
    """Load ``symbol -> sector`` from YAML (under a top-level ``sectors`` key)."""
    data: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "sectors" not in data:
        raise ValueError(f"{path} must contain a 'sectors' mapping")
    sectors = data["sectors"]
    if not isinstance(sectors, dict) or not sectors:
        raise ValueError(f"{path}: 'sectors' must be a non-empty mapping")
    return {str(k): str(v) for k, v in sectors.items()}


def uncovered_symbols(sector_map: dict[str, str], symbols: tuple[str, ...]) -> list[str]:
    """Universe symbols missing a sector label (empty list == full coverage)."""
    return [s for s in symbols if s not in sector_map]


def sector_of(sector_map: dict[str, str], symbol: str) -> str:
    """Sector label for ``symbol`` (raises if unmapped — fail closed)."""
    if symbol not in sector_map:
        raise KeyError(f"no sector for {symbol}")
    return sector_map[symbol]
