"""Cross-sectional intraday long-short ranker (NSE) — new program layers.

Layer 0 (the predecessor statistical harness) is frozen under ``src/vendored``
and reached only through :mod:`xsranker.harness.adapter`. Everything in this
package is new code built on top of that frozen core (Deep Dive 03).
"""

from __future__ import annotations

__version__ = "0.0.0"
