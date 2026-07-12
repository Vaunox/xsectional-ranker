"""Typed Layer-2 config (signal / execution / cost / null), built off ``Settings``.

TOY-stamped fields (``k_per_leg``, ``gross_floor_inr``, ``null.draws_per_day``) are
deliberately NOT the frozen research values — those are committed blind at the
Phase 2->3 boundary. The pre-registered non-TOY frozen values (participation cap,
spread multipliers, ATR period, sector-cap divisor) are real here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from xsranker.core.config import Settings


def _req(m: Mapping[str, Any], key: str, ctx: str) -> Any:
    if key not in m:
        raise ValueError(f"config: missing '{key}' under {ctx}")
    return m[key]


@dataclass(frozen=True, slots=True)
class SignalConfig:
    """Signal parameters (the ATR window is a frozen 20-day measure)."""

    atr_period: int


@dataclass(frozen=True, slots=True)
class ExecutionConfig:
    """Execution parameters. ``k_per_leg`` and ``gross_floor_inr`` are TOY here."""

    k_per_leg: int
    participation_cap: float
    gross_floor_inr: float
    sector_cap_divisor: int

    @property
    def sector_cap(self) -> int:
        """ceil(k / divisor) names per sector per leg."""
        return -(-self.k_per_leg // self.sector_cap_divisor)


#: Cost-corridor modes. ``FIXED_SPREAD`` is the candidate-#2+ standard (verified fees + a
#: pinned fixed spread; Corwin-Schultz RETIRED from the live path). ``CORWIN_SCHULTZ`` is
#: retained ONLY for regenerating candidate #1's ledger streams at historical fidelity (the
#: cost model in force when they were run) — never for a live verdict.
CORWIN_SCHULTZ = "corwin_schultz"
FIXED_SPREAD = "fixed_spread"


@dataclass(frozen=True, slots=True)
class CostCorridorConfig:
    """Cost-corridor bounds. ``mode`` selects fees+fixed-spread (live) vs Corwin-Schultz.

    In ``FIXED_SPREAD`` mode only the ``*_spread_bps`` are used (round-trip proportional
    spread; the square-root impact term is zeroed — the fixed spread IS the conservative
    slippage envelope). In ``CORWIN_SCHULTZ`` mode only the ``*_multiplier`` fields are used.
    """

    mode: str
    optimistic_spread_multiplier: float  # CS mode only
    pessimistic_spread_multiplier: float  # CS mode only
    optimistic_spread_bps: float  # fixed mode only (round-trip proportional spread, bps)
    pessimistic_spread_bps: float  # fixed mode only


@dataclass(frozen=True, slots=True)
class NullConfig:
    """Null-panel parameters. ``draws_per_day`` (N) is TOY here."""

    draws_per_day: int


@dataclass(frozen=True, slots=True)
class Layer2Config:
    """The full Layer-2 config surface."""

    signal: SignalConfig
    execution: ExecutionConfig
    cost: CostCorridorConfig
    null: NullConfig


def load_layer2_config(settings: Settings) -> Layer2Config:
    """Build the typed Layer-2 config from the merged mapping on ``settings``."""
    raw = settings.raw
    sig = _req(raw, "signal", "root")
    ex = _req(raw, "execution", "root")
    cost = _req(raw, "cost", "root")
    null = _req(raw, "null", "root")
    return Layer2Config(
        signal=SignalConfig(atr_period=int(_req(sig, "atr_period", "signal"))),
        execution=ExecutionConfig(
            k_per_leg=int(_req(ex, "k_per_leg", "execution")),
            participation_cap=float(_req(ex, "participation_cap", "execution")),
            gross_floor_inr=float(_req(ex, "gross_floor_inr", "execution")),
            sector_cap_divisor=int(_req(ex, "sector_cap_divisor", "execution")),
        ),
        cost=CostCorridorConfig(
            mode=str(_req(cost, "mode", "cost")),
            optimistic_spread_multiplier=float(_req(cost, "optimistic_spread_multiplier", "cost")),
            pessimistic_spread_multiplier=float(
                _req(cost, "pessimistic_spread_multiplier", "cost")
            ),
            optimistic_spread_bps=float(_req(cost, "optimistic_spread_bps", "cost")),
            pessimistic_spread_bps=float(_req(cost, "pessimistic_spread_bps", "cost")),
        ),
        null=NullConfig(draws_per_day=int(_req(null, "draws_per_day", "null"))),
    )
