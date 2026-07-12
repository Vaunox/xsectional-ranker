"""Durable, fail-closed effective-N trial ledger (R2 fix, Inviolable Rule 4).

Wraps the FROZEN vendored ``TrialLedger`` with a committed storage location, a manifest of
required prior-candidate streams, and a fail-closed integrity guard — so the DSR always
deflates by the honest cumulative effective-N and never a silently-undercounted one.
"""

from xsranker.ledger.config import LedgerConfig, load_ledger_config
from xsranker.ledger.persistence import (
    LedgerIntegrityError,
    LedgerManifest,
    arm_trial_id,
    load_manifest,
    open_persistent_ledger,
    verify_ledger_integrity,
    write_manifest,
)

__all__ = [
    "LedgerConfig",
    "LedgerIntegrityError",
    "LedgerManifest",
    "arm_trial_id",
    "load_ledger_config",
    "load_manifest",
    "open_persistent_ledger",
    "verify_ledger_integrity",
    "write_manifest",
]
