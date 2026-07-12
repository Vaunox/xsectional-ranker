"""Durable, fail-closed trial ledger (R2 fix) — teeth for Inviolable Rule 4.

The load-bearing test is the FAIL-CLOSED one: if a prior candidate's streams are missing at
gate time, the gate must go red (never a silently-undercounted effective-N). Both the guard
(``verify_ledger_integrity``) and the gate entry point (``run_program``) are exercised.
"""

from __future__ import annotations

import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from xsranker.backtest.harness import ArmRun, DayStreams
from xsranker.backtest.report import run_program
from xsranker.core.config import load_settings
from xsranker.gate.config import GateThresholds
from xsranker.harness.adapter import HarnessAdapter, TrialLedger
from xsranker.ledger.config import load_ledger_config
from xsranker.ledger.persistence import (
    LedgerIntegrityError,
    LedgerManifest,
    arm_trial_id,
    load_manifest,
    verify_ledger_integrity,
    write_manifest,
)

_THRESH = GateThresholds(
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
_DAYS = [date(2024, 1, 1) + timedelta(days=i) for i in range(5)]


def _ledger(dir_: Path) -> TrialLedger:
    return TrialLedger(dir_)


def _mk_arm() -> ArmRun:
    """A structurally-valid ArmRun; its contents never matter — the guard fires first."""
    ds = DayStreams(dict.fromkeys(_DAYS, 0.001), dict.fromkeys(_DAYS, (0.0, 0.0)))
    return ArmRun(
        optimistic=ds,
        pessimistic=ds,
        trading_days=len(_DAYS),
        signal_day_drops=0,
        null_draw_day_drops=0,
        short_ban_fires=0,
    )


# --------------------------------------------------------------------------- #
# The manifest + trial-id scheme                                                #
# --------------------------------------------------------------------------- #


def test_arm_trial_id_scheme() -> None:
    assert arm_trial_id("cand1", "A-Z", 30) == "cand1__A-Z__30"
    assert arm_trial_id("cand1", "A-Z", 30, cost="fees+ar") == "cand1__A-Z__30__fees+ar"


def test_manifest_roundtrip_and_required_ids() -> None:
    m = LedgerManifest(candidates={"cand1": ("cand1__A__15", "cand1__A__30")})
    assert m.required_trial_ids == ("cand1__A__15", "cand1__A__30")
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "MANIFEST.yaml"
        write_manifest(p, m)
        assert load_manifest(p).candidates == {"cand1": ("cand1__A__15", "cand1__A__30")}


def test_load_manifest_missing_file_is_empty() -> None:
    with tempfile.TemporaryDirectory() as d:
        assert load_manifest(Path(d) / "nope.yaml").required_trial_ids == ()


def test_committed_repo_manifest_loads_and_is_empty_pre_1b() -> None:
    """The real ledger/MANIFEST.yaml is committed, parses, and is empty until 1B arms it."""
    cfg = load_ledger_config(load_settings())
    assert cfg.dir.name == "ledger"
    assert cfg.manifest_path.name == "MANIFEST.yaml"
    assert load_manifest(cfg.manifest_path).required_trial_ids == ()


# --------------------------------------------------------------------------- #
# The fail-closed guard                                                         #
# --------------------------------------------------------------------------- #


def test_verify_passes_when_all_required_present() -> None:
    with tempfile.TemporaryDirectory() as d:
        led = _ledger(Path(d))
        led.log_trial(
            strategy="cand1__A__15", params={}, returns=[0.1, -0.2], trial_id="cand1__A__15"
        )
        verify_ledger_integrity(led, LedgerManifest(candidates={"cand1": ("cand1__A__15",)}))


def test_verify_fails_closed_when_required_missing() -> None:
    """THE TEETH: an empty ledger + a manifest that requires a stream -> raise."""
    with tempfile.TemporaryDirectory() as d:
        led = _ledger(Path(d))  # empty
        manifest = LedgerManifest(candidates={"cand1": ("cand1__A__15", "cand1__A-Z__30")})
        with pytest.raises(LedgerIntegrityError, match="fails closed"):
            verify_ledger_integrity(led, manifest)


def test_verify_fails_closed_when_present_but_empty_stream() -> None:
    """A present-but-EMPTY stream is silently dropped by the participation ratio -> also fail."""
    with tempfile.TemporaryDirectory() as d:
        led = _ledger(Path(d))
        led.log_trial(strategy="cand1__A__15", params={}, returns=[], trial_id="cand1__A__15")
        with pytest.raises(LedgerIntegrityError, match="EMPTY"):
            verify_ledger_integrity(led, LedgerManifest(candidates={"cand1": ("cand1__A__15",)}))


# --------------------------------------------------------------------------- #
# The GATE fails closed (run_program) — the operator's exact requirement         #
# --------------------------------------------------------------------------- #


def test_run_program_fails_closed_on_missing_prior_candidate() -> None:
    """Stub the ledger empty + require a prior candidate -> the GATE goes red (before any DSR)."""
    adapter = HarnessAdapter(load_settings())
    manifest = LedgerManifest(candidates={"cand1": ("cand1__A__15",)})
    with tempfile.TemporaryDirectory() as d:
        led = _ledger(Path(d))  # empty — cand1's streams are missing
        with pytest.raises(LedgerIntegrityError):
            run_program(
                {"A": _mk_arm(), "B": _mk_arm()},
                ledger=led,
                adapter=adapter,
                thresholds=_THRESH,
                cpcv_groups=5,
                cpcv_k=2,
                periods_per_year=252.0,
                pbo_splits=4,
                manifest=manifest,
            )
        assert led.count() == 0  # failed closed BEFORE charging anything


def test_run_program_without_manifest_is_unguarded() -> None:
    """No manifest -> the guard is a no-op (existing callers are unaffected)."""
    adapter = HarnessAdapter(load_settings())
    with tempfile.TemporaryDirectory() as d:
        led = _ledger(Path(d))
        # Reaches the charging step (no LedgerIntegrityError); it may later raise on the tiny
        # synthetic CPCV, so we only assert the guard did not fire and arms were charged.
        try:
            run_program(
                {"A": _mk_arm(), "B": _mk_arm()},
                ledger=led,
                adapter=adapter,
                thresholds=_THRESH,
                cpcv_groups=2,
                cpcv_k=1,
                periods_per_year=252.0,
                pbo_splits=2,
            )
        except LedgerIntegrityError:  # pragma: no cover - must never happen here
            pytest.fail("unguarded run_program must not raise LedgerIntegrityError")
        except Exception:
            pass
        assert led.count() == 2  # both arms were charged (the guard did not block)
