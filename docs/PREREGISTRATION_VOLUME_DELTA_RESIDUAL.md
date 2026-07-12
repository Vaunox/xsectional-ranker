# Pre-Registration — V_resid: Price-Orthogonal Proxy Cumulative Volume Delta

> **STATUS: FROZEN — operator sign-off 2026-07-12. BLIND.**
> A **new signal** (per the operator's D8-STOP ruling), not a tweak of the retired V/V-A. Every
> parameter was pinned **BLIND** before any V_resid verdict run; **D8-on-V_resid passed** (§7),
> and this freeze **precedes** the single verdict run (a strictly later commit — the provenance
> proof that the bar preceded the experiment). Successor to candidate #2's V/V-A, which D8
> **retired pre-verdict** (substantially momentum, not an independent flow axis — see
> RESEARCH_FINDINGS). `src/vendored/` pristine.

---

## 0. Why this signal exists (the D8 disposition of V/V-A)

D8 (blind, pre-verdict) found that raw **V** and abnormal **V-A** rank the cross-section
**~0.72–0.75 (Spearman)** like the morning open→entry return — i.e. **substantially
volume-weighted momentum**, because a bar's close-vs-open sign (which signs V) is itself a price
measure. That is the 0.5–0.8 STOP band. It cleared the *other* bar decisively — **independent of
candidate #1's gap** (|rank-corr| ≤ 0.13). So the flow axis is real but **price-contaminated**;
V_resid **removes the price component** to isolate the ~47% residual flow variance that is the
signal we actually wanted. This is a *removal* of a known leak, not an addition of price.

## 1. Signal (blind, a-priori, mechanism-first)

**V_resid.** For each day, across the eligible cross-section, fit an ordinary least-squares
regression of raw **V** on the **morning return** (open→entry) and **rank on the residual**:

```
V_resid(name, day) = V(name, day) − ( a_day + b_day · morning_return(name, day) )
```

where `a_day, b_day` are that day's cross-sectional OLS coefficients. The residual is orthogonal
(least-squares) to the morning return **by construction**, so ranking on it isolates directional
flow the price move does not explain — *"was there more buying/selling pressure than the morning
price move alone accounts for?"* — which **is** the a-priori TWAP/VWAP slice-persistence
mechanism, with the price leak removed. `src/xsranker/signals/volume_delta.py::cross_sectional_residual`.

- **V (raw)** = `(ΣV_up − ΣV_down) / ΣV_total`, bars classed by their own close-vs-open (flat →
  denominator only), over the window bars with minute ≤ `entry_minute` (the frozen
  `entry_window_value`/`hold_return` convention).
- **morning return** = `entry_window_return` (open→entry), the same window and entry V uses.
- **Single signal.** V_resid replaces the retired V/V-A — there is **no raw-vs-abnormal split**
  (V-A's trailing baseline is a distinct axis, retired with V-A). One signal × 3 windows = **3
  arms**. Per the operator: run once; do **not** run V and V_resid and pick the winner.

## 2. Direction + mechanism (CONTINUATION) + the hard constraint

**CONTINUATION** — LONG the highest V_resid (most residual net-buying pressure), SHORT the
lowest. Mechanism: institutional VWAP/TWAP order-slicing persists intra-session; the *residual*
(price-orthogonal) one-sided flow is the cleanest read of an unfinished parent order. **HARD
CONSTRAINT (unchanged):** direction is signed by flow (`ΣV_up − ΣV_down`), never a price move;
the residualization only *removes* the price-explained part — it never re-signs on price.

## 3. Measurement window + point-in-time

Windows swept `{15, 30, 45}`. V and the morning return are both known at entry and prefix-
invariant (teeth green on V). The cross-sectional residual uses **only that day's cross-section**
(all values known at entry), so it adds **no** look-ahead — it inherits V's and the morning
return's point-in-time property. Days with < 10 eligible names are dropped (a degenerate
cross-section can't be residualized); a constant control on a day degenerates to a demean.

## 4. Entry / exit / execution / cost — INHERITED (step-2 standard, unchanged)

Entry at window close, hold to session close; `k=5`; risk-parity sizing; Execution-Aware Dollar
Neutrality; ⌈k/2⌉ sector cap; dual masks; circuit filter; gross floor ₹100,000. **Cost corridor =
the live standard: verified fees + fixed 5 bps (opt) / 18 bps (pess), impact 0, no Corwin-Schultz**
(`config` `cost.mode: fixed_spread`). `sd.spread` (CS) is not computed for this path
(`compute_spread=False`).

## 5. The null + the gate — INHERITED, unchanged

Global Null Panel (seed 20260711, N=1000, feasible ⌈k/2⌉-capped disjoint, 0% zero-pad; null-health
telemetry live). Gate: beat-random ≥ 95th on the excess-over-null stream; DSR ≥ 0.95; CPCV median
> 0; positive-fraction > 0.5; PBO ≤ 0.20; **absolute-net > 0 per bound**. CPCV 6/2, PBO 16, 252/yr.

## 6. Cumulative ledger (Rule 4) + the V/V-A charge question (flag)

V_resid's DSR deflates by the **cumulative** cluster-adjusted effective-N: candidate #1's **6
durably-committed arms** (`ledger/`, the fail-closed guard is armed) **+ V_resid's 3 arms**. The
regeneration + fail-closed persistence (R2) is already committed, so the cumulative charge is
real and reproducible at gate time.

**Ledger policy (operator-ruled 2026-07-12) — the return-blind-screen bright line.** The
D8-screened V/V-A are **NOT charged** to the effective-N ledger. The rationale is *statistical,
not bookkeeping*: D8 screens on **correlation with momentum — a criterion blind to returns.** A
return-blind, pre-registered, bands-fixed-in-advance screen never sees performance, so it
**cannot select for a lucky pass**, and increasing the probability of a false PASS is exactly what
effective-N exists to price. (The naïve "no return stream was persisted" reasoning is *wrong* — it
is a bookkeeping fact one could dodge by simply not saving streams; the correct test is whether the
step could fish for a good result.)

> **STANDING LEDGER POLICY (every future candidate).**
> - A construction **screened out on a return-blind, pre-registered criterion** — D8 independence,
>   prefix-invariance, eligibility, data-integrity — is **NOT charged.** None of these can fish for
>   a pass (they never see returns).
> - A construction that was **RUN and evaluated on returns is CHARGED, always, even if discarded.**
>   Example: had we run V, seen it fail, and *then* tried V_resid, that is a second bite at
>   performance and must be charged. (Recorded identically in `PROGRESS.md`.)

## 7. Hard pre-run gates (blind)

1. **D8 re-run on V_resid — PASSED (2026-07-12).** corr vs morning return **Pearson = −0.000**
   (exactly — the OLS residual is linearly orthogonal to the regressor by construction; verified,
   not assumed), **Spearman ~0.11–0.13** (independent band); corr vs candidate #1's gap **|ρ| ≤
   0.03** (independent, stronger than V's −0.13). Both bands cleared. (`scripts/d8_independence.py`.)

   > **Limitation (honest scoping — do not over-claim).** OLS removes only the **linear**
   > price-explained component, so V_resid is **linearly** orthogonal to the morning return
   > (Pearson ≈ 0 by construction) — **not momentum-free in every sense.** A small **nonlinear**
   > rank remnant is expected and remains (Spearman ~0.11–0.13, well inside the < 0.5 band but not
   > zero). State V_resid as *"flow orthogonal to linear morning momentum,"* never *"all momentum
   > removed."* This bounds the independence claim; it does not change the verdict logic.
2. **Prefix-invariance** (inherited from V + the same-day cross-sectional residual adds no lookahead).

## 8. Frozen parameter ledger (pin at sign-off)

| Parameter | Value | Swept? | Charged? |
|---|---|---|---|
| Signal | **V_resid** = per-day XS OLS residual of V on morning-return | — | Yes (1 signal) |
| Direction | **CONTINUATION** (long highest residual, short lowest) | No | — |
| Window | `{15, 30, 45}` | Yes | Yes (3 arms) |
| V base | raw `(ΣV_up−ΣV_down)/ΣV_total`, bars ≤ entry_minute | No | — |
| Control | morning return (open→entry) | No | — |
| Residualization | OLS per day, min 10 names, constant-control→demean | No | — |
| k / sizing / neutrality / caps / masks / floor | inherited | No | — |
| Cost corridor | fees + fixed 5 / 18 bps, impact 0 (no CS) | both bounds | — |
| Null seed / N / gate bars | 20260711 / 1000 / (95th, DSR .95, PBO .20, sign, abs-net) | No | — |
| Ledger | cumulative: cand-#1 6 arms + V_resid 3 (V/V-A NOT charged — §6 flag) | — | Yes |

## 9. The three non-negotiable conditions (operator, 2026-07-12)

1. **Own blind pre-registration** (this doc); freeze, charge to the ledger, **run once** — never
   run V and V_resid and pick the winner.
2. **V and V-A are RETIRED** as pre-registered — no verdict run; the D8 finding is their disposition.
3. **Re-run D8 on V_resid before its verdict run** — corr vs morning return ≈ 0 (verify), corr vs
   gap stays low. (Results brought with this draft.)

**Signed off 2026-07-12; D8-on-V_resid PASSED. The single BLIND verdict run is authorized as a
strictly later commit than this freeze. `src/vendored/` pristine; recorded verdicts untouched.**
