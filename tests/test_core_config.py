"""Tests for the layered YAML config loader (Part I §1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from xsranker.core.config import DEFAULT_CONFIG_DIR, load_settings


def test_loads_repo_defaults() -> None:
    settings = load_settings()
    assert settings.config_dir == DEFAULT_CONFIG_DIR
    assert settings.log_level == "INFO"
    assert settings.log_renderer == "console"
    # The determinism seed is present and integral (Check 4 wires it downstream).
    assert isinstance(settings.seed, int)


def _write(dir_: Path, name: str, text: str) -> None:
    (dir_ / name).write_text(text, encoding="utf-8")


def test_env_overlay_deep_merges(tmp_path: Path) -> None:
    _write(tmp_path, "default.yaml", "seed: 1\nlogging:\n  level: INFO\n  renderer: console\n")
    (tmp_path / "env").mkdir()
    _write(tmp_path / "env", "dev.yaml", "logging:\n  level: DEBUG\n")
    settings = load_settings(tmp_path, env="dev")
    assert settings.log_level == "DEBUG"  # overlaid
    assert settings.log_renderer == "console"  # preserved from base (deep merge)
    assert settings.seed == 1


def test_missing_default_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_settings(tmp_path)


def test_missing_seed_is_rejected(tmp_path: Path) -> None:
    _write(tmp_path, "default.yaml", "logging:\n  level: INFO\n")
    with pytest.raises(ValueError, match="seed"):
        load_settings(tmp_path)


def test_unknown_env_overlay_raises(tmp_path: Path) -> None:
    _write(tmp_path, "default.yaml", "seed: 1\n")
    with pytest.raises(FileNotFoundError):
        load_settings(tmp_path, env="nope")
