"""Ex-ante ⌈k/2⌉-per-sector cap — mechanism enforcement, not a post-hoc flag (#6).

A clustered sector gap is macro repricing, not idiosyncratic overreaction, so fading
it violates the signal's core hypothesis. The cap is applied AT CONSTRUCTION: walking
the conviction-ranked candidates, a name is skipped if its sector is already at the
cap, moving to the next eligible name — the FORBIDDEN alternative (a post-hoc
concentration flag that forces an illegitimate sample filter on a pass) is never used.
"""

from __future__ import annotations

from collections.abc import Sequence


def apply_sector_cap(
    ranked: Sequence[tuple[str, str]], *, k: int, per_sector_cap: int
) -> list[str]:
    """Select up to ``k`` names from conviction-ranked ``(symbol, sector)`` pairs.

    No sector contributes more than ``per_sector_cap``; on violation, skip to the next
    eligible name (never drop a lower-ranked name to make room). Returns fewer than
    ``k`` only if the ranked pool is exhausted under the cap.
    """
    selected: list[str] = []
    per_sector: dict[str, int] = {}
    for symbol, sector in ranked:
        if len(selected) >= k:
            break
        if per_sector.get(sector, 0) >= per_sector_cap:
            continue  # sector full -> skip to the next eligible name
        selected.append(symbol)
        per_sector[sector] = per_sector.get(sector, 0) + 1
    return selected
