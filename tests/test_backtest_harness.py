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
from xsranker.execution.book import Book, Position, Side
from xsranker.execution.config import (
    CORWIN_SCHULTZ,
    FIXED_SPREAD,
    CostCorridorConfig,
    ExecutionConfig,
)
from xsranker.execution.pipeline import SymbolInputs
from xsranker.gate.config import GateThresholds
from xsranker.harness.adapter import HarnessAdapter
from xsranker.signals.spec import SignalArm

EXEC = ExecutionConfig(
    k_per_leg=2, participation_cap=0.01, gross_floor_inr=1_000.0, sector_cap_divisor=2
)
COST = CostCorridorConfig(
    mode=FIXED_SPREAD,
    optimistic_spread_multiplier=1.0,
    pessimistic_spread_multiplier=3.0,
    optimistic_spread_bps=5.0,
    pessimistic_spread_bps=18.0,
)
THRESH = GateThresholds(
    null_percentile=95.0,
    dsr_min=0.95,
    pbo_max=0.20,
    cpcv_median_min=0.0,
    positive_fraction_min=0.5,
    absolute_net_min=0.0,
    near_margin_percentile=2.0,
    near_margin_prob=0.02,
    near_margin_sharpe=0.02,
    near_margin_net=0.0002,
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


def test_run_arm_reports_null_health() -> None:
    """The per-arm null-health aggregate is populated and healthy on a feasible panel — the
    observable early-warning for the rejection loop (replaces the suppressed per-attempt spam)."""
    r = np.random.default_rng(11)
    run = run_arm(
        DAYS,
        _skilled_cross(0.6 + r.random(40)),
        adapter=_adapter(),
        exec_cfg=EXEC,
        cost_cfg=COST,
        cost_model=_adapter().load_cost_model(),
        draws_per_day=25,
        rng=np.random.default_rng(20260711),
    )
    h = run.null_health
    assert h.total_draws == len(run.pessimistic.signal_by_day) * 25  # N nulls per surviving day
    assert h.mean_attempts >= 1.0 and h.max_attempts >= 1
    assert h.ceiling_hits == 0  # no draw exhausted the retry ceiling on a feasible panel
    assert 0.0 <= h.rejection_rate <= 1.0


def test_build_symbol_days_can_skip_the_dead_cs_spread(build_ohlcv) -> None:
    """compute_spread=False drops the now-dead Corwin-Schultz estimate (the live FIXED corridor
    ignores it); the same days are produced, each with spread 0.0."""
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(25)]
    series = build_ohlcv("SYM", dates, bars_per_day=6)
    common = {
        "arm": SignalArm.A,
        "entry_minute": 575,
        "atr_period": 20,
        "sector": "IT",
        "long_eligible": True,
        "short_eligible": True,
        "circuit_locked_by_day": {},
        "adapter": _adapter(),
    }
    with_cs = build_symbol_days("SYM", series, **common, compute_spread=True)
    without_cs = build_symbol_days("SYM", series, **common, compute_spread=False)
    assert without_cs and with_cs.keys() == without_cs.keys()
    assert all(sd.spread == 0.0 for sd in without_cs.values())


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


def _cost_cfg(mode: str, opt_bps: float, pess_bps: float, deploy: float) -> CostCorridorConfig:
    return CostCorridorConfig(
        mode=mode,
        optimistic_spread_multiplier=1.0,
        pessimistic_spread_multiplier=3.0,
        optimistic_spread_bps=opt_bps,
        pessimistic_spread_bps=pess_bps,
        deployment_notional_inr=deploy,
    )


def _two_name_book(notional: float) -> tuple[Book, dict[str, SymbolDay]]:
    book = Book(
        (Position("L", Side.LONG, "S1", 1.0, notional),),
        (Position("S", Side.SHORT, "S2", 1.0, notional),),
        gross_inr=notional,
    )
    by_symbol = {"L": _sym_day("L", "S1", -0.03, 0.0), "S": _sym_day("S", "S2", 0.03, 0.0)}
    return book, by_symbol


def test_fixed_spread_charges_fees_at_deployment_notional_not_book_notional() -> None:
    """The live corridor prices the size-aware fees at the ₹10k DEPLOYMENT notional, independent
    of the (liquidity-max) book notional the truncation produced -> 10.605 bps fees + spread."""
    from xsranker.backtest.harness import _position_costs

    cm = _adapter().load_cost_model()
    cfg = _cost_cfg(FIXED_SPREAD, 1.0, 5.0, 10_000.0)
    book_big, by_big = _two_name_book(5_000_000.0)  # huge book notional
    book_sml, by_sml = _two_name_book(50_000.0)  # small book notional
    opt_big, pess_big = _position_costs(book_big, by_big, cm, cfg, 0.01)
    opt_sml, _ = _position_costs(book_sml, by_sml, cm, cfg, 0.01)
    # cost fraction is INDEPENDENT of the book notional (fees priced at deployment size)
    assert opt_big["L"] == opt_big["S"] == opt_sml["L"]
    # equals verified fees(₹10k)=10.605 bps + the pinned spread, at both bounds
    assert abs(opt_big["L"] * 1e4 - 11.605) < 5e-2
    assert abs(pess_big["L"] * 1e4 - 15.605) < 5e-2


def test_deployment_notional_pricing_is_strictly_more_conservative_than_book() -> None:
    """Teeth for the fix: pricing fees at ₹10k costs MORE (bps) than at the old liquidity-max
    book notional — the understatement the re-pin corrects (the ₹20 brokerage cap only bites large).
    """
    from xsranker.backtest.harness import _position_costs

    cm = _adapter().load_cost_model()
    book, by_symbol = _two_name_book(1_000_000.0)
    small_deploy = _cost_cfg(FIXED_SPREAD, 1.0, 5.0, 10_000.0)
    large_deploy = _cost_cfg(FIXED_SPREAD, 1.0, 5.0, 1_000_000.0)
    opt_small, _ = _position_costs(book, by_symbol, cm, small_deploy, 0.01)
    opt_large, _ = _position_costs(book, by_symbol, cm, large_deploy, 0.01)
    assert opt_small["L"] > opt_large["L"]  # ₹10k deployment pays materially more fees than ₹1M


def test_cs_mode_still_prices_fees_at_book_notional_for_regen_fidelity() -> None:
    """CS mode (candidate-#1 regen) IGNORES the deployment notional and prices at the book
    notional, so the historical streams stay byte-reproducible — changing book size changes cost."""
    from xsranker.backtest.harness import _position_costs

    cm = _adapter().load_cost_model()
    cfg = _cost_cfg(CORWIN_SCHULTZ, 1.0, 3.0, 10_000.0)  # deployment_notional is inert in CS mode
    book_a, by_a = _two_name_book(100_000.0)
    book_b, by_b = _two_name_book(1_000_000.0)
    opt_a, _ = _position_costs(book_a, by_a, cm, cfg, 0.01)
    opt_b, _ = _position_costs(book_b, by_b, cm, cfg, 0.01)
    assert opt_a["L"] != opt_b["L"]  # CS reads the book notional -> size-dependent (unchanged)


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
