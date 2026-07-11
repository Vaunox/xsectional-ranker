"""Layer 2 — the Global Null Panel (the benchmark).

Random long-k/short-k draws pushed through the IDENTICAL execution pipeline as the
signal — same masks, circuit filter, sector cap, risk-parity sizing, caps, truncation,
gross floor. ONLY selection differs (ranked vs random). Generated once globally with a
fixed logged seed (reproducible, versioned), then sliced to the signal's surviving
days; not purged (a memoryless draw has zero parameters and cannot leak).
"""

from __future__ import annotations
