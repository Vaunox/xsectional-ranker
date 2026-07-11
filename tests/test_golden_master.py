"""Check 2 — golden-master bit-for-bit reconciliation (Deep Dive 03).

Each fixture in ``tests/golden`` was birthed by running the vendored harness in
the PREDECESSOR repo at pinned commit ``0c5c592`` (numpy 2.4.6 / scipy 1.17.1,
Python 3.11; see ``src/vendored/VENDORED_FROM.md`` and the ``scratch/xsr-golden-gen``
branch there). This test replays each fixture's stored ``inputs`` through the
byte-identical vendored code HERE and asserts the result equals the stored
``outputs`` to full numeric tolerance. A mismatch means the numeric stack drifted
— a hard stop, not a "close enough".

Tolerance: ``rtol=0, atol=1e-12`` (Deep Dive 03 Check 2). Observed drift on this
stack is exactly 0.0 (see the manifest); the tolerance is the documented ceiling,
not evidence of slop.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

import pytest

from scripts.generate_goldens import COMPUTERS

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
ATOL = 1e-12

#: The five Deep-Dive-03 Check-2 minimums plus the sixth seeded-RNG golden.
REQUIRED: dict[str, str] = {
    "cpcv_path_distribution": "one CPCV path-distribution",
    "dsr_known_effective_n": "one DSR at a known effective-N",
    "pbo_cscv": "one PBO / CSCV case",
    "effective_n_correlated_group": "one effective-N clustering of a known correlated group",
    "round_trip_cost": "one full round-trip cost",
    "monte_carlo_sign_flip_seeded": "one seeded Monte-Carlo robustness (RNG seed-lock)",
    # Phase-2 vendored feature primitives (TA-Lib enters here; atr is bit-stability):
    "feature_gap": "vendored gap (overnight gap) primitive",
    "feature_atr": "vendored atr (talib.ATR) primitive — bit-stability",
    "feature_cross_sectional_rank": "vendored cross_sectional_rank primitive",
}


def _mismatches(recomputed: Any, stored: Any, path: str = "") -> list[str]:
    """Recursively collect bit-for-bit mismatches (atol on numbers, NaN==NaN)."""
    out: list[str] = []
    if isinstance(stored, dict):
        if not isinstance(recomputed, dict) or recomputed.keys() != stored.keys():
            return [f"{path}: dict shape differs"]
        for key in stored:
            out += _mismatches(recomputed[key], stored[key], f"{path}.{key}")
    elif isinstance(stored, list):
        if not isinstance(recomputed, list) or len(recomputed) != len(stored):
            return [f"{path}: list length differs"]
        for i, (r, s) in enumerate(zip(recomputed, stored, strict=True)):
            out += _mismatches(r, s, f"{path}[{i}]")
    elif isinstance(stored, bool) or isinstance(recomputed, bool):
        if recomputed != stored:
            out.append(f"{path}: {recomputed!r} != {stored!r}")
    elif isinstance(stored, (int, float)) and isinstance(recomputed, (int, float)):
        rf, sf = float(recomputed), float(stored)
        if math.isnan(sf) or math.isnan(rf):
            if not (math.isnan(sf) and math.isnan(rf)):
                out.append(f"{path}: NaN mismatch ({recomputed!r} vs {stored!r})")
        elif abs(rf - sf) > ATOL:
            out.append(f"{path}: |{rf} - {sf}| = {abs(rf - sf):.3e} > {ATOL:.0e}")
    elif recomputed != stored:
        out.append(f"{path}: {recomputed!r} != {stored!r}")
    return out


def test_golden_set_covers_the_check2_minimums() -> None:
    """Fail closed if any required golden category is missing (no silent drop)."""
    present = {p.stem for p in GOLDEN_DIR.glob("*.json")}
    missing = set(REQUIRED) - present
    assert not missing, f"missing required goldens: {sorted(missing)}"


@pytest.mark.golden
@pytest.mark.parametrize("name", sorted(REQUIRED))
def test_golden_reconciles_bit_for_bit(name: str) -> None:
    """The vendored function here reproduces the predecessor-birthed output exactly."""
    assert os.environ.get("OMP_NUM_THREADS") == "1", (
        "golden reconciliation requires OMP_NUM_THREADS=1 (Deep Dive 03 Check 4) "
        "to avoid BLAS reduction-order drift; set it in the env or run via CI."
    )
    path = GOLDEN_DIR / f"{name}.json"
    assert path.exists(), f"missing golden fixture: {name}"
    stored = json.loads(path.read_text(encoding="utf-8"))
    assert stored["meta"]["predecessor_sha"] == "0c5c592b9bc80525625597906cdaf8d7f203bb13"
    recomputed = COMPUTERS[name](stored["inputs"])
    mism = _mismatches(recomputed, stored["outputs"])
    assert not mism, f"golden '{name}' drifted from the pinned stack:\n" + "\n".join(mism)


def test_round_trip_cost_golden_anchors_the_hand_worked_figure() -> None:
    """The cost golden is pinned to the predecessor's hand-worked ₹182.4452 fixture."""
    stored = json.loads((GOLDEN_DIR / "round_trip_cost.json").read_text(encoding="utf-8"))
    assert stored["outputs"]["round_trip_cost"] == pytest.approx(182.4452, abs=1e-4)
