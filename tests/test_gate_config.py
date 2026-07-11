"""Gate-threshold loader — binds every field; fails closed on a missing block/key.

Uses an in-test ``gate:`` mapping so the loader is exercised WITHOUT committing any
value to ``config/default.yaml`` — the four blind values are frozen only at Step 2.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping

import pytest

from xsranker.core.config import Settings, load_settings
from xsranker.gate.config import load_gate_thresholds

_FULL_BLOCK = {
    "null_percentile": 95,
    "dsr_min": 0.95,
    "pbo_max": 0.20,
    "cpcv_median_min": 0.0,
    "positive_fraction_min": 0.5,
    "near_margin_percentile": 2.0,
    "near_margin_prob": 0.02,
    "near_margin_sharpe": 0.02,
}


def _settings_with_gate(block: Mapping[str, object]) -> Settings:
    settings = load_settings()
    raw = dict(settings.raw)
    raw["gate"] = block
    return dataclasses.replace(settings, raw=raw)


def _settings_without_gate() -> Settings:
    settings = load_settings()
    raw = {k: v for k, v in settings.raw.items() if k != "gate"}
    return dataclasses.replace(settings, raw=raw)


def test_loader_binds_every_field() -> None:
    gt = load_gate_thresholds(_settings_with_gate(dict(_FULL_BLOCK)))
    assert gt.null_percentile == 95.0
    assert gt.dsr_min == 0.95
    assert gt.pbo_max == 0.20
    assert gt.cpcv_median_min == 0.0
    assert gt.positive_fraction_min == 0.5
    assert gt.near_margin_percentile == 2.0
    assert gt.near_margin_prob == 0.02
    assert gt.near_margin_sharpe == 0.02


def test_loader_fails_closed_without_a_gate_block() -> None:
    # A settings whose config has no gate block must raise (robust to default.yaml
    # gaining one at the Step-2 freeze — the loader fails closed, never silently).
    with pytest.raises(ValueError, match="gate"):
        load_gate_thresholds(_settings_without_gate())


def test_loader_fails_closed_on_a_missing_key() -> None:
    partial = {"null_percentile": 95}
    with pytest.raises(ValueError):
        load_gate_thresholds(_settings_with_gate(partial))
