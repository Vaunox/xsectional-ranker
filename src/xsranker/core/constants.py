"""Program-wide constants (no business thresholds — those live in config)."""

from __future__ import annotations

from typing import Final

#: Import namespace of the new program package.
PACKAGE_NAME: Final[str] = "xsranker"

#: IANA timezone for the NSE trading session; all timestamps are stamped in IST.
INDIA_TZ: Final[str] = "Asia/Kolkata"
