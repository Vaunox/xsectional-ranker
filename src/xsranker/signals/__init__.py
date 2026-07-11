"""Layer 2 — signal ranking (Signals A and A-Z).

A ranks by gap%; A-Z ranks by gap% ÷ ATR% (ATR-20 in return units) — the frozen,
price-neutral definition (MASTER_BLUEPRINT Part V, resolved 2026-07-11). Both use the
FROZEN vendored ``gap``/``atr`` primitives through the adapter; the intraday->daily
resample for ATR-20 is new Layer-2 code and is point-in-time (no future bars in a
day's aggregation, and the ATR feeding day D uses only completed days < D).
"""

from __future__ import annotations
