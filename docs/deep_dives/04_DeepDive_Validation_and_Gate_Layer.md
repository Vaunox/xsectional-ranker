# Deep Dive 04 — Validation & Gate Layer (Layer 3)

*The imported gate, unchanged, plus one new benchmark layer. The discipline is inherited verbatim; only the null is different.*

## Scope
The kill-gate criteria (imported, frozen), the beat-random-percentile benchmark (new), DSR deflation across all arms, the phased verdict logic, and the logged diagnostics.

## The gate — reuse the harness, change only the benchmark
Every criterion from the predecessor applies unchanged (CPCV median path-Sharpe, DSR ≥ threshold vs effective-N, PBO, path-positivity/percentile, profit factor / expectancy, robustness battery, regime stability), computed by the frozen imported harness. **One thing is added, nothing is edited:** the benchmark against which "positive" is judged is not zero but the **Global Null Panel percentile.** A study's realized net return on each surviving day is compared to that day's null distribution; the signal must clear a pre-registered percentile, not merely beat zero.

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

## To expand later
- Exact percentile threshold selection and its pre-registration.
- Interaction between the null-percentile benchmark and the imported DSR (both are multiple-testing corrections; ensure no double-penalty or double-credit).
