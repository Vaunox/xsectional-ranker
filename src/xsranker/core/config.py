"""Typed, layered YAML configuration (Part I §1 — no literal thresholds in code).

A base ``config/default.yaml`` is optionally overlaid by an environment file
(``config/env/<env>.yaml``). Business logic reads typed fields off
:class:`Settings` rather than parsing YAML or hard-coding constants.

This module is deliberately free of any ``lab.*`` (vendored) import: it hands the
harness adapter a ``config_dir`` and a ``seed``, and the adapter is the sole
bridge to the frozen cost/statistics machinery (freeze boundary, Deep Dive 03).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

#: Repository ``config/`` directory (…/src/xsranker/core/config.py → parents[3]).
DEFAULT_CONFIG_DIR: Path = Path(__file__).resolve().parents[3] / "config"


@dataclass(frozen=True, slots=True)
class Settings:
    """Typed program settings resolved from the layered YAML config."""

    #: Directory the config was loaded from (also where the cost model lives).
    config_dir: Path
    #: Minimum log level to emit.
    log_level: str
    #: Log renderer (``"console"`` or ``"json"``).
    log_renderer: str
    #: Master determinism seed for every stochastic harness path (Check 4).
    seed: int


def _deep_merge(base: Mapping[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively merge ``overlay`` onto ``base`` (overlay wins at the leaves)."""
    merged: dict[str, Any] = dict(base)
    for key, value in overlay.items():
        existing = merged.get(key)
        if isinstance(existing, Mapping) and isinstance(value, Mapping):
            merged[key] = _deep_merge(existing, value)
        else:
            merged[key] = value
    return merged


def _read_yaml(path: Path) -> dict[str, Any]:
    """Parse a YAML file into a mapping (empty file → empty mapping)."""
    data: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping at the top level")
    return data


def load_settings(config_dir: Path | None = None, *, env: str | None = None) -> Settings:
    """Load :class:`Settings` from ``config_dir`` (default: the repo ``config/``).

    Args:
        config_dir: Directory holding ``default.yaml`` (and ``env/<env>.yaml``).
        env: Optional environment name; if given, ``env/<env>.yaml`` is overlaid.

    Raises:
        FileNotFoundError: If ``default.yaml`` is missing.
        ValueError: If a required key is absent or malformed.
    """
    directory = config_dir or DEFAULT_CONFIG_DIR
    base_path = directory / "default.yaml"
    if not base_path.exists():
        raise FileNotFoundError(f"missing base config: {base_path}")
    merged = _read_yaml(base_path)
    if env is not None:
        overlay_path = directory / "env" / f"{env}.yaml"
        if not overlay_path.exists():
            raise FileNotFoundError(f"unknown env overlay: {overlay_path}")
        merged = _deep_merge(merged, _read_yaml(overlay_path))

    logging_cfg = merged.get("logging", {})
    if not isinstance(logging_cfg, Mapping):
        raise ValueError("'logging' must be a mapping")
    if "seed" not in merged:
        raise ValueError("config must define a top-level 'seed' (determinism lock)")

    return Settings(
        config_dir=directory,
        log_level=str(logging_cfg.get("level", "INFO")),
        log_renderer=str(logging_cfg.get("renderer", "console")),
        seed=int(merged["seed"]),
    )
