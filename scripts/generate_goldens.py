"""Golden-master generator — Deep Dive 03, Check 2 (bit-for-bit reconciliation).

**Where this runs.** The authoritative golden fixtures are *birthed in the
predecessor repo* (``intraday-strategy-lab``) at pinned commit ``0c5c592``, on a
scratch branch that touches ``tests/`` only — never ``src/lab/`` (Deep Dive 03:
regenerate in the predecessor, never here). This exact script and the resulting
``tests/golden/*.json`` are then committed into THIS repo so the regeneration
procedure is self-sufficient and re-runnable without that branch surviving.

**What Check 2 proves.** Both repos ``import lab.*`` — in the predecessor that
resolves to ``src/lab``; here to the byte-identical ``src/vendored/lab``. Each
fixture stores concrete ``inputs`` and the ``outputs`` the vendored function
produced at home. ``tests/test_golden_master.py`` replays the stored inputs
through the vendored function *here* and asserts the result equals the stored
outputs to full tolerance. A mismatch means the numeric stack drifted — hard stop.

The six fixtures cover the five Deep-Dive-03 Check-2 minimums — CPCV path
distribution, DSR at known effective-N, PBO/CSCV, effective-N clustering of a
known correlated group, full round-trip cost — plus a sixth, a seeded Monte-Carlo
robustness golden that exercises the RNG path where the determinism seed most
needs proving (Check 4).

Usage:
    python scripts/generate_goldens.py            # write tests/golden/*.json
    python scripts/generate_goldens.py --check     # recompute + verify, write nothing
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import tempfile
from collections.abc import Callable
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import scipy
from lab.research.trials.ledger import TrialLedger
from lab.research.validation.costs import CostModel
from lab.research.validation.cpcv import combinatorial_purged_cv
from lab.research.validation.metrics import (
    deflated_sharpe_ratio,
    expected_max_sharpe,
    probabilistic_sharpe_ratio,
)
from lab.research.validation.pbo import probability_of_backtest_overfitting
from lab.research.validation.robustness import monte_carlo_sign_flip

IST = ZoneInfo("Asia/Kolkata")
#: Default output dir (this repo's tests/golden). Overridable with --out so the
#: same script can birth fixtures from inside the predecessor's tests/ tree.
DEFAULT_GOLDEN_DIR = Path(__file__).resolve().parents[1] / "tests" / "golden"

# Fixed seeds used ONLY to synthesize the canned inputs, which are then stored
# verbatim in the fixture. The reconciliation test reads stored inputs; it never
# re-draws them — so input reproducibility across repos is irrelevant. (The one
# RNG that IS load-bearing across repos is inside monte_carlo_sign_flip; that
# seed lives in the fixture inputs.)
_INPUT_SEED_CPCV = 101
_INPUT_SEED_PBO = 202
_INPUT_SEED_LEDGER = 303


def _business_days(start: datetime, count: int) -> list[datetime]:
    """``count`` weekday dates at ``start``'s date, forward from ``start``."""
    days: list[datetime] = []
    cur = start
    while len(days) < count:
        if cur.weekday() < 5:
            days.append(cur)
        cur += timedelta(days=1)
    return days


def _session_windows(n: int) -> tuple[list[str], list[str]]:
    """``n`` (entry 09:15, exit 15:20) IST windows on consecutive weekdays, ISO."""
    day0 = datetime(2024, 1, 1, tzinfo=IST)
    days = _business_days(day0, n)
    entries = [datetime.combine(d.date(), time(9, 15), tzinfo=IST).isoformat() for d in days]
    exits = [datetime.combine(d.date(), time(15, 20), tzinfo=IST).isoformat() for d in days]
    return entries, exits


def _parse_times(iso: list[str]) -> list[datetime]:
    return [datetime.fromisoformat(s) for s in iso]


# --------------------------------------------------------------------------- #
# Fixture 1 — CPCV path-distribution                                          #
# --------------------------------------------------------------------------- #
def build_cpcv() -> dict[str, Any]:
    rng = np.random.default_rng(_INPUT_SEED_CPCV)
    n = 36
    returns = (rng.normal(0.0004, 0.01, n)).tolist()
    entries, exits = _session_windows(n)
    return {
        "returns": returns,
        "entry_times": entries,
        "exit_times": exits,
        "n_groups": 6,
        "k_test_groups": 2,
        "periods_per_year": 252.0,
    }


def compute_cpcv(inp: dict[str, Any]) -> dict[str, Any]:
    result = combinatorial_purged_cv(
        inp["returns"],
        _parse_times(inp["entry_times"]),
        _parse_times(inp["exit_times"]),
        n_groups=int(inp["n_groups"]),
        k_test_groups=int(inp["k_test_groups"]),
        periods_per_year=float(inp["periods_per_year"]),
    )
    return {
        "path_sharpes": list(result.path_sharpes),
        "n_paths": result.n_paths,
        "n_finite_paths": result.n_finite_paths,
        "median_path_sharpe": result.median_path_sharpe,
        "positive_fraction": result.positive_fraction,
        "tenth_percentile": result.tenth_percentile,
    }


# --------------------------------------------------------------------------- #
# Fixture 2 — DSR at a known effective-N (+ PSR, expected-max-Sharpe)          #
# --------------------------------------------------------------------------- #
def build_dsr() -> dict[str, Any]:
    return {
        "observed_sharpe": 0.145,
        "n": 480,
        "skew": -0.35,
        "kurtosis": 4.8,
        "effective_trials": 7.0,
        "trial_sharpe_std": 0.06,
        "benchmark_sharpe": 0.0,
    }


def compute_dsr(inp: dict[str, Any]) -> dict[str, Any]:
    return {
        "deflated_sharpe_ratio": deflated_sharpe_ratio(
            float(inp["observed_sharpe"]),
            int(inp["n"]),
            float(inp["skew"]),
            float(inp["kurtosis"]),
            effective_trials=float(inp["effective_trials"]),
            trial_sharpe_std=float(inp["trial_sharpe_std"]),
        ),
        "expected_max_sharpe": expected_max_sharpe(
            float(inp["effective_trials"]), float(inp["trial_sharpe_std"])
        ),
        "probabilistic_sharpe_ratio": probabilistic_sharpe_ratio(
            float(inp["observed_sharpe"]),
            float(inp["benchmark_sharpe"]),
            int(inp["n"]),
            float(inp["skew"]),
            float(inp["kurtosis"]),
        ),
    }


# --------------------------------------------------------------------------- #
# Fixture 3 — PBO via CSCV                                                     #
# --------------------------------------------------------------------------- #
def build_pbo() -> dict[str, Any]:
    rng = np.random.default_rng(_INPUT_SEED_PBO)
    n_periods, n_configs = 24, 4
    matrix = rng.normal(0.0, 0.01, (n_periods, n_configs))
    matrix[:, 0] += 0.002  # one config carries a mild in-sample edge
    entries, exits = _session_windows(n_periods)
    return {
        "performance_matrix": matrix.tolist(),
        "entry_times": entries,
        "exit_times": exits,
        "n_splits": 8,
    }


def compute_pbo(inp: dict[str, Any]) -> dict[str, Any]:
    result = probability_of_backtest_overfitting(
        inp["performance_matrix"],
        _parse_times(inp["entry_times"]),
        _parse_times(inp["exit_times"]),
        n_splits=int(inp["n_splits"]),
    )
    return {"pbo": result.pbo, "logits": result.logits.tolist()}


# --------------------------------------------------------------------------- #
# Fixture 4 — effective-N clustering of a known correlated group              #
# --------------------------------------------------------------------------- #
def build_ledger() -> dict[str, Any]:
    rng = np.random.default_rng(_INPUT_SEED_LEDGER)
    length = 200
    base_a = rng.normal(0.0, 0.01, length)
    base_b = rng.normal(0.0, 0.01, length)
    streams: list[list[float]] = []
    # Two tight clusters of 4 near-duplicates each => effective-N ~2, raw 8.
    for _ in range(4):
        streams.append((base_a + rng.normal(0.0, 1e-5, length)).tolist())
    for _ in range(4):
        streams.append((base_b + rng.normal(0.0, 1e-5, length)).tolist())
    return {"streams": streams}


def compute_ledger(inp: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        ledger = TrialLedger(Path(tmp) / "trials")
        for i, stream in enumerate(inp["streams"]):
            ledger.log_trial("G", {"i": i}, stream, trial_id=f"{i:04d}")
        return {
            "count": ledger.count(),
            "effective_trials": ledger.effective_trials(),
            "trial_sharpe_std": ledger.trial_sharpe_std(),
        }


# --------------------------------------------------------------------------- #
# Fixture 5 — full round-trip cost (cost config pinned INTO the fixture)       #
# --------------------------------------------------------------------------- #
def build_cost() -> dict[str, Any]:
    # The exact statutory rates behind the hand-worked ₹182.4452 fixture, pinned
    # into the golden so the reconciliation is independent of config_dir paths
    # (Resolution D). Mirrors config/costs.yaml.
    return {
        "cost_config": {
            "brokerage": {"rate": 0.0003, "cap": 20.0},
            "stt": {"sell_rate": 0.00025},
            "exchange_txn": {"rate": 0.0000297},
            "sebi_turnover": {"rate": 0.000001},
            "stamp": {"buy_rate": 0.00003},
            "gst": {"rate": 0.18},
            "slippage": {
                "base_rate": 0.0005,
                "impact_coefficient": 0.002,
                "participation_cap": 0.10,
                "stress_multiplier": 3.0,
            },
        },
        "notional": 100_000.0,
    }


def compute_cost(inp: dict[str, Any]) -> dict[str, Any]:
    cm = CostModel.from_mapping(inp["cost_config"])
    notional = float(inp["notional"])
    return {
        "round_trip_cost": cm.round_trip_cost(notional, notional),
        "round_trip_cost_fraction": cm.round_trip_cost_fraction(notional),
        "round_trip_cost_fraction_stressed": cm.round_trip_cost_fraction(notional, stressed=True),
        "round_trip_cost_fraction_participation_5pct": cm.round_trip_cost_fraction(
            notional, participation=0.05
        ),
        "slippage_rate_at_cap": cm.slippage_rate(cm.slippage_participation_cap),
    }


# --------------------------------------------------------------------------- #
# Fixture 6 — seeded Monte-Carlo robustness (the RNG / seed-lock golden)       #
# --------------------------------------------------------------------------- #
def build_mc() -> dict[str, Any]:
    # A concrete return stream with a clear positive edge; the fraction beaten is
    # produced by np.random.default_rng(seed) INSIDE the vendored function, so this
    # fixture is the load-bearing cross-repo RNG reproducibility check.
    # A modest edge (per-period Sharpe ~0.1) so the beaten fraction lands strictly
    # in (0, 1): the exact value is set by the 2000 sign-flip vectors drawn from
    # np.random.default_rng(seed) INSIDE the vendored function, making this the
    # load-bearing cross-repo RNG / seed-lock golden. A degenerate 0.0/1.0 would
    # pass even under RNG drift and prove nothing.
    rng = np.random.default_rng(999)
    returns = rng.normal(0.001, 0.012, 150).tolist()
    return {"returns": returns, "n_shuffles": 2000, "seed": 20260711}


def compute_mc(inp: dict[str, Any]) -> dict[str, Any]:
    return {
        "beaten_fraction": monte_carlo_sign_flip(
            inp["returns"], n_shuffles=int(inp["n_shuffles"]), seed=int(inp["seed"])
        )
    }


# --------------------------------------------------------------------------- #
# Registry + driver                                                           #
# --------------------------------------------------------------------------- #
#: name -> (build_inputs, compute). The reconciliation test imports COMPUTERS.
BUILDERS: dict[str, Callable[[], dict[str, Any]]] = {
    "cpcv_path_distribution": build_cpcv,
    "dsr_known_effective_n": build_dsr,
    "pbo_cscv": build_pbo,
    "effective_n_correlated_group": build_ledger,
    "round_trip_cost": build_cost,
    "monte_carlo_sign_flip_seeded": build_mc,
}
COMPUTERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "cpcv_path_distribution": compute_cpcv,
    "dsr_known_effective_n": compute_dsr,
    "pbo_cscv": compute_pbo,
    "effective_n_correlated_group": compute_ledger,
    "round_trip_cost": compute_cost,
    "monte_carlo_sign_flip_seeded": compute_mc,
}


def _meta() -> dict[str, Any]:
    return {
        "predecessor_sha": "0c5c592b9bc80525625597906cdaf8d7f203bb13",
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "generated_by": "scripts/generate_goldens.py",
        "note": "Birth in predecessor repo @ pinned SHA; verify in this repo (Check 2).",
    }


def write_all(golden_dir: Path) -> None:
    golden_dir.mkdir(parents=True, exist_ok=True)
    for name, build in BUILDERS.items():
        inputs = build()
        outputs = COMPUTERS[name](inputs)
        payload = {"name": name, "meta": _meta(), "inputs": inputs, "outputs": outputs}
        path = golden_dir / f"{name}.json"
        # Force LF regardless of OS so goldens are byte-stable across platforms
        # (Windows write_text would otherwise emit CRLF and desync the fixtures).
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
        )
        print(f"wrote {path}")


def check_all(golden_dir: Path) -> int:
    failures = 0
    for name in BUILDERS:
        path = golden_dir / f"{name}.json"
        if not path.exists():
            print(f"MISSING {name}")
            failures += 1
            continue
        stored = json.loads(path.read_text(encoding="utf-8"))
        recomputed = COMPUTERS[name](stored["inputs"])
        if json.dumps(recomputed, sort_keys=True) != json.dumps(stored["outputs"], sort_keys=True):
            print(f"DRIFT   {name}")
            failures += 1
        else:
            print(f"ok      {name}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="recompute + verify, write nothing")
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_GOLDEN_DIR, help="golden output directory"
    )
    args = parser.parse_args()
    if args.check:
        return check_all(args.out)
    write_all(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
