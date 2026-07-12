# Research Findings — Cross-Sectional Intraday Long-Short Ranker (NSE)

> **How this document is maintained.** A *living research paper*, authored as each phase completes — **not pre-filled**. Scaffolds are replaced with real, cost-inclusive, gate-computed numbers and honest verdicts only when produced by an actual validated run. An honest KILL is a complete result. **Amended 2026-07-12** (see §7): a null-construction bug was found, fixed, and verified; a cost-realism re-run then re-based the KILL on an **estimator-free** footing (the recorded loss had been Corwin-Schultz-inflated). The KILL verdict was right throughout and is retained; its *stated basis* was corrected twice, to progressively firmer ground.

## Abstract
A market-neutral, cross-sectional intraday ranker (overnight-gap **reversal** — long the biggest gap-downs, short the biggest gap-ups, held entry→close) was tested for a cost-surviving edge on an NSE large-cap survivor cache, against a random long-k/short-k null pushed through the identical execution model. **Result: a decisive KILL, on an estimator-free basis — two first-class findings, read together:**
1. **A genuine but tiny gross selection edge.** Against a *corrected* execution-matched null, the vol-adjusted **A-Z 15/30 beat random** — a real, cost-robust **gross selection alpha of ≈ +10 bps/day** (this reverses the original, contaminated "no edge" claim).
2. **The edge does not clear the fee floor.** The ~+10–13 bps/day gross barely exceeds the exact, **Zerodha-verified statutory fees alone (~9 bps/day at the book level)**. At **zero spread**, on survivorship-inflated data — the most generous case that exists — it nets **+2.9 / +2.1 / −0.5 bps/day: breakeven at best**, and decisively negative once any real spread (>0) or the survivorship correction is applied. **This holds with the Corwin-Schultz spread estimator removed entirely** — the verdict depends on no spread model.

The earlier **−74 to −220 bps/day** figures were **Corwin-Schultz-inflated** (CS over-reads spread ~2–3× on the traded extreme-gap names, confirmed against Abdi-Ranaldo) and are demoted to a spread-sensitivity range (§5.3). Beating a cost-bled random book is **necessary but not sufficient**; the fee floor decides. Phase-1 **survivorship-inflated upper bound** (a KILL here is hyper-trustworthy) at **small book size** (§6). The gap **A-Z** arms are standalone-KILLed for direct intraday trading but **BANKED as a provisional fusion feature** — a real ~12.6 bps selection edge (beats random decisively), survivorship-asterisked (§9); a low-turnover direct-trading lead is left open, not licensed.

## 1. Objective & scope
Does a cross-sectional overnight-gap-**reversal** ranker, held entry-to-close in a market-neutral book, beat a random long-k/short-k selection **net of cost** *and* make money in absolute terms? Phase 1 is an **upper-bound smoke test** on a survivor cache: a KILL is hyper-trustworthy, a PASS is provisional-only. Exploration-grade throughout.

## 2. Data
NSE 5-minute OHLCV via the inherited Parquet cache (read-only): **49 present-day large-cap survivors** (NIFTY-50 constituents), **2015-02-02 → 2026-07-03** (~2,790 IST trading days). Split/bonus back-adjusted; **cash dividends unadjusted** (bounded ex-div residual, accepted for the upper bound). Regular-session filtered (09:15–15:30 IST; Muhurat/evening bars dropped — a load-bearing correctness step for the entry→close hold return).

### 2.1 Known limitation — survivorship (Phase 1)
The signal longs the biggest gap-downs; survivor-only data **deletes** exactly the catastrophic gap-downs that delisted, so the long leg is inflated. **Phase-1 results are survivorship-inflated upper bounds.** A KILL is therefore *more* trustworthy, not less: the strategy failed even while subsidized — and even the +10 bps gross edge (§4) is an upper bound whose true out-of-sample value is lower (which is why the zero-spread breakeven is negative OOS).

## 3. Methodology
Imported, frozen statistical harness (CPCV / DSR / PBO / effective-N ledger — verified per Deep Dive 03, reached only through `HarnessAdapter`). New Layer-3 benchmark = Global Null Panel percentile. Execution-Aware Dollar Neutrality (fixed-k, risk-parity weights, weakest-link truncation, gross-floor day-drop). **Cost model:** the frozen, itemized Indian intraday schedule (`config/costs.yaml`, verified against Zerodha — §5.3) composed with a spread term. The blind run used a Corwin-Schultz spread corridor (opt 1× / pess 3×); the 2026-07-12 cost-realism re-run replaced the disputed spread with verified fees + a defensible spread (fixed 5 bps / Abdi-Ranaldo), which is the go-forward standard (§7.3). Ex-ante ⌈k/2⌉ sector cap; dual eligibility masks; point-in-time signal + entry→close hold return (no-lookahead, teeth-tested). **Composition (operator ruling):** each arm's per-day quantity = net **minus the null median** (selection alpha) for the excess stream feeding CPCV/DSR/PBO. **Verdict logic (amended 2026-07-12):** an arm must clear the excess-stream criteria **and** a new **absolute-net bar** — median daily net > 0 per cost bound (§7.3). Full spec: `MASTER_BLUEPRINT.md`, `docs/deep_dives/`.

**Pre-registration (blind, before any result):** k=5, N=1000 null draws/day, null-percentile=95th (α=0.05), DSR≥0.95, PBO≤0.20, CPCV median>0, positive-fraction>0.5 (`pre-registration-frozen` @ `31cc292`); CPCV n_groups=6/k_test=2, PBO n_splits=16, periods_per_year=252 (addendum @ `de6e1c3`); **gross floor RE-FROZEN blind ₹100,000** (`pre-registration-v2` @ `7e6a829`, see §6). The absolute-net bar (§7.3) is a **stricter** gate added post-hoc; it can only kill, never resurrect, so it carries no pre-registration hazard.

## 4. Results scorecard — **KILL (all six arms)**, estimator-free
Program: raw arms 6 · effective-N **5.98** (from the streams; not a raw 6) · **PBO 0.000**. Two tables, read together: Table 1 = corrected selection skill (beats random); Table 2 = the absolute economics that decide.

### Table 1 — Excess-over-null (selection alpha, *corrected* null)
| Arm | Window | beat% | DSR opt / pess | CPCV median opt / pess | CPCV 10th pess | Excess-stream reading |
|---|---|--:|--:|--:|--:|---|
| A | 15 | 100 | 0.99 / 0.80 | 1.84 / 1.39 | −0.17 | opt clears, pess fails |
| A | 30 | 100 | 0.85 / 0.27 | 1.34 / 1.03 | −0.29 | **DEAD** |
| A | 45 | 99.9 / 81.4 | 0.16 / 0.00 | 0.71 / 0.24 | −1.01 | **DEAD** |
| A-Z | 15 | 100 | **1.00 / 1.00** | 2.47 / 2.37 | **+0.93** | **beats random, both bounds** |
| A-Z | 30 | 100 | **0.99 / 0.99** | 1.65 / 1.78 | **+1.14** | **beats random, both bounds** |
| A-Z | 45 | 100 | 0.74 / 0.85 | 1.17 / 1.27 | +0.49 | DSR<0.95 → DEAD |

Null median (the tell the null is honest): **opt −86 / pess −234 bps/day** on every arm (properly negative, 0% zero-pad — §7).

### Table 2 — Absolute economics (**the decider**) — gross vs the fee floor
Per unit one leg's gross; median (mean) bps/day. GROSS = entry→close spread P&L (cost-free). Columns are increasingly conservative cost assumptions; the **estimator-free** ones (gross, fees-only, fees+5bps) carry the verdict.
| Arm | GROSS | NET fees-only *(0 spread)* | NET fees + 5 bps | NET fees + AR/name |
|---|--:|--:|--:|--:|
| A_15 | +13.1 (+12.9) | **+2.9** | −7.1 (−7.8) | −73.0 (−80.6) |
| A-Z_15 | +12.6 (+12.2) | **+2.1** | −7.9 (−8.5) | −72.4 (−78.2) |
| A-Z_30 | +9.6 (+9.0) | **−0.5** | −10.5 (−11.0) | −75.7 (−81.3) |

**The gross edge ≈ the Zerodha fee floor.** Verified fees are 4.5–8.2 bps/name (4.47 @ ₹500k → 8.24 @ ₹100k; ~4.2 bps median paid → ~9 bps/book). So at **zero spread**, on a survivorship-inflated upper bound, net is **+2.9 / +2.1 / −0.5 bps/day — breakeven at best**; a fair fixed 5 bps spread → −7 to −11; the AR per-name spread (real thin tail, §5.3) → −72 to −76. **All six arms KILL** under the amended absolute-net gate (§7.3): there is no room left for any spread, and the true OOS gross is below even this inflated one.

## 5. Study results
### 5.1 — Selection alpha is real, but ~10 bps (Table 1 + gross)
With the corrected null, the vol-adjusted **A-Z 15/30** beat the execution-matched random book on every excess-stream criterion at **both** cost bounds (DSR≈1.0 after effective-N deflation, CPCV median +1.6…+2.5, 10th-percentile **positive**, beat 100%). The mechanism is genuine: the ranker's picks earn a positive gross spread of **+9.6 to +12.6 bps/day** (median) that a random neutral book does not. **Cost-robustness tell:** opt-DSR ≈ pess-DSR (excess ≈ gross selection alpha; the cost both books pay cancels). The **raw** A arms diverge across bounds — their apparent edge is cost-fragile — so only the vol-adjusted selection survives *as selection*.

### 5.2 — The fee floor kills it (estimator-free — the primary basis)
The gross edge (~+10–13 bps/day) is essentially the same magnitude as the **exact, verified Zerodha statutory fees alone (~9 bps/day book-level)**. Strip out every spread assumption: at fees-only the strategy nets **+2.9 / +2.1 / −0.5 bps/day**, i.e. breakeven — and this is on a **survivorship-inflated upper bound**, so the true out-of-sample gross is lower and fees-only is negative OOS. Any real spread (>0) is pure additional loss. **This basis uses no spread estimator at all** — it is immune to the Corwin-Schultz dispute (§5.3) and is the ground the verdict now stands on.

### 5.3 — The disputed spread: Corwin-Schultz over-read (correction on the record)
The originally-recorded **−74 / −220 bps/day** used a Corwin-Schultz (CS) spread corridor (opt 1× / pess 3×). CS over-reads on high-range days, and this strategy selects exactly the high-range extreme-gap names. Cross-checked against **Abdi-Ranaldo (AR)** (less range-sensitive), point-in-time, same trailing window, on the traded names:

| | CS median | AR median | AR p90 | AR p95 | AR max | CS/AR (median) |
|---|--:|--:|--:|--:|--:|--:|
| A-Z_15 selected | 34.7 | 18.5 | 108.6 | 134.7 | 656 | ×1.9 |
| A-Z_30 selected | 35.1 | 19.3 | 108.8 | 134.8 | 656 | ×1.8 |
| A_15 selected | 35.3 | 11.8 | 114.7 | 142.3 | 656 | ×3.0 |

**CS over-reads spread ~1.8–3.0× on the traded gap names** (universe baseline ~×2.2–2.4). So the −74/−220 figures were **spread-inflated** and are demoted here to a spread-sensitivity range — the verdict does not rest on them. Two honest caveats on AR: its **thin tail is real selection cost** (p90–95 ≈ 108–142 bps — the extreme-gap picks genuinely include wide-spread names, which is why fees+AR is still −72 to −76), but its **max ≈ 656 bps is estimator noise**, so the AR per-name bound is not itself the ground of the verdict either. The verdict rests on §5.2 (fees-only / fees+5bps), which need no estimator.

## 6. Capacity finding (first-class result) — the book is structurally small
The extreme-gap selection **systematically picks less-liquid names** (thin names gap most), and the neutral gross is the weakest-link `min` across the leg under a 1%-of-entry-window participation cap. Consequences, all **blind** (computed before any return):
- **Feasible neutral-book gross: median ₹2.7M (w15) → ₹5.3M (w45), fat low tail** (p10 ≈ ₹0.1–0.2M). The corrected null faces the **same** floor and forms a floor-clearing book on every surviving day (§7), so the beat-random comparison is on a shared, feasible day set.
- The frozen fee model is **near scale-invariant** (only the ₹20 brokerage cap helps larger orders: ~8.2 bps/name @ ₹100k → ~4.5 @ ₹500k) → no cost-mechanical floor beyond integer-share **lot granularity**.
- The original ₹5M floor (`31cc292`) was **ill-posed** and dropped 48–71% of days; superseded blind by **₹100,000** (`pre-registration-v2`) — the minimal floor at which every name forms a real whole-share position — before any return was seen.
- **Stamp glued to the verdict:** even the ~10 bps gross edge (§4) deploys only a **₹3–5M** median neutral book with ~10 bps integer-share tracking error. A real, low-capacity property that **follows into the Phase-4 mid-caps (likely worse there).**

## 7. Corrections & methodology fixes (first-class — they protect every future candidate)
### 7.1 The null-construction bug — what it was
The random long-k/short-k null selection was **infeasible on ~50% of draws** (a random 5-long/5-short book cannot form a valid **disjoint** pair under the ⌈k/2⌉=3 **sector cap** roughly half the time). The infeasible draw was **zero-padded** with `0.0`. A flat 0.0 book beats a real random book that pays cost, so the padding pulled the null **up toward 0** and **manufactured a false, across-the-board KILL** on the excess stream.

### 7.2 The error trail (kept on the record, not erased)
- The **original excess-stream KILL was contaminated** (DSR 0.00, CPCV −11…−29 were a zero-padding artifact, not real selection net-negativity).
- **The originally-stated basis was false.** This record previously claimed the KILL "rested on DSR/CPCV **independent of the null**." **That was wrong** — per Ruling 1 they run on the **excess-over-null** stream, fully exposed to the degraded null. Corrected, the excess stream **reverses**: A-Z 15/30 beat random (Table 1).
- **An interim null fix was itself wrong and corrected** (it set the null floor to 0 — a relaxation below the signal's floor — inflating the signal's alpha). Both errors pushed toward a pass; both removed.
- **The re-grounded absolute basis was then itself CS-inflated** (−74/−220), and is now re-based estimator-free (§5.2–5.3). Each correction moved the KILL to firmer ground; the verdict never changed.

### 7.3 The three methodology fixes (now standard)
1. **Null construction.** `build_random_book` **rejection-samples a feasible, floor-clearing, ⌈k/2⌉-capped, disjoint** book at the **identical ₹100k floor** as the signal — no zero-pad, no relaxation. Verified: **0% zero-pad, 0 null-draw-drops**; **sanity tell** — the true null median net must be slightly negative (−86 opt / −234 pess bps), never ≈0/positive. (`src/xsranker/null/panel.py`; `tests/test_null_panel.py`.)
2. **Absolute-net gate.** Beat-random is **necessary but not sufficient** — an arm can beat a cost-bled null yet lose money net of cost. The gate now requires the arm's **median daily absolute net > 0** per bound, binding, riding the corridor. (`src/xsranker/gate/arm.py`; teeth: `tests/test_gate_arm.py::test_beats_a_bleeding_null_but_net_negative_is_killed_on_absolute_economics`.)
3. **Cost realism — the standard cost model.** Corwin-Schultz over-reads spread ~2–3× on gap-selected names (§5.3), which inflated the recorded loss. The standard is **verified statutory fees + a defensible spread, never CS alone**: `config/costs.yaml` is the committed, Zerodha-verified fee model (brokerage 0.03%/₹20 cap, STT 0.025% sell, exchange 0.00297%, SEBI, stamp 0.003% buy, GST 18%); the spread term is a conservative fixed bound and/or the Abdi-Ranaldo estimator (`abdi_ranaldo_spread`), not the range-inflated CS. The exact corridor spread params for the next candidate are to be pinned **blind at its pre-registration** — not set here, post-result.

### 7.4 Cost symmetry (estimator-independent)
Signal and null pass through the **identical** cost function (`_book_returns` → `_position_costs`); confirmed by code and empirically (per-name cost for a name held by both books agrees to <6 bps, the residual being different notional, not a different charge). This symmetry holds under any spread estimator, so it is not disturbed by the CS→fees+AR correction; the CS-based per-name magnitudes quoted in the blind run (~42/114 bps) are themselves over-read per §5.3.

### 7.5 Cost corridor RE-PINNED to deployment economics (blind, pre-candidate-#3-verdict, 2026-07-12)
New information — the actual deployment size (**₹1 lakh capital, k=5 → ₹10,000 per name**) — changed the corridor materially in **both** directions. Re-pinned BLIND before any candidate-#3 return was seen. The old corridor was wrong two ways at once: fees under-charged, spread wildly over-charged.

**The re-pinned corridor (the live standard going forward):**
| bound | size-aware fees @ ₹10k | + spread (NSE-anchored) | **break-even gross** |
|---|---|---|---|
| optimistic | 10.605 bps | 1 bps | **11.60 bps/day** |
| pessimistic | 10.605 bps | 5 bps | **15.60 bps/day** |

1. **Fees were UNDER-charged — now size-aware at the true deployment notional.** The verified fee model (§7.3) was always size-dependent via the **₹20-per-order brokerage cap**, but the runs priced fees at the *liquidity-max book notional* (~₹0.6–1M/name, the truncation's capacity size) → only **~4–4.5 bps**. Deployment is ₹10k/name, where fees are **10.605 bps round-trip**. Fees are now charged at a pinned `deployment_notional_inr` (= capital / 2k), **decoupled from the capacity sizing** (which still drives the gross-floor day-drop — different question, both notional-independent fractions, §ruling seam 1).
   - **Fees are FLAT at 10.605 bps for any per-name notional below ~₹66,667** (where 0.03% first exceeds the ₹20 cap). **CORRECTION ON THE RECORD (operator, 2026-07-12):** this **kills the idea that k is a fee lever at ₹1L capital** — k=3/5/10 all deploy < ₹66.7k/name and pay the identical 10.605 bps. A prior suggestion that fewer names → lower fees was **wrong at this capital**; k only becomes a fee lever above ~₹67k/name (i.e., much larger capital). Recorded so the dead option is not silently re-proposed.

2. **Spread was OVER-charged — Abdi-Ranaldo RETIRED, replaced by NSE's PUBLISHED impact cost.** The old 18 bps pessimistic was AR-median magnitude. **NSE publishes the authoritative execution-cost measure** — official monthly impact cost per Nifty-50 constituent, defined as degradation vs the bid-offer **mid** (it *does* walk the book). Corroborated: **Nifty-50 impact cost = 0.02% ≈ 2 bps one-way at a ₹50 lakh basket** (~4 bps round-trip). We trade **₹10k = 500× smaller**, deep inside top-of-book. Pinned optimistic **1 bps**, pessimistic **5 bps** (NSE's ~4 bps @ ₹50L rounded up — deliberately conservative since our size is 500× smaller). **AR is retired from the live corridor exactly as CS was (§5.3): estimators over-read; NSE publishes the real number.** `abdi_ranaldo_spread` / `corwin_schultz_spread` stay in code for history only.

3. **Liquidity-selection check (first-class, return-blind).** Unlike candidate #1 (which longs the *extreme-gap thin tail*, §6), **candidate #3's SR does NOT select the illiquid tail.** Over 2,814 days the SR-traded extremes sit at liquidity **percentile mean 0.547 / median 0.559** (0.5 = neutral) — *slightly deeper* than average, because SR is sector-relative and its most-traded names (SHRIRAMFIN, COALINDIA, BPCL, ONGC, RELIANCE) are ₹45–280 cr/morning. **₹10k participation in even the thinnest selected name: median 0.0104%, worst-ever 1.35%.** This is a **real structural difference between the two signals** and is what *justifies the tight spread bound* — no worst-name penalty is warranted, so the universe-representative NSE regime (already overstated 500×) applies.

4. **THE SMALL-CAPITAL PENALTY (first-class deployment finding — arguably the program's most important economic constraint).** At **₹1 lakh** the break-even bar is **11.6–15.6 bps/day**; at **₹50 lakh/name** it is **~6.5 bps** (fees ~4.5 + comparable small spread) — roughly **half**. The gap is almost entirely the brokerage-cap fee effect. **The same signal can be viable at scale and dead at ₹1 lakh.** Small capital is structurally penalised; this is not a property of any one candidate but of the deployment size, and it stamps every Phase-1 verdict. A signal killed at ₹1L is *not* proven dead at ₹50L — the corridor is a moving, capital-dependent bar.

**This re-pin does NOT resurrect candidate #1.** Its ~12.6 bps gross would clear the new *optimistic* bar (11.6) by ~1 bps but **fail the pessimistic** (15.6) — and it is survivorship-inflated (§2.1), so its true OOS gross is lower still. **It stays dead.** The corridor change is a cost-model correction that applies to every future candidate, **not a rescue** of a killed one.

## 8. Diagnostics (logged, not gates)
| arm | surviving days | signal day-drop (₹100k floor) | null-draw-drop | null median net (opt/pess) | short-ban | circuit-flag | sector-conc |
|---|--:|--:|--:|--:|--:|--:|--:|
| A / A-Z, w15 | 2507 / 2553 | 10.2% / 8.5% | **0.0%** | −86 / −234 bps | 0.0% | 6.0% | 0.44 |
| A / A-Z, w30 | 2580 / 2616 | 7.6% / 6.3% | **0.0%** | −86 / −235 bps | 0.0% | 16.4% | 0.44 |
| A / A-Z, w45 | 2631 / 2650 | 5.7% / 5.0% | **0.0%** | −86 / −236 bps | 0.0% | 25.8% | 0.44 |

Signal day-drop matches the ₹100k feasibility prediction (5–10%). **Null-draw-drop 0%** (corrected null forms a floor-clearing book on every surviving day). **Short-ban 0%**. Circuit-flag rises with the window (6%→26%). Sector concentration 0.44 (below the 0.6 cap). **Market-day conditioning: UNAVAILABLE** (no index in cache; Phase-4). *(The null median figures above are the CS-corridor values; the cost-realism re-run (§5.2–5.3) supersedes them for the absolute-economics reading.)*

## 9. Conclusion
On this survivor-cache upper bound, the cross-sectional overnight-gap-**reversal** ranker is a **KILL — all six arms**, on an **estimator-free** basis. **What this claims, precisely:**
- The **selection has a real but tiny gross edge** (~+10 bps/day; A-Z 15/30 beat an execution-matched random book, cost-robustly). A genuine, if weak, cross-sectional signal.
- The **edge does not clear the fee floor**: ~+10–13 bps/day gross vs ~9 bps/day of exact Zerodha statutory fees → **breakeven at zero spread on an inflated upper bound** (+2.9 / +2.1 / −0.5), decisively negative once any spread or the survivorship correction is applied. **Independent of Corwin-Schultz or any spread model.** Not executable as a directly-traded intraday strategy.

**What it does not claim:** nothing about a real, delisted-inclusive universe (Phase 4); nothing about deployable capacity beyond the ₹3–5M finding.

**Disposition (amended 2026-07-12) — standalone-KILL; BANKED as a provisional feature.** The gap
**A-Z** arms are **NOT fully retired.** They carry a **real, measurable selection edge** — the
z-scored arms beat the execution-matched random book **decisively** (beat% 100, DSR ≈ 1.0) — and
*signal is exactly what the fusion engine eats*. Per the capstone (`POST_PROJECT_DIRECTIONS.md` §2:
"components may be weak — decisiveness is demanded at the **ensemble**, not the component; killing
every slightly-positive component individually destroys the building blocks the ensemble is made
of"), a component with a real edge is **banked**, never deleted. Three inseparable stamps:
1. **Standalone-dead** — cannot trade alone (~+12.6 bps gross ≈ the ~9–14 bps fee floor). **Verdict
   unchanged.**
2. **Real selection edge** — ~+12.6 bps/day gross, beats random decisively. This is *why* it is banked.
3. **Survivorship-inflated asterisk** — the signal longs the gap-downs (dying-stock profile), so the
   true out-of-sample edge is **below 12.6 and unmeasured**; its seat is **provisional pending
   Phase-4 point-in-time measurement.**

The gap A-Z form is the stable's **first (provisional) member.** **Small ≠ zero:** candidate #1 has
a *small real* edge (banked); the retired candidate-#2 V_resid had *zero* edge (beat% ~50, DSR 0,
gross ≈ 0 — a coin flip, genuinely dead, nothing to fuse). The stable now holds **one provisional
member**, not two, and not zero. (The low-turnover / longer-hold direct-trading lead from §9 is
still open but explicitly NOT licensed — that is separate from the banking.)

## 10. Reproducibility appendix
- **Universe:** `config/universe/survivor_cache.yaml` (49 NIFTY-50 survivors). Cache read-only via `XSR_DATA_CACHE_PATH`; regular-session filtered 09:15–15:30 IST.
- **Frozen params (blind, in history):** k=5, N=1000, null-percentile=95, DSR≥0.95, PBO≤0.20, CPCV median>0, pos-frac>0.5 (`pre-registration-frozen` @ `31cc292`); CPCV n_groups=6/k_test=2, PBO n_splits=16, periods/yr=252 (`de6e1c3`); **gross floor ₹100,000** (`pre-registration-v2` @ `7e6a829`).
- **Cost model:** `config/costs.yaml` — the committed, Zerodha-verified statutory fee schedule (the standard fee model). Spread term: CS corridor for the blind run; verified fees + fixed-5bps / Abdi-Ranaldo for the 2026-07-12 cost-realism re-run and going forward (§7.3).
- **Amendment (2026-07-12):** null-construction fix + absolute-net gate + this corrected record committed together; a later cost-realism re-run re-based the KILL estimator-free and demoted the CS −74/−220 to a spread-sensitivity range (§5.3). Absolute/gross economics computed through the identical book + cost code paths.
- **Machinery:** frozen harness vendored @ predecessor `0c5c592` (20 files, hash-tripwired); Layer-3 gate @ `982420d` (+ absolute-net bar); run harness @ `b96fc18`. Null seed **20260711**.
- **Run:** single blind execution, 6 arms × both cost bounds, no tweak-and-rerun; re-run on the corrected null, then a cost-realism sensitivity re-run — every verdict change flagged to and ruled by the operator before any record was touched.
- **Stamps (never separable from any "it works" reading):** exploration-grade · survivorship-inflated upper bound · small-size / low-capacity (₹3–5M book, ~10 bps tracking error).

---

# Candidate #2 — Proxy Cumulative Volume Delta: the D8 pre-verdict finding (2026-07-12)

**Pre-registration** `candidate-2-preregistration` @ `3cb7b15`. **Disposition of V / V-A: RETIRED at D8, pre-verdict** (operator-ruled 2026-07-12) — no verdict run; the finding below is their disposition. The price-orthogonalised successor **V_resid** carries the axis forward (`docs/PREREGISTRATION_VOLUME_DELTA_RESIDUAL.md`).

## The finding (first-class, methodological)

**A proxy cumulative-volume-delta signed by each bar's close-vs-open is ~73% rank-equivalent to the morning return — it is substantially volume-weighted momentum, not an independent flow axis.**

The pre-registered **D8** gate (blind, pre-verdict) correlated the signal *values* (no P&L) of raw **V** = (ΣV_up−ΣV_down)/ΣV_total and abnormal **V-A** = V ÷ trailing-median-20d baseline against (a) the morning open→entry return and (b) candidate #1's overnight gap. Per-day **cross-sectional Spearman** (the strategy ranks the cross-section), mean over ~2,800 days:

| signal | vs morning return (w15 / 30 / 45) | vs candidate #1 gap |
|---|--:|--:|
| **V** | 0.751 / 0.735 / 0.727 | −0.126 / −0.113 / −0.104 |
| **V-A** | 0.747 / 0.732 / 0.724 | −0.104 / −0.093 / −0.085 |

- **vs morning return: 0.72–0.75 → the pre-registered 0.5–0.8 STOP band.** V/V-A rank the universe ~73% like the morning price move. **Mechanism:** the bar close-vs-open sign that signs V *is itself a price measure* — a stock drifting up all morning yields mostly up-bars → high V. A verdict on V would be **uninterpretable**: a PASS unclaimable as an independent feature, a FAIL merely re-testing already-dead intraday momentum (ORB / breakout are killed). It would also break the effective-N independence the fusion ensemble depends on.
- **vs candidate #1 gap: |ρ| ≤ 0.13 → INDEPENDENT.** The flow axis is genuinely distinct from the overnight gap; the ~47% residual variance is real flow information worth **isolating**, not abandoning.

**Why this is a valuable result, not a failure.** It was caught by a *pre-verdict* independence screen — before any backtest — on a widely-used retail "CVD" construction. The disciplined fix is a new signal, **V_resid** (the per-day cross-sectional residual of V on the morning return), pre-registered separately; D8 is re-run on it (corr vs morning return ≈ 0 by construction — verified below) before any V_resid verdict.

## What was spent
- **No verdict run, no ledger charge for V/V-A.** D8 is a signal-construction diagnostic (correlations), not a DSR trial; V/V-A produced no return stream and are absent from the effective-N ledger.
- **Cost swap verified in passing:** the live corridor is now fees + fixed 5/18 bps (Corwin-Schultz retired from the live path); the fixed-corridor null median is **~−50 bps** vs CS **−234** (~4.7× less negative). Null-health telemetry healthy (mean attempts ≈ 1.1, ceiling hits 0).

## D8 re-run on V_resid (the fix — the leak is removed)

**V_resid** = the per-day cross-sectional OLS residual of V on the morning return
(`cross_sectional_residual`). Re-running D8 (mean per-day cross-sectional correlation):

| signal | vs morning return — xs-Pearson / xs-Spearman (w15 / 30 / 45) | vs candidate #1 gap (xs-Spearman) |
|---|--:|--:|
| **V_resid** | −0.000 / 0.130 · −0.000 / 0.116 · −0.000 / 0.110 | −0.031 / −0.023 / −0.017 |

- **vs morning return: Pearson ≈ 0 (exactly — the OLS residual is linearly orthogonal to the regressor by construction); Spearman ~0.11–0.13** (a small nonlinear rank remnant), well inside the < 0.5 **independent** band. The momentum leak that STOPped V is removed.
- **vs candidate #1 gap: |ρ| ≤ 0.03** — independence from the retired gap axis is preserved (stronger than V's −0.13).

V_resid isolates the ~47% price-orthogonal flow residual and clears both D8 bands, so it earned a verdict run under its own blind pre-registration (`docs/PREREGISTRATION_VOLUME_DELTA_RESIDUAL.md`, tag `vresid-preregistration`).

## The V_resid verdict — KILL (all 3 arms, a decisive null)

Single blind verdict run (fixed 5/18 bps corridor, N=1000, seed 20260711, CONTINUATION, cumulative ledger):

| arm | beat% | DSR | CPCV median | abs-net bps (opt / pess) | verdict |
|---|--:|--:|--:|--:|---|
| V_resid w15 | 46 | 0.00 | −0.10 | −19.9 / −45.9 | KILL |
| V_resid w30 | 63 | 0.00 | 0.22 | −19.2 / −45.2 | KILL |
| V_resid w45 | 48 | 0.00 | 0.04 | −18.7 / −44.7 | KILL |

Cumulative **effective-N = 8.97** (candidate #1's 6 arms + V_resid's 3 = 9 raw → 8.97 effective): **D6's clustering assumption held** — V_resid genuinely did not collapse into candidate #1, so the independent-axis claim was correct and the higher (near-additive) DSR bar was properly applied. PBO 0.78.

**A true null, not a cost-eaten edge — two independent, each-sufficient failures:** (1) **no selection edge** — beat-random percentile **46–63** (V_resid ranks the cross-section *at the median of the random null* — a coin flip); DSR 0; CPCV medians ~0. (2) **loses money** — absolute net **−19 bps opt / −45 bps pess**, both bounds. The opt→pess gap (−26 bps) matches the corridor's per-leg spread widening (5→18 bps × 2 legs), so **gross ≈ 0**: there is no gross edge for cost to eat.

### Contrast with candidate #1 — this KILL is cleaner and more definitive
- **Candidate #1 (gap):** a **real +12.6 bps/day gross edge** (beat% 100, DSR ≈ 1.0) the fee floor destroyed. The *signal existed*; the *economics* killed it (leaving a low-turnover carry-forward lead).
- **V_resid:** **no edge at all** — ranks no better than random. Nothing to rescue with better cost, exit timing, or turnover. A cleaner, more definitive null.

## Conclusion — the volume-delta axis is exhausted
**Once the price-momentum contamination is stripped from proxy CVD, the remaining institutional-flow signal has no intraday cross-sectional predictive power on this universe.** Both halves are accounted for: the promising half (V/V-A) was **recycled dead momentum** (D8-retired, ~73% morning-return-equivalent; ORB / breakout are already killed); the genuinely independent half (V_resid, price-orthogonal) is **empty** (verdict KILL). The **TWAP/VWAP slice-persistence hypothesis does not hold here.** Candidate #2 is **fully retired**; per the roadmap this routes to candidate #3 (sector-relative, intraday-reversal form).

**Ledger:** V_resid was RUN and evaluated on returns → **CHARGED** (3 streams durably persisted, `candidate-2r-vresid`; cumulative ledger now 9 arms). V / V-A were return-blind **D8 rejections → NOT charged** (the standing return-blind-screen bright line — `PROGRESS.md`).

---

# Candidate #3 — Sector-relative intraday reversal: VERDICT = KILL (all 6 arms; independent but empty)

Sector-relative morning move **SR** = open->entry return - leave-one-out same-sector-peer mean; **SR-Z** = SR / ATR%. Ranked REVERSAL, 2 signals x {15,30,45} = 6 charged arms, under the RE-PINNED live corridor (§7.5). The FIRST candidate to CLEAR the distinctness gate (independent of the banked gap, |rank-corr| 0.16-0.19) — and it is **empty**.

## The verdict — KILL, all 6 arms
| arm | verdict | beat%(o/p) | DSR(o/p) | CPCVmed | absNet bps (o/p) | median GROSS |
|---|---|---|---|---|---|---|
| SR__15 | kill | 71/71 | 0.00/0.00 | 0.29 | -22.4/-30.4 | +0.83 bps |
| SR-Z__15 | kill | 92/92 | 0.00/0.00 | 0.27 | -20.8/-28.8 | +2.41 bps |
| SR__30 | kill | 80/80 | 0.00/0.00 | 0.26 | -22.8/-30.8 | +0.44 bps |
| SR-Z__30 | kill | 87/87 | 0.00/0.00 | 0.37 | -22.4/-30.4 | +0.84 bps |
| SR__45 | near-thresh | 97/97 | 0.01/0.01 | 0.64 | -21.0/-29.0 | +2.18 bps |
| SR-Z__45 | kill | 99/99 | 0.03/0.03 | 0.66 | -21.2/-29.2 | +1.96 bps |

Cumulative **effective-N = 13.48** (15 raw arms: cand#1 6 + cand#2r 3 + cand#3 6); **PBO = 0.382**. Verdict is robust to the arm-count question (DSR ≈ 0 regardless).

**Noise with a sign, not a small edge.** Gross is *positive* but ~1 bps (0.44-2.41 median) at **50-52% days-positive — a coin flip**; DSR ≈ 0 (indistinguishable from noise after deflation); median net decisively negative (-20 to -31 bps both bounds). "Small ≠ zero" holds *literally* (the point estimate is nonzero) but the **Entry gate requires a real edge = statistically distinguishable from noise after deflation, not merely positive-signed.** Candidate #3 fails it.

## Four first-class findings

1. **The re-pin did NOT manufacture this KILL — the opposite.** SR fails even the *optimistic* 11.6 bps break-even by **~10 bps**. It dies on its own near-zero gross (~1 bps), not on any cost assumption — **estimator-free clean**. The corridor correction (§7.5) was right AND was not needed to kill this; nobody should read the cost change as having caused the death.

2. **High beat-random (71-99) is NOT a reprieve — it is a mean-based rank on a right-skewed stream.** `beat_percentile` ranks the signal's *mean* net within the null; the SR stream is right-skewed (most days lose a little, a few win big), so the mean beats random selection while the **robust median net is decisively negative**. Methodological lesson (sharpens the absolute-net gate, §7.3): **beat-random on a skewed stream can mislead; the median net is the honest absolute statistic.** This is why the absolute-net gate uses the median, and why beat-random is necessary-not-sufficient.

3. **The 0.77 momentum diagnostic resolves cleanly — sector-demeaning added independence but not edge.** SR was ~0.77 rank-correlated with raw morning momentum (pre-reg addendum B); the verdict confirms even its tiny gross is largely the intraday-reversal-on-the-morning-move effect. **The sector framing did not earn its seat** over plain reversal — it bought distinctness from the gap, not a new source of return.

4. **Independence without edge is NOT bankable (NEW STANDING RULE).** SR proved genuinely independent of the banked gap (the distinctness gate's whole purpose) and **empty**. Banking a noise-level (DSR ≈ 0, 51%-hit) feature *because* it is independent would be the feature-zoo error: fusing noise-level features **stacks noise, not edge, and raises effective-N (the bar) for zero benefit**. **Independence is necessary but not sufficient; a robust standalone edge is also required.** Precedent for every future candidate.

## The contrast IS the finding — the stable stays at ONE provisional member
- **Candidate #1 (gap):** gross **+12.6 bps**, DSR ≈ **1.0**, beat% **100** → a statistically **robust edge that COST killed**. **Banked** (provisional fusion feature).
- **Candidate #3 (SR):** gross **~1 bps**, DSR ≈ **0**, **51% days-positive** → **no distinguishable edge**. **Not banked.**

Three candidates tested (gap, volume-delta, sector-relative); **one banked, and the fusion story still needs a second member that does not yet exist.** Independence is now *demonstrably* achievable (SR cleared the gate) — the missing ingredient is an independent partner that *also* carries a real edge.

**Ledger:** candidate #3 was RUN and evaluated on returns → **CHARGED** (6 streams durably persisted, `candidate-3-sector-relative`; cumulative ledger now **15 arms**, effective-N 13.48). The distinctness screen was return-blind → not itself charged (the standing bright line).

---

# Gap regime-conditioning: a gross-edge SCREEN batch (2026-07-12, charges nothing; rules out, never blesses)

A four-probe **gross-only screen** on data already owned (panel pickle; no null, no DSR, no verdict). Purpose: find where the banked gap edge lives and whether anything independent has a pulse. Discipline: a strong result **authorizes** a pre-registered study, it does not **become** one; the search must be charged to the ledger inside that study.

## The live finding — the banked gap edge is REGIME-CONDITIONAL, confirmed FOUR independent ways
The 12.63 bps gap A-Z_15 gross (reproduced exactly) is **not flat across regimes — it concentrates where morning dislocation is largest**:
1. **Market-vol tercile:** low 7.7 → mid 12.3 → **high 23.0** bps (~3x).
2. **Gap-dispersion tercile:** narrow 7.1 → mid 15.3 → **wide 18.5** bps (~2.6x).
3. **Abstention gate** (trade only high market-gap-magnitude days): all 12.6 → top-75% 15.4 → top-50% 17.0 → **top-25% 23.0** bps, monotone, hit-rate rising 56.1 -> 58.5%. The top-25% ~23 bps clears even the pessimistic 15.6 break-even (§7.5).
4. **Exit path** (Probe 4 below): the HIGH-vol column dominates at *every* exit. **"High-vol + hold-to-close" is the combination.**

## Probe 4 — exit-timing: a mechanistic NULL (edge accrues to the close; front-loading FALSIFIED)
Same gap A-Z_15 book, fixed at entry 09:30; only the exit varies. Median gross bps:

| exit | ALL | LOW-vol | MID-vol | HIGH-vol |
|---|---|---|---|---|
| 11:00 | 4.63 | 1.84 | 4.09 | 9.14 |
| 12:30 | 7.24 | 3.25 | 4.17 | 16.06 |
| 14:00 | 8.86 | 4.29 | 7.34 | 16.95 |
| 15:20 (close) | 12.84 | 9.12 | 12.10 | 18.98 |

**The edge accrues MONOTONICALLY to the close (4.6 -> 7.2 -> 8.9 -> 12.8), in every volatility bucket, with no exception.** It is a **slow, full-session convergence — not a morning snap-back**. Holding to close *collects* the edge; every earlier exit *strictly loses* gross. This **explains why intraday-scalping variants of gap reversal fail**: at 11:00 the edge simply has not accrued yet. **Exit-timing is RULED OUT — no study needed** (a real mechanistic finding, not merely a null). The regime gate does NOT stack with early exit: high-vol days are best held to close (19.0 bps).

## Probe 2 — an independent pulse (PARKED)
Prior-day-range REVERSAL (long low-range, short high-range): **7.5 bps gross, 54% days+, rank-corr vs gap 0.04** — the first axis to show a real edge that is genuinely independent of the banked gap. Weak and below break-even standalone, but a real **fusion-ingredient candidate**. **PARKED** (second priority; fuse if abstention holds). Realized-vol was weaker (4.6 bps / 52%) and gap-confounded (its construction includes today's |gap|) — not a clean test.

## Dispositions
- **GRADUATED:** the regime-abstention study on the banked gap (its own blind pre-registration; mechanism-derived gate; the full 3-axis x 4-level + exit search charged to the ledger; survivorship-interaction quantified before any verdict is believed).
- **PARKED:** prior-day-range (independent, weak).
- **SKIPPED:** options/OI (#5) — a live ~23 bps regime lead exists on owned data; not worth days of chain-aggregation pipeline while that is unresolved.
- **RULED OUT:** exit-timing.
