# mypy: disable-error-code="no-untyped-def, no-any-return, no-untyped-call"
"""Run harness end-to-end on a tiny synthetic universe with a KNOWN answer.

Six names in distinct sectors: the gap-downs subsequently RISE and the gap-ups FALL, so
the signal (long the biggest gap-downs, short the biggest gap-ups) is the OPTIMAL
selection. The harness must: net-return the book correctly (every day positive, ~0.06),
have the gate detect the skill (every per-arm binding criterion passes, beat=100), cluster
two correlated arms below the raw count (effective-N < 2), and report clean diagnostics
(0 day-drops, 0 short-ban). A no-edge signal must fail beat-random. Assembly from OHLCV is
spot-checked against the (separately teeth-tested) point-in-time primitives.
"""

from __future__ import annotations

import tempfile
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from xsranker.backtest.diagnostics import run_diagnostics
from xsranker.backtest.harness import SymbolDay, build_symbol_days, run_arm
from xsranker.backtest.report import run_program
from xsranker.core.config import load_settings
from xsranker.core.types import IST_OFFSET_NS, OHLCV
from xsranker.execution.config import CostCorridorConfig, ExecutionConfig
from xsranker.execution.pipeline import SymbolInputs
from xsranker.gate.config import GateThresholds
from xsranker.harness.adapter import HarnessAdapter
from xsranker.signals.spec import SignalArm

EXEC = ExecutionConfig(
    k_per_leg=2, participation_cap=0.01, gross_floor_inr=1_000.0, sector_cap_divisor=2
)
COST = CostCorridorConfig(optimistic_spread_multiplier=1.0, pessimistic_spread_multiplier=3.0)
THRESH = GateThresholds(
    null_percentile=95.0,
    dsr_min=0.95,
    pbo_max=0.20,
    cpcv_median_min=0.0,
    positive_fraction_min=0.5,
    near_margin_percentile=2.0,
    near_margin_prob=0.02,
    near_margin_sharpe=0.02,
)
# (symbol, sector, gap, edge_sign): downs (neg gap) rise (+), ups (pos gap) fall (-).
SPEC = [
    ("DOWN1", "S1", -0.05, +1.0),
    ("DOWN2", "S2", -0.04, +1.0),
    ("DOWN3", "S3", -0.03, +1.0),
    ("UP1", "S4", 0.05, -1.0),
    ("UP2", "S5", 0.04, -1.0),
    ("UP3", "S6", 0.03, -1.0),
]
DAYS = [date(2024, 1, 1) + timedelta(days=i) for i in range(40)]


def _adapter() -> HarnessAdapter:
    return HarnessAdapter(load_settings())


def _sym_day(symbol, sector, signal, hold):
    return SymbolDay(
        SymbolInputs(symbol, signal, sector, 2.0, 1_000_000_000.0, True, True, False), hold, 0.0005
    )


def _skilled_cross(scale: np.ndarray):
    # net(d) = 0.06 * scale[d] > 0 every day (the edge; a common move would cancel).
    return {
        d: [_sym_day(s, sec, g, sign * 0.03 * scale[i]) for s, sec, g, sign in SPEC]
        for i, d in enumerate(DAYS)
    }


def test_skilled_signal_detected_and_arms_cluster_end_to_end() -> None:
    r = np.random.default_rng(7)
    shared = r.random(40)  # common component -> the two arms are positively correlated
    run_a = run_arm(
        DAYS,
        _skilled_cross(0.6 + shared + 0.3 * r.random(40)),
        adapter=_adapter(),
        exec_cfg=EXEC,
        cost_cfg=COST,
        cost_model=_adapter().load_cost_model(),
        draws_per_day=50,
        rng=np.random.default_rng(20260711),
    )
    run_b = run_arm(
        DAYS,
        _skilled_cross(0.6 + shared + 0.3 * r.random(40)),
        adapter=_adapter(),
        exec_cfg=EXEC,
        cost_cfg=COST,
        cost_model=_adapter().load_cost_model(),
        draws_per_day=50,
        rng=np.random.default_rng(20260712),
    )

    # book P&L: every surviving day profits; the pessimistic bound costs more.
    assert len(run_a.optimistic.signal_by_day) == 40
    assert run_a.signal_day_drops == 0 and run_a.short_ban_fires == 0
    sig_opt = np.array([run_a.optimistic.signal_by_day[d] for d in DAYS])
    sig_pess = np.array([run_a.pessimistic.signal_by_day[d] for d in DAYS])
    assert (sig_opt > 0).all()
    assert (sig_pess < sig_opt).all()  # cost is strictly worse at the pessimistic bound

    diag = run_diagnostics(run_a, _skilled_cross(0.6 + shared), draws_per_day=50)
    assert diag.signal_day_drop_fraction == 0.0
    assert diag.short_ban_fire_rate == 0.0

    with tempfile.TemporaryDirectory() as d:
        ledger = _adapter().trial_ledger(Path(d))
        prog = run_program(
            {"A": run_a, "B": run_b},
            ledger=ledger,
            adapter=_adapter(),
            thresholds=THRESH,
            cpcv_groups=5,
            cpcv_k=2,
            periods_per_year=252.0,
            pbo_splits=4,
        )
    arm = prog.arms[0]
    # the gate detects the skill: every per-arm binding criterion passes, at both bounds.
    for report in (arm.optimistic, arm.pessimistic):
        assert report.beat_random.beat_percentile == 100.0
        assert report.beat_passed and report.dsr_passed
        assert report.cpcv_median_passed and report.positive_fraction_passed
    # Ruling 3: two correlated arms cluster below the raw count (never a raw 2).
    assert prog.raw_arm_count == 2
    assert 1.0 <= prog.effective_trials < 2.0
    assert np.isfinite(prog.pbo.pbo)  # PBO computes (its value is a 2-arm/tiny-split artifact here)


def _no_edge_cross(seed: int):
    # holds bear no relation to the gap -> the fixed-by-gap selection earns ~random ->
    # the signal cannot beat the execution-matched random null.
    rng = np.random.default_rng(seed)
    return {
        d: [_sym_day(s, sec, g, float(rng.normal(0.0, 0.02))) for s, sec, g, _ in SPEC]
        for d in DAYS
    }


def test_no_edge_signal_fails_beat_random() -> None:
    run_a = run_arm(
        DAYS,
        _no_edge_cross(1),
        adapter=_adapter(),
        exec_cfg=EXEC,
        cost_cfg=COST,
        cost_model=_adapter().load_cost_model(),
        draws_per_day=50,
        rng=np.random.default_rng(1),
    )
    run_b = run_arm(
        DAYS,
        _no_edge_cross(2),
        adapter=_adapter(),
        exec_cfg=EXEC,
        cost_cfg=COST,
        cost_model=_adapter().load_cost_model(),
        draws_per_day=50,
        rng=np.random.default_rng(2),
    )
    with tempfile.TemporaryDirectory() as d:
        ledger = _adapter().trial_ledger(Path(d))
        prog = run_program(
            {"A": run_a, "B": run_b},
            ledger=ledger,
            adapter=_adapter(),
            thresholds=THRESH,
            cpcv_groups=5,
            cpcv_k=2,
            periods_per_year=252.0,
            pbo_splits=4,
        )
    # a signal with no edge does not clear the 95th null percentile -> beat fails.
    assert not prog.arms[0].optimistic.beat_passed


def _ohlcv(symbol: str, per_day: list[tuple[date, float, float, float]]) -> OHLCV:
    """Per day: (date, day_open, entry_close, day_close) -> bars at 09:15 / 09:45 / 15:25.

    Each bar gets a +-0.5% high/low band so ATR and Corwin-Schultz spread are defined.
    """
    ts: list[np.datetime64] = []
    o: list[float] = []
    h: list[float] = []
    low: list[float] = []
    c: list[float] = []
    for d, day_open, entry_close, day_close in per_day:
        base = np.datetime64(d, "ns")
        for minute, px in ((555, day_open), (585, entry_close), (925, day_close)):
            utc = (
                base
                + np.timedelta64(minute * 60, "s").astype("timedelta64[ns]")
                - np.timedelta64(IST_OFFSET_NS, "ns")
            )
            ts.append(utc)
            o.append(day_open)
            c.append(px)
            h.append(px * 1.005)
            low.append(px * 0.995)
    return OHLCV(
        symbol,
        "5minute",
        np.array(ts, dtype="datetime64[ns]"),
        np.array(o),
        np.array(h),
        np.array(low),
        np.array(c),
        np.full(len(c), 100_000, dtype=np.int64),
    )


def test_assembly_from_ohlcv_wires_the_primitives() -> None:
    # 8 gently-rising days + a gap-DOWN on 01-08: prior close 104 -> open 102 (gap ~ -1.9%);
    # entry 102 -> close 107.1 -> hold +5%. Earlier days give ATR/spread their lookback.
    per_day = [
        (date(2024, 1, d), 100.0 + i, 100.0 + i, 101.0 + i) for i, d in enumerate(range(1, 6))
    ]
    per_day.append((date(2024, 1, 8), 102.0, 102.0, 107.1))  # the gap-down day we check
    per_day.append((date(2024, 1, 9), 108.0, 108.0, 108.5))
    series = _ohlcv("X", per_day)

    days = build_symbol_days(
        "X",
        series,
        arm=SignalArm.A,
        entry_minute=585,
        atr_period=2,
        sector="S1",
        long_eligible=True,
        short_eligible=True,
        circuit_locked_by_day={},
        adapter=_adapter(),
    )
    check = date(2024, 1, 8)
    assert check in days  # all point-in-time inputs (gap, hold, value, atr, spread) exist
    sd = days[check]
    assert sd.inputs.signal < 0  # a gap-DOWN day -> negative gap%
    assert abs(sd.hold - (107.1 / 102.0 - 1.0)) < 1e-9  # entry->close hold matches the primitive
    assert sd.inputs.entry_window_value_inr > 0
    assert np.isfinite(sd.spread)  # the spread wired through (its value is the CS estimator's)
