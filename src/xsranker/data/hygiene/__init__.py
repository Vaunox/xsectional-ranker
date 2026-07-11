"""Hygiene jobs: corp-action adjustment, bad-tick filtering, gap and liquidity checks.

Idempotent, tested, logged (Part I §2). Original Layer-1 code — not the frozen
vendored harness.
"""

from __future__ import annotations
