"""Point-in-time feature machinery for Layer 1.

These are the morning-window / trailing features the leakage suites exercise — the
signal ranking features (gap, ATR-20, cross_sectional_rank) are Phase 2 and are not
here. Everything computable at the entry instant uses only bars <= entry, with
trailing/expanding normalization only.
"""

from __future__ import annotations
