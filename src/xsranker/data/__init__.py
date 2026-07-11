"""Layer 1 — data seam, hygiene, and the point-in-time universe machinery.

All external access is behind an adapter/Repository; paths and thresholds are
config, never literals (Part I §1). Phase 1 reads the inherited external Parquet
cache read-only — no Kite ingestion, no cache regeneration.
"""

from __future__ import annotations
