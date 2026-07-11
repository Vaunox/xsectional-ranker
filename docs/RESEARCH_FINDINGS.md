# Research Findings — Cross-Sectional Intraday Long-Short Ranker (NSE)

> **How this document is maintained.** A *living research paper*, authored as each phase completes — **not pre-filled**. Scaffolds are replaced with real, cost-inclusive, gate-computed numbers and honest verdicts only when produced by an actual validated run. An honest KILL is a complete result.

## Abstract
A market-neutral, cross-sectional intraday ranker (overnight-gap **reversal** — long the biggest gap-downs, short the biggest gap-ups, held entry→close) was tested for a cost-surviving selection edge on an NSE large-cap survivor cache, against a random long-k/short-k null through the identical execution model. **Result: a decisive KILL.** Across both signal variants (A = gap%, A-Z = gap%÷ATR%) × three entry windows {15,30,45 min} × both cost bounds, the ranker is **net-negative** — CPCV path-Sharpes −11 to −29, Deflated Sharpe 0.00, positive-path-fraction 0.00. The signal has no edge; it loses money net of cost. This is a Phase-1 **survivorship-inflated upper bound** (a KILL here is hyper-trustworthy) at **small book size** (see §6). A **null-construction bug** (§7) was found and quarantined; it did not affect this KILL.

## 1. Objective & scope
Does a cross-sectional overnight-gap-**reversal** ranker, held entry-to-close in a market-neutral book, beat a random long-k/short-k selection **net of cost**? Phase 1 is an **upper-bound smoke test** on a survivor cache: a KILL is hyper-trustworthy, a PASS is provisional-only. Exploration-grade throughout.

## 2. Data
NSE 5-minute OHLCV via the inherited Parquet cache (read-only): **49 present-day large-cap survivors** (NIFTY-50 constituents), **2015-02-02 → 2026-07-03** (~2,790 IST trading days). Split/bonus back-adjusted; **cash dividends unadjusted** (bounded ex-div residual, accepted for the upper bound). Regular-session filtered (09:15–15:30 IST; Muhurat/evening bars dropped — a load-bearing correctness step for the entry→close hold return).

### 2.1 Known limitation — survivorship (Phase 1)
The signal longs the biggest gap-downs; survivor-only data **deletes** exactly the catastrophic gap-downs that delisted, so the long leg is inflated. **Phase-1 results are survivorship-inflated upper bounds.** A KILL is therefore *more* trustworthy, not less: the strategy failed even while subsidized.

## 3. Methodology
Imported, frozen statistical harness (CPCV / DSR / PBO / effective-N ledger — verified per Deep Dive 03, reached only through `HarnessAdapter`). New Layer-3 benchmark = Global Null Panel percentile. Execution-Aware Dollar Neutrality (fixed-k, risk-parity weights, weakest-link truncation, gross-floor day-drop). Cost corridor (optimistic 1× / pessimistic 3× Corwin-Schultz spread) composing the frozen Indian intraday cost model. Ex-ante ⌈k/2⌉ sector cap; dual eligibility masks; point-in-time signal + entry→close hold return (no-lookahead, teeth-tested). **Composition (operator ruling):** each arm's per-day quantity = net **minus the null median** (selection alpha); that excess feeds CPCV/DSR/PBO. Full spec: `MASTER_BLUEPRINT.md`, `docs/deep_dives/`.

**Pre-registration (blind, before any result):** k=5, N=1000 null draws/day, null-percentile=95th (α=0.05), DSR≥0.95, PBO≤0.20, CPCV median>0, positive-fraction>0.5 (`pre-registration-frozen` @ `31cc292`); CPCV n_groups=6/k_test=2, PBO n_splits=16, periods_per_year=252 (addendum @ `de6e1c3`); **gross floor RE-FROZEN blind ₹100,000** (`pre-registration-v2` @ `7e6a829`, see §6).

## 4. Signal slate & results scorecard — **KILL (all arms)**
Basis of the verdict is **DSR / CPCV net-negativity** (computed on the signal's own P&L), **not** beat-random percentile (which was measured against a degraded null — §7).

| ID | Signal | Windows | Cost bounds | DSR | CPCV median path-Sharpe | pos-frac | Verdict |
|---|---|---|---|--:|--:|--:|---|
| A | gap% | 15/30/45 | opt & pess | **0.00** | −10.8 … −28.0 | 0.00 | **KILL** |
| A-Z | gap%÷ATR-20 | 15/30/45 | opt & pess | **0.00** | −11.9 … −28.9 | 0.00 | **KILL** |

**Program:** raw arms 6 · effective-N **5.56** (computed from the streams; not a raw 6) · **PBO 0.000** (no differential overfitting — expected when all arms are uniformly unprofitable).

## 5. Study results
### 5.1 — Signal A (raw gap%)
All three windows, both cost bounds: DSR 0.00; CPCV median path-Sharpe −10.8 (w15,opt) → −28.0 (w45,pess); CPCV 10th-percentile −12 → −29; positive-path-fraction 0.00; corridor **DEAD** (fails even the optimistic bound). Beat-random percentile 0.0 (see §7 caveat).

### 5.2 — Signal A-Z (volatility-adjusted gap%÷ATR-20)
Materially identical: DSR 0.00; CPCV median −11.9 → −28.9; positive-fraction 0.00; corridor **DEAD**, both bounds, all windows. Vol-adjustment does not rescue the sign — the reversal premise is simply absent here (net of cost, upper-bound universe).

**Window / cost reading (observation, not conclusion):** the P&L degrades monotonically toward the wider window and the pessimistic bound (CPCV median −10.8 → −28.0 across w15→w45 and opt→pess), i.e. more cost / more holding → more loss. Consistent with a signal that is net-negative before the corridor even widens.

## 6. Capacity finding (first-class result) — the book is structurally small
The extreme-gap selection **systematically picks less-liquid names** (thin names gap most), and the neutral gross is the weakest-link `min` across the leg under a 1%-of-entry-window participation cap. Consequences, all **blind** (computed before any return):
- **Feasible neutral-book gross: median ₹2.7M (w15) → ₹5.3M (w45), fat low tail** (p10 ≈ ₹0.1–0.2M), max ~₹30–60M. The null faces the **same** constraint (median ₹3.97M) — symmetric to the *signal's* book size.
- The **cost model is scale-invariant** (~16–23 bps flat across ₹20k→₹100M; no fixed component) → there is **no cost-mechanical floor**. The only small-size effect is integer-share **lot granularity**.
- The original ₹5M floor (`31cc292`) was **ill-posed** (assumed a cost floor that does not exist) and dropped 48–71% of days; it was superseded blind by **₹100,000** (`pre-registration-v2`) — the minimal floor at which every name forms a real whole-share position — before any return was seen.
- **Stamp glued to the verdict:** even where it survives, the strategy deploys only a **₹3–5M** median neutral book with ~10 bps integer-share tracking error. A real, low-capacity property of the idea that **follows into the Phase-4 mid-caps (likely worse there).**

## 7. Null-construction bug — **Phase-2 BLOCKER (must fix before any beat-random judgment)**
**What:** the random long-k/short-k null selection is **infeasible on ~50% of draws** — a random 5-long/5-short book cannot form a valid **disjoint** pair under the ⌈k/2⌉=3 **sector cap** roughly half the time, so the draw is dropped and contributes **0.0** to that day's null distribution (`build_random_book` → `DayDropped` → `harness.run_arm` appends `0.0`, harness.py:212–213). **The beat-random benchmark was therefore ~half zero-padded.**

**Confirmed mechanism (the seam):** the failure is *"infeasible random draw → 0.0 contribution,"* counted in a **separate** `null_draw_day_drops` counter — it does **not** touch the signal's `signal_day_drops` or the surviving-day set. So drop-rate accounting is **not** corrupted (signal day-drop 5–10% and null-draw-drop 47–56% are independent). The fix seam is precisely `build_random_book` (the null selection must form a valid book every draw — e.g., constrained/resampled selection respecting the sector cap and disjoint legs), **not** the accounting.

**Impact on this KILL: none.** The verdict rests on **absolute net-negativity** (DSR/CPCV computed on the signal's own P&L; with the null median ≈0 from zero-padding, the excess stream ≈ the raw net stream — which is deeply negative). A repaired null cannot rescue a book that net-negative.

**Why it is a blocker, not a footnote:** left uncaught, a half-flat null would **manufacture false PASSes** for any near-breakeven signal downstream. It **must be fixed and re-verified** before any signal is judged on beat-random in Phase 2.

## 8. Diagnostics (logged, not gates)
| arm | surviving days | signal day-drop (₹100k floor) | null-draw-drop | short-ban | circuit-flag | sector-conc |
|---|--:|--:|--:|--:|--:|--:|
| A / A-Z, w15 | 2507 / 2553 | 10.2% / 8.5% | 47.1% / 47.3% | 0.0% | 6.0% | 0.44 |
| A / A-Z, w30 | 2580 / 2616 | 7.6% / 6.3% | 51.2% / 51.4% | 0.0% | 16.4% | 0.44 |
| A / A-Z, w45 | 2631 / 2650 | 5.7% / 5.0% | 56.2% / 56.3% | 0.0% | 25.8% | 0.44 |

Signal day-drop matches the ₹100k feasibility prediction (5–10%). **Short-ban 0%** (as expected on large-cap survivors). Circuit-flag fraction rises with the entry window (6%→26%) — a logged characteristic, not a gate. Sector concentration 0.44 (below the ⌈5/2⌉/5 = 0.6 cap). **Market-day conditioning: UNAVAILABLE** — no index series in the cache; not sourced mid-experiment (Phase-4). The neutrality guarantee rests on the truncation mechanism, not this diagnostic, so its absence drops one secondary cross-check without weakening neutrality.

## 9. Conclusion
On this survivor-cache upper bound, the cross-sectional overnight-gap-**reversal** ranker (both A and A-Z, all windows, both cost bounds) is **decisively net-negative — a KILL**, on the strength of its own DSR/CPCV P&L, independent of the (degraded) beat-random benchmark. **What this claims:** the gap-reversal *selection* has no cost-surviving edge on NSE large caps, even survivorship-subsidized, at a small (₹3–5M) neutral book. **What it does not claim:** nothing about a real, delisted-inclusive universe (Phase 4), nothing about deployable capacity beyond the ₹3–5M finding, and nothing validated via beat-random (that benchmark is quarantined pending the §7 fix). The gap signal family is **retired**; per the roadmap this routes to candidate search.

## 10. Reproducibility appendix
- **Universe:** `config/universe/survivor_cache.yaml` (49 NIFTY-50 survivors). Cache read-only via `XSR_DATA_CACHE_PATH`; regular-session filtered 09:15–15:30 IST.
- **Frozen params (blind, in history):** k=5, N=1000, null-percentile=95, DSR≥0.95, PBO≤0.20, CPCV median>0, pos-frac>0.5 (`pre-registration-frozen` @ `31cc292`); CPCV n_groups=6/k_test=2, PBO n_splits=16, periods/yr=252 (`de6e1c3`); **gross floor ₹100,000** (`pre-registration-v2` @ `7e6a829`) — supersedes the ill-posed ₹5,000,000 @ `31cc292`, which remains in history as the superseded line.
- **Machinery:** frozen harness vendored @ predecessor `0c5c592` (20 files, hash-tripwired); Layer-3 gate @ `982420d`; run harness @ `b96fc18`. Null seed **20260711**.
- **Run:** single blind execution, 6 arms × both cost bounds, no tweak-and-rerun.
- **Known defect (quarantined):** the §7 null-selection infeasibility — fix `build_random_book` and re-verify before Phase-2 beat-random.
