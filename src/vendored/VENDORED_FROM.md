# VENDORED_FROM — provenance manifest for the frozen statistical harness

*This directory is **frozen**. The code under `src/vendored/lab/` is byte-identical
to a pinned commit of the predecessor program `intraday-strategy-lab` and is
**never edited** (Inviolable Rule 5, Deep Dive 03). New behavior is a new layer on
top, reached only through `xsranker.harness.adapter.HarnessAdapter`. Any change to a
file here — even one byte — fails the CI hash tripwire below.*

---

## Source & pin

| Field | Value |
|---|---|
| Source repo | `intraday-strategy-lab` (sibling program) |
| **Pinned commit SHA** | **`0c5c592b9bc80525625597906cdaf8d7f203bb13`** |
| Commit | `Merge pull request #55 from Vaunox/phase5-synthesis` |
| Commit date | 2026-07-10 23:17:19 +0530 |
| Vendored on | 2026-07-11 |
| Vendoring method | `git cat-file blob <SHA>:src/<path>` (exact stored blob bytes, LF) |

### Why HEAD (`0c5c592`), not the `gate-2-harness` tag
The predecessor's `gate-2-harness` tag (`9e8da23`, 2026-07-05) is a **known-buggy**
snapshot of the harness. Between that tag and this pin, the harness modules received
**660 lines of correctness fixes** — including `fix(sharpe): annualize by realized
frequency, not the fixed 18750 constant`, `fix(harness): …PBO alignment, stub guard`,
`refactor(validation): extract shared purge_indices primitive`, and
`fix(validation): close four Phase-2 harness gaps (purge, slippage, robustness)`.
Pinning to the tag would vendor code with fixed-since bugs; HEAD is the hardened
harness on a clean `main`.

### Baseline proven sound at the pin (guardrail, ruling 1)
Before vendoring, the predecessor's own suite was run at this exact commit:

```
$ cd intraday-strategy-lab            # HEAD == 0c5c592, clean working tree
$ OMP_NUM_THREADS=1 .venv/Scripts/python.exe -m pytest
375 passed in 5.35s
```

Environment: Python 3.11.9, numpy 2.4.6, scipy 1.17.1, `OMP_NUM_THREADS=1`,
run 2026-07-11. The baseline is proven, not assumed.

---

## Determinism lock (Check 4)

Golden-master bit-for-bit equality is only meaningful against a locked numeric
stack. These are the **exact** versions the pin resolved under Python 3.11 (the
predecessor's `.python-version`); pinned `==` in `pyproject.toml` and frozen in the
committed `uv.lock`. On Python 3.12 the predecessor lockfile resolves *different*
versions (numpy 2.5.1 / scipy 1.18.0), so the **Python minor is load-bearing** and
pinned to 3.11.

| Dependency | Pinned version |
|---|---|
| Python | 3.11 (3.11.9) |
| numpy | 2.4.6 |
| scipy | 1.17.1 |
| TA-Lib | 0.7.0 *(Phase 2 — backs the vendored `atr`)* |

The Phase-0 statistical harness imports **only** numpy + scipy. **Phase 2** adds the
feature primitives (below), which bring **TA-Lib 0.7.0** (`talib.ATR`); pinned `==`
in `pyproject.toml` + `uv.lock`. TA-Lib's `ATR` is single-threaded Wilder-average C
(no BLAS reduction), so `OMP_NUM_THREADS=1` discipline continues and the `feature_atr`
golden confirms bit-stability.

`OMP_NUM_THREADS=1` (and the OpenBLAS/MKL/NumExpr equivalents) is pinned for golden
runs — in CI env, in `tests/conftest.py`, and asserted by the golden test — to avoid
BLAS reduction-order differences producing a false drift alarm. **Observed golden
drift on this stack is exactly `0.0`** (predecessor-birthed fixtures reconcile
bit-for-bit against local recomputation); the documented tolerance `rtol=0,
atol=1e-12` is the ceiling, not evidence of slop. No tolerance was loosened.

---

## Vendored files (20) — hashes & certifying tests

SHA-256 is the CI tripwire source of truth (`src/vendored/vendored_hashes.txt`, now
20 files); the git blob OID is the pin cross-reference. Paths are relative to
`src/vendored/`. Rows 1–16 are the Phase-0 statistical harness; the last 4 are the
**Phase-2 feature primitives** (same pin, additive).

| File | SHA-256 (prefix) | git blob | Certified by |
|---|---|---|---|
| `lab/__init__.py` | `89b7f089d9cf` | `07ac02dd6dac` | import gate |
| `lab/core/__init__.py` | `97983254283c` | `09c9185f747d` | import gate |
| `lab/core/constants.py` | `19093ddc6576` | `67bf345304df` | `INDIA_TZ` (backtester/robustness) |
| `lab/core/types.py` | `4bd32e2eb60e` | `b066508a9ff0` | `Candle`/`Side`/`BarInterval` (all tests) |
| `lab/research/__init__.py` | `d17a7b9089ef` | `330718c744d9` | import gate |
| `lab/research/trials/__init__.py` | `f7ef51e1fbba` | `70cee4b14a7c` | import gate |
| `lab/research/trials/ledger.py` | `1e7e84ae55a5` | `3a196ec3fd80` | `test_ledger.py`; golden `effective_n_correlated_group` |
| `lab/research/validation/__init__.py` | `99b6071f534b` | `ee83df1f4765` | import gate |
| `lab/research/validation/backtester.py` | `4727434887c1` | `7ffdcc7aef0f` | `test_validation_core.py` (run_backtest, two-engine) |
| `lab/research/validation/costs.py` | `f4c49139ac2f` | `5c88bafeba91` | `test_validation_core.py` (₹182.4452); golden `round_trip_cost` |
| `lab/research/validation/cpcv.py` | `29c123a353a6` | `9c6935c7995d` | `test_cpcv_pbo.py`; golden `cpcv_path_distribution` |
| `lab/research/validation/metrics.py` | `26c24a4198b7` | `785a4359a735` | `test_metrics.py`; golden `dsr_known_effective_n` |
| `lab/research/validation/pbo.py` | `88688dae77d1` | `cdaea46c0083` | `test_cpcv_pbo.py`; golden `pbo_cscv` |
| `lab/research/validation/robustness.py` | `11f470ee402f` | `dfd1370cfae4` | `test_robustness.py`; golden `monte_carlo_sign_flip_seeded` |
| `lab/research/validation/sharpe.py` | `d88ea2df39e0` | `16b9968f810d` | `test_metrics.py` |
| `lab/research/validation/splitter.py` | `babbd7378d27` | `7a0f740d829d` | `test_validation_core.py` (PurgedKFold), `test_cpcv_pbo.py` |
| `lab/data/__init__.py` *(P2)* | `f50acddd2d5c` | `20ef9b6c4da1` | import gate |
| `lab/data/features/__init__.py` *(P2)* | `6973477c3b08` | `718ee37fb47f` | import gate |
| `lab/data/features/ohlcv.py` *(P2)* | `9bd7bf80daa5` | `51388e30315e` | vendored `OHLCV` (bridge target) |
| `lab/data/features/indicators.py` *(P2)* | `ec81b4dd296a` | `1bea0ea17ea8` | goldens `feature_gap`/`feature_atr`/`feature_cross_sectional_rank` + machinery-removal |

Full 64-hex digests: `src/vendored/vendored_hashes.txt` (`sha256sum -c` compatible).

### Phase-2 additive vendoring (feature primitives)
`ohlcv.py` + `indicators.py` are vendored **byte-identical from the same pin** for
three used primitives — `gap`, `atr` (`talib.ATR`), `cross_sectional_rank` — surfaced
on the adapter for Signals A/A-Z and risk-parity sizing. Per the no-cherry-pick freeze
rule, `indicators.py` brings ~40 unused single-name indicators along, **frozen** and
hash-verified; only the **3 used** functions get golden-master reconciliation +
machinery-removal falsification. The adapter converts `xsranker.core.types.OHLCV` →
the vendored `OHLCV` (IST-localizing timestamps for the vendored `.date()` day
grouping; int→float volume) — a load-bearing seam with its own gate-zero-class tests
(`tests/test_ohlcv_bridge.py`). Goldens for the 3 were birthed in the predecessor env
(numpy 2.4.6 / TA-Lib 0.7.0) and reconcile bit-for-bit here.

---

## The adapter surface (the only sanctioned entry points)

`xsranker.harness.adapter.HarnessAdapter` is the **sole** importer of `lab.*`
(enforced by `scripts/check_freeze_boundary.py`). It fronts these 14 vendored
functions; **every one** is covered by machinery-removal falsification (Check 3):

`per_period_sharpe`, `annualized_sharpe`, `probabilistic_sharpe_ratio`,
`expected_max_sharpe`, `deflated_sharpe_ratio`, `combinatorial_purged_cv`,
`cpcv_distribution_summary`, `probability_of_backtest_overfitting`, `trial_ledger`
(`TrialLedger`), `load_cost_model`, `trade_cost_fraction`, `monte_carlo_sign_flip`,
`inject_ohlc_noise`, `fraction_positive`.

---

## The four verification checks (all green)

| Check | What | Where | Result |
|---|---|---|---|
| 1 — predecessor unit tests re-run here | ported hand-computed tests (costs ₹182.4452, DSR/PSR, PBO/CSCV, effective-N, robustness) | `tests/vendored_unit/` | **52 passed** |
| 2 — golden-master reconciliation | 6 fixtures birthed in the predecessor, replayed here bit-for-bit (`atol=1e-12`) | `tests/test_golden_master.py`, `tests/golden/` | **8 passed**, drift `0.0` |
| 3 — machinery-removal falsification | every adapter-surface fn: certifying check passes with machinery, goes red when the vendored entry point is stubbed | `tests/test_machinery_removal.py` | **28 passed** (14 controls + 14 falsifications) |
| 4 — dependency & determinism lock | exact numeric stack pinned; seeded RNG reproducible & config-wired; hash tripwire + freeze boundary have teeth | `tests/test_vendored_freeze.py` | **7 passed** |

CI (`.github/workflows/ci.yml`, `windows-latest` to match the birth platform) runs
the hash tripwire, the freeze boundary, ruff + black + mypy(strict), and the full
pytest gate with `OMP_NUM_THREADS=1`.

### Golden set covers the Deep-Dive-03 Check-2 minimums (+1)
1. CPCV path-distribution — `cpcv_path_distribution.json`
2. DSR at a known effective-N — `dsr_known_effective_n.json`
3. PBO / CSCV — `pbo_cscv.json`
4. effective-N clustering of a known correlated group — `effective_n_correlated_group.json`
5. full round-trip cost — `round_trip_cost.json` (anchors the hand-worked ₹182.4452)
6. **seeded Monte-Carlo robustness** — `monte_carlo_sign_flip_seeded.json` (beaten
   fraction `0.9735`, strictly in (0,1) so the RNG path — where the seed lock most
   needs proving — genuinely determines the value).

### Golden regeneration procedure (self-sufficient)
`scripts/generate_goldens.py` and the fixtures are committed here so regeneration
never depends on the predecessor branch surviving. To regenerate: run the generator
**inside the predecessor repo** at the pin (never here — Deep Dive 03), on a scratch
branch touching `tests/` only:

```
# in intraday-strategy-lab @ 0c5c592, scratch branch scratch/xsr-golden-gen
OMP_NUM_THREADS=1 .venv/Scripts/python.exe tests/golden_gen/generate_goldens.py --out tests/golden
# then copy tests/golden/*.json into this repo and run tests/test_golden_master.py
```

The birth branch `scratch/xsr-golden-gen` (`efaee5a`) records this in the
predecessor; it is **not for merge** and touches `tests/` only — `src/lab/` is
untouched (the frozen harness was never modified to birth its own goldens).

---

## What is NOT vendored (scope boundary)

- **Feature/indicator primitives** (`ATR`, `gap`, `cross_sectional_rank` in the
  predecessor's `data/features/`) — **deferred to Phase 1**, when the data/signal
  layer gives them a real call site (Completion Standard (a)); vendoring them now
  would freeze dead code and pull TA-Lib into Phase 0. They will be vendored from
  **this same SHA**, into this same manifest, using the identical freeze/adapter/
  golden pattern.
- **The predecessor strategy layer** (`research/strategies/*`) — not harness; never
  imported by this program (which builds its own cross-sectional signal layer). Two
  predecessor robustness tests that depend on it are documented-omitted from the
  Check-1 port; the two-engine reconciliation they exercised is still covered by
  `test_validation_core.py` with hand-built targets.

### Carry-forward note (so absence is not read as a gap)
The vendored **single-name** event/vectorized backtester (`backtester.run_backtest`,
`robustness.vectorized_backtest`, `robustness.two_engines_agree`) is frozen and
verified (Check 1) but **not surfaced on the adapter**: this program does not drive
the single-name engine. The cross-sectional book and its **own** two-engine
reconciliation are **new Phase-2 code**. The absence of an x-sectional two-engine
check in Phase 0 is by design, not an omission.

### Phase-0 call sites (so the log does not imply more integration than exists)
The Phase-0 call site for every vendored function is the **verification harness
itself** (the ported tests, the golden runners, the machinery-removal registry).
Real research call sites arrive in Phase 2/3. **GATE 0 = "verified + frozen", not
"wired into the research pipeline."**

---

## Operator sign-off

- [x] **Operator sign-off — GATE 0.** Reviewed and accepted at predecessor pin 0c5c592.
  Provenance independently verified against source: HEAD==pin, gate-2-harness→9e8da23,
  five vendored files byte-identical (blob OID + SHA-256), Sharpe realized-frequency fix
  confirmed present at pin / absent at tag. Baseline (375 predecessor tests green at the
  pin, Py3.11.9 / numpy 2.4.6 / scipy 1.17.1 / OMP_NUM_THREADS=1) confirmed. Four
  verification checks green (104 passed): predecessor tests re-run, golden-master
  reconciliation (drift 0.0, 6 fixtures), machinery-removal falsification (14/14),
  dependency+determinism lock. Vendored tree frozen, hash tripwire + freeze-boundary grep
  armed. Documented omissions reviewed and accepted (1 vacuous-guard removed, 2
  strategy-layer imports deferred; coverage substituted). Harness authorized as frozen
  Layer 0. Phase 1 remains closed pending separate sign-off.

  Signed: build owner (nevesia26@gmail.com), authorized in session — Date: 2026-07-11
