"""Candidate #3 sector-relative move (SR / SR-Z) — leave-one-out correctness, the peer-count
gate, per-day independence (point-in-time), and the SR-Z ATR guard.

SR demeans each name against its SAME-DAY same-sector peers EXCLUDING itself, so (a) a name never
biases its own benchmark, (b) each day is an independent cross-section (no lookahead across days),
and (c) SR is exactly mean-zero within each qualifying sector each day.
"""

from __future__ import annotations

from datetime import date

from xsranker.signals.sector_relative import (
    DEFAULT_MIN_PEERS,
    sector_relative_move,
    sector_relative_z,
)

_D1 = date(2024, 1, 1)
_D2 = date(2024, 1, 2)


def test_leave_one_out_exact_values() -> None:
    # One 3-name sector, values 1/2/3: SR_i = val_i - mean(the OTHERS).
    mr = {"A": {_D1: 1.0}, "B": {_D1: 2.0}, "C": {_D1: 3.0}}
    sector = {"A": "BANK", "B": "BANK", "C": "BANK"}
    sr = sector_relative_move(mr, sector)
    assert abs(sr["A"][_D1] - (1.0 - 2.5)) < 1e-12  # 1 - mean(2,3) = -1.5
    assert abs(sr["B"][_D1] - (2.0 - 2.0)) < 1e-12  # 2 - mean(1,3) =  0.0
    assert abs(sr["C"][_D1] - (3.0 - 1.5)) < 1e-12  # 3 - mean(1,2) = +1.5


def test_sr_is_mean_zero_within_sector_each_day() -> None:
    # Leave-one-out demeaning is exactly sum-zero within each sector on each day (an algebraic
    # identity: sum_i loo_mean_i == sum_i val_i), so SR is sector-neutral by construction.
    mr = {
        "A": {_D1: 0.4, _D2: -0.1},
        "B": {_D1: -0.2, _D2: 0.5},
        "C": {_D1: 0.7, _D2: 0.3},
        "D": {_D1: -0.9, _D2: 0.0},
    }
    sector = dict.fromkeys(("A", "B", "C", "D"), "BANK")
    sr = sector_relative_move(mr, sector)
    for d in (_D1, _D2):
        assert abs(sum(sr[s][d] for s in ("A", "B", "C", "D"))) < 1e-12


def test_own_value_excluded_teeth() -> None:
    # Teeth for leave-one-out: an extreme own value must NOT dilute its own benchmark. An inclusive
    # sector mean would give SR_A = 100 - mean(100,0,0) = 66.67; leave-one-out keeps the full 100.
    mr = {"A": {_D1: 100.0}, "B": {_D1: 0.0}, "C": {_D1: 0.0}}
    sector = dict.fromkeys(("A", "B", "C"), "BANK")
    sr = sector_relative_move(mr, sector)
    assert abs(sr["A"][_D1] - 100.0) < 1e-12  # 100 - mean(0,0), not 100 - mean(100,0,0)


def test_min_peers_gate_and_missing_sector() -> None:
    mr = {
        "A": {_D1: 1.0},
        "B": {_D1: 2.0},
        "C": {_D1: 3.0},  # BANK: 3 names -> n=3 >= min_peers+1 -> qualifies
        "P": {_D1: 1.0},
        "Q": {_D1: 2.0},  # AUTO: 2 names -> n=2 < 3 -> excluded
        "Z": {_D1: 9.0},  # no sector entry -> excluded
    }
    sector = {"A": "BANK", "B": "BANK", "C": "BANK", "P": "AUTO", "Q": "AUTO"}  # Z absent
    sr = sector_relative_move(mr, sector, min_peers=DEFAULT_MIN_PEERS)
    assert set(sr) == {"A", "B", "C"}  # only the >=3-name sector, only where the sector is known


def test_per_day_independence_no_cross_day_leak() -> None:
    # Day D2's SR must be identical whether or not D1 is present: each day is its own cross-section,
    # so no other day (past OR future) can perturb it.
    full = {"A": {_D1: 1.0, _D2: 4.0}, "B": {_D1: 2.0, _D2: 5.0}, "C": {_D1: 3.0, _D2: 6.0}}
    sector = dict.fromkeys(("A", "B", "C"), "BANK")
    sr_full = sector_relative_move(full, sector)
    d2_only = {"A": {_D2: 4.0}, "B": {_D2: 5.0}, "C": {_D2: 6.0}}
    sr_d2 = sector_relative_move(d2_only, sector)
    for s in ("A", "B", "C"):
        assert abs(sr_full[s][_D2] - sr_d2[s][_D2]) < 1e-12


def test_sector_relative_z_divides_by_atr_and_drops_nonpositive() -> None:
    sr = {"A": {_D1: 1.5, _D2: 2.0}, "B": {_D1: -0.5, _D2: 1.0}}
    atr = {"A": {_D1: 0.5, _D2: 0.0}, "B": {_D1: 0.25}}  # A/_D2 zero ATR; B/_D2 absent
    srz = sector_relative_z(sr, atr)
    assert abs(srz["A"][_D1] - 3.0) < 1e-12  # 1.5 / 0.5
    assert _D2 not in srz.get("A", {})  # zero ATR -> dropped (not rankable)
    assert abs(srz["B"][_D1] - (-2.0)) < 1e-12  # -0.5 / 0.25
    assert _D2 not in srz.get("B", {})  # absent ATR -> dropped
