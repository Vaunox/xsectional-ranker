# Deep Dive 04 — Validation & Gate Layer (Layer 3)

*The imported gate, unchanged, plus one new benchmark layer. The discipline is inherited verbatim; only the null is different.*

## Scope
The kill-gate criteria (imported, frozen), the beat-random-percentile benchmark (new), DSR deflation across all arms, the phased verdict logic, and the logged diagnostics.

## The gate — reuse the harness, change only the benchmark
Every criterion from the predecessor applies unchanged (CPCV median path-Sharpe, DSR ≥ threshold vs effective-N, PBO, path-positivity/percentile, ~~profit factor / expectancy~~, robustness battery, ~~regime stability~~), computed by the frozen imported harness. (**Correction, 2026-07-11:** profit factor / expectancy / regime stability are *not* in the frozen harness — resolved as logged diagnostics, not gates; see "Resolved open questions" below.) **One thing is added, nothing is edited:** the benchmark against which "positive" is judged is not zero but the **Global Null Panel percentile.** A study's realized net return on each surviving day is compared to that day's null distribution; the signal must clear a pre-registered percentile, not merely beat zero.

## DSR deflation across arms (honest multiple-testing)
The trial ledger charges every arm: **2 signals (A, A-Z) × the window sweep {15, 30, 45}**, plus any sizing/neutrality choices that were ever run. The DSR bar rises for every swing taken; the winning arm is never reported as if it were the only test. The imported effective-N clustering collapses correlated arms (the three windows of one signal cluster tightly; A vs A-Z are more distinct) — never a raw count.

## The null is a distribution, not a point
Because the baseline endures the identical execution model, its per-day outcome is itself noisy. So the null is **N draws per day** (Deep Dive 02); the signal must beat a real percentile of that distribution. A single random draw would be its own overfitting-by-luck hazard. This percentile logic feeds the DSR/PBO honestly rather than a hand-set zero line.

## Phased verdict logic
- **Phase 1 (survivor cache) — Upper-Bound Smoke Test.** Survivorship *subsidizes* the long leg (signal longs the gap-downs that survivor-only deletes).
  - **KILL → hyper-trustworthy.** Failed even while subsidized → walk away for the cost of a branch. This is the expected, valuable outcome.
  - **PASS → provisional / untrustworthy.** Earns *only* the right to trigger Phase 2. Never greenlights production.
- **Phase 2 (point-in-time crucible) — the only gate authorized to issue a true PASS.** Rerun identically on the clean mid-cap universe; a pass here greenlights a production repo, a kill closes the program honestly.

## Logged diagnostics (informational, not gates)
- **Market-day conditioning** — split P&L by index intraday direction; a residual-tilt tell. Note: OLS attribution averages out *conditional* tail-beta, so this is a diagnostic, not the neutrality mechanism (truncation is).
- **Post-hoc sector concentration** — flag P&L on days a leg was sector-clustered; secondary check behind the ex-ante cap.
- **Circuit-flag fraction**, **short-ban fire-rate** (expected ~0% in Phase 1), **day-drop fraction**, **effective-N per checkpoint**.

## Exploration-grade stamping
Every Phase-1 result carries the survivorship-inflated-upper-bound stamp; nothing enters a verdict scorecard until the Phase-2 crucible. The held-out portion of the universe is reserved to confirm a positive only — never mined.

## STOP-and-flag
Any PASS / near-threshold / INSUFFICIENT / contradiction stops for operator ruling before recording — the sign-off gate is real, as in the predecessor.

## Resolved open questions (operator-ruled 2026-07-11, before any run)

**DSR x null-percentile composition (Ruling 1) — resolved.** The two corrections act on *orthogonal axes*, so both apply without double-penalty or double-credit. The null-percentile strips *per-day execution/structure/liquidity/survivorship luck* (the edge ranked and random books both enjoy), isolating **selection skill**; the DSR strips *cross-arm search luck* (the multiple-testing bar). Mechanically: each arm's per-day quantity is redefined as **net minus the null median** (the excess-over-null stream, the selection alpha), and *that* excess — never the raw net — feeds the imported CPCV/DSR/PBO. Deflating the raw net would bank the survivorship subsidy as alpha; deflating the excess cannot. The beat-random percentile is the *per-arm* significance bar; the DSR *owns* cross-arm multiplicity, so the percentile is **not** inflated for the arm count. Impl: `src/xsranker/gate/` (`benchmark.excess_over_null_median` → the excess stream; `arm.evaluate_arm` runs the imported criteria on it). Teeth: `tests/test_gate_arm.py::test_positive_pnl_that_loses_to_the_null_is_killed` — an arm with **positive raw P&L** but negative selection alpha is correctly KILLED.

**Null-percentile threshold selection (proposed; frozen blind at Step 2) — resolved derivation.** The bar derives from a target *per-arm* false-positive tolerance chosen a-priori: beating the P-th percentile ⇒ under H0 (ranked ≈ random) an arm clears it with probability (100 − P)/100, which *is* the per-arm false-positive rate. Proposed **α = 0.05 ⇒ 95th percentile** (the conventional a-priori significance level; the asymmetric false-PASS cost argues against going below the 90th). It is **not** inflated for the 6 arms — the DSR owns multiplicity (above). N (null draws/day) is set for percentile *resolution*: 1000 draws → ~50 in the upper 5% tail, a stable bar. Final blind sign-off at Checkpoint B; committed to config only at Step 2.

**PF / expectancy / regime-stability (Ruling 2) — resolved doc-vs-code discrepancy.** DD04's gate list (§"The gate") named profit factor, expectancy, and regime stability as imported criteria, but they are **absent from the frozen harness** (only `fraction_positive`, CPCV's `tenth_percentile`, and a feature-level `trend_regime` exist). Resolved 2026-07-11 as **logged diagnostics, not gates** — profit factor and expectancy are small new teeth-tested helpers over the net-return stream (`src/xsranker/gate/diagnostics.py`); "regime stability" folds into the market-day-conditioning diagnostic. This **preserves the one-new-criterion rule**: the only new *gate* criterion is beat-random. Recorded so the correction cannot later read as a silent weakening.

**Ledger charging (Ruling 3) — resolved.** The **6 signal×window arms** are the search axes charged to the effective-N ledger; the cost corridor is a mandatory *both-bounds robustness range*, not a selectable search dimension (you don't get to pick the favorable bound), so it is **not** 12 trials. Effective-N clusters the 6 from the actual streams (the three windows of one signal correlate tightly) — a raw "6" surfacing anywhere is a red flag. Impl: `src/xsranker/gate/program.py::charge_arms`.
