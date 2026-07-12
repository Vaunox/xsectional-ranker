"""Typed config for the durable trial ledger (R2 fix — no literal paths in code)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from xsranker.core.config import Settings


@dataclass(frozen=True, slots=True)
class LedgerConfig:
    """Resolved paths for the durable, committed trial ledger."""

    #: The durable ledger directory (committed, holds one JSON per trial + the manifest).
    dir: Path
    #: The manifest declaring which prior candidates' streams must be present (fail-closed).
    manifest_path: Path


def load_ledger_config(settings: Settings) -> LedgerConfig:
    """Build :class:`LedgerConfig` from the ``ledger:`` block of the merged config.

    Paths are resolved relative to the repo root (the parent of ``config/``), so the ledger
    lives in the repo and is committed — never an ephemeral temp dir (the R2 defect).

    Raises:
        ValueError: if the ``ledger`` block or ``ledger.dir`` is absent.
    """
    raw = settings.raw
    block = raw.get("ledger")
    if not isinstance(block, Mapping):
        raise ValueError("config: missing 'ledger' block (durable trial ledger, R2 fix)")
    if "dir" not in block:
        raise ValueError("config: missing 'ledger.dir'")
    repo_root = settings.config_dir.parent
    directory = repo_root / str(block["dir"])
    manifest = directory / str(block.get("manifest_file", "MANIFEST.yaml"))
    return LedgerConfig(dir=directory, manifest_path=manifest)
