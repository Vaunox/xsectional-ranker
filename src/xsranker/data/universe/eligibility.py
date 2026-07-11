"""Dual eligibility masks — asymmetric short-bans modeled at their true granularity.

Short-bans are asymmetric: an ASM/GSM name can be legally un-shortable intraday yet
perfectly valid as a 100%-cash long, so eligibility is TWO masks, not one
(murder-board concession #7):

* ``long_eligible`` — intraday-tradable long: EQ-series (T2T/BE/BZ trade
  delivery-only, so cannot be squared intraday) and listed. ASM/GSM does not block
  a long.
* ``short_eligible`` — EQ-series, non-ASM, non-GSM, and shortable intraday. Where
  clean historical surveillance lists are unavailable, shortability is a margin/
  leverage PROXY (100% margin / 1x leverage ⇒ short-ineligible).

**Phase-1 honesty stamp:** architecturally complete but empirically UNEXERCISED —
large-cap survivors are all EQ / non-surveillance / shortable, so both masks pass
everything and the fire-rate is ~0%. That ~0% is the correct signature (logged),
not a gap; the masks go load-bearing only in the Phase-2/4 mid-cap crucible.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: Stamp carried by Phase-1 mask artifacts.
PHASE1_MASK_STAMP = (
    "dual eligibility masks architecturally complete but empirically unexercised in "
    "Phase 1 (~0% fire-rate on large-cap survivors is the expected signature)"
)


class Series(StrEnum):
    """NSE trading series (subset). EQ is intraday-tradable; BE/BZ are Trade-to-Trade."""

    EQ = "EQ"
    BE = "BE"  # Trade-to-Trade (delivery only)
    BZ = "BZ"  # Trade-to-Trade surveillance (delivery only)


@dataclass(frozen=True, slots=True)
class SecurityStatus:
    """Per-symbol, per-day tradability state feeding the dual masks."""

    symbol: str
    series: Series
    asm: bool = False  # Additional Surveillance Measure
    gsm: bool = False  # Graded Surveillance Measure
    shortable: bool = True  # margin/leverage proxy: False ⇒ 100% margin / 1x leverage


def long_eligible(status: SecurityStatus) -> bool:
    """Intraday-tradable long: EQ-series (T2T cannot be squared intraday)."""
    return status.series == Series.EQ


def short_eligible(status: SecurityStatus) -> bool:
    """EQ-series, non-ASM, non-GSM, and shortable intraday (margin/leverage proxy)."""
    return status.series == Series.EQ and not status.asm and not status.gsm and status.shortable
