# Research Findings — Cross-Sectional Intraday Long-Short Ranker (NSE)

> **How this document is maintained.** A *living research paper*, authored as each phase completes — **not pre-filled**. Scaffolds are replaced with real, cost-inclusive, gate-computed numbers and honest verdicts only when produced by an actual validated run. An honest KILL is a complete result. **Amended 2026-07-12** (see §7): a null-construction bug was found, fixed, and verified; this record was corrected in place — the KILL verdict was right and is retained, but its originally-stated basis was false and has been replaced with the un-corruptible one.

## Abstract
A market-neutral, cross-sectional intraday ranker (overnight-gap **reversal** — long the biggest gap-downs, short the biggest gap-ups, held entry→close) was tested for a cost-surviving edge on an NSE large-cap survivor cache, against a random long-k/short-k null pushed through the identical execution model. **Result: a decisive KILL — now grounded on two first-class findings that must be read together:**
1. **The ranker has a genuine but tiny selection edge.** Against a *corrected* execution-matched null, the volatility-adjusted variants **A-Z at the 15- and 30-min windows do beat random** — a real, cost-robust **gross selection alpha of ≈ +10 bps/day**. This is worth recording, and it reverses the original (contaminated) claim that the ranker had "no edge."
2. **The strategy is nonetheless net-negative and unexecutable.** In absolute terms it loses **−74 bps/day (optimistic) to −220 bps/day (pessimistic)**, because the daily full-turnover round-trip cost (~86–230 bps) **dwarfs the ~10 bps alpha by 8–20×**. Net-negative even at a generous ~20 bps realistic cost. This basis never touches the null and is cost-model-robust — the ground the KILL now stands on.

Beating a cost-bled random book is **necessary but not sufficient**; the money-losing absolute economics decide. This is a Phase-1 **survivorship-inflated upper bound** (a KILL here is hyper-trustworthy) at **small book size** (§6). The gap family is retired for direct intraday trading (§9); a low-turnover carry-forward is left open, explicitly not licensed.

## 1. Objective & scope
Does a cross-sectional overnight-gap-**reversal** ranker, held entry-to-close in a market-neutral book, beat a random long-k/short-k selection **net of cost** *and* make money in absolute terms? Phase 1 is an **upper-bound smoke test** on a survivor cache: a KILL is hyper-trustworthy, a PASS is provisional-only. Exploration-grade throughout.

## 2. Data
NSE 5-minute OHLCV via the inherited Parquet cache (read-only): **49 present-day large-cap survivors** (NIFTY-50 constituents), **2015-02-02 → 2026-07-03** (~2,790 IST trading days). Split/bonus back-adjusted; **cash dividends unadjusted** (bounded ex-div residual, accepted for the upper bound). Regular-session filtered (09:15–15:30 IST; Muhurat/evening bars dropped — a load-bearing correctness step for the entry→close hold return).

### 2.1 Known limitation — survivorship (Phase 1)
The signal longs the biggest gap-downs; survivor-only data **deletes** exactly the catastrophic gap-downs that delisted, so the long leg is inflated. **Phase-1 results are survivorship-inflated upper bounds.** A KILL is therefore *more* trustworthy, not less: the strategy failed even while subsidized — and even the +10 bps gross edge (§4) is an upper bound whose true out-of-sample value is lower.

## 3. Methodology
Imported, frozen statistical harness (CPCV / DSR / PBO / effective-N ledger — verified per Deep Dive 03, reached only through `HarnessAdapter`). New Layer-3 benchmark = Global Null Panel percentile. Execution-Aware Dollar Neutrality (fixed-k, risk-parity weights, weakest-link truncation, gross-floor day-drop). Cost corridor (optimistic 1× / pessimistic 3× Corwin-Schultz spread, the pessimistic bound also evaluating the ≤1%-participation impact at the cap) composing the frozen Indian intraday cost model. Ex-ante ⌈k/2⌉ sector cap; dual eligibility masks; point-in-time signal + entry→close hold return (no-lookahead, teeth-tested). **Composition (operator ruling):** each arm's per-day quantity = net **minus the null median** (selection alpha); that excess feeds CPCV/DSR/PBO. **Verdict logic (amended 2026-07-12):** an arm must clear the excess-stream criteria **and** a new **absolute-net bar** — median daily net return > 0 per cost bound (§7.3). Full spec: `MASTER_BLUEPRINT.md`, `docs/deep_dives/`.

**Pre-registration (blind, before any result):** k=5, N=1000 null draws/day, null-percentile=95th (α=0.05), DSR≥0.95, PBO≤0.20, CPCV median>0, positive-fraction>0.5 (`pre-registration-frozen` @ `31cc292`); CPCV n_groups=6/k_test=2, PBO n_splits=16, periods_per_year=252 (addendum @ `de6e1c3`); **gross floor RE-FROZEN blind ₹100,000** (`pre-registration-v2` @ `7e6a829`, see §6). The absolute-net bar (§7.3) is a **stricter** gate added post-hoc; it can only kill, never resurrect, so it carries no pre-registration hazard.

## 4. Results scorecard — **KILL (all arms)**, on absolute economics

**Two tables, read together.** Table 1 is the corrected beat-random / excess-stream result (selection skill). Table 2 is the absolute economics (the decider). Program: raw arms 6 · effective-N **5.98** (from the streams; not a raw 6) · **PBO 0.000**.

### Table 1 — Excess-over-null (selection alpha, *corrected* null)
| Arm | Window | beat% | DSR opt / pess | CPCV median opt / pess | CPCV 10th pess | Excess-stream reading |
|---|---|--:|--:|--:|--:|---|
| A | 15 | 100 | 0.99 / 0.80 | 1.84 / 1.39 | −0.17 | opt clears, **pess fails** (L2_TRIGGER) |
| A | 30 | 100 | 0.85 / 0.27 | 1.34 / 1.03 | −0.29 | **DEAD** |
| A | 45 | 99.9 / 81.4 | 0.16 / 0.00 | 0.71 / 0.24 | −1.01 | **DEAD** |
| A-Z | 15 | 100 | **1.00 / 1.00** | 2.47 / 2.37 | **+0.93** | **beats random, both bounds** |
| A-Z | 30 | 100 | **0.99 / 0.99** | 1.65 / 1.78 | **+1.14** | **beats random, both bounds** |
| A-Z | 45 | 100 | 0.74 / 0.85 | 1.17 / 1.27 | +0.49 | DSR<0.95 → DEAD |

Null median (the random book's own net, the tell that the null is honest): **opt −86 bps/day, pess −234 bps/day** on every arm (slightly-to-solidly negative, 0% zero-pad — §7).

### Table 2 — Absolute economics (net of cost — **the decider**)
Per unit of one leg's gross; median (mean) bps/day. Gross = pure entry→close spread P&L (cost-free); NET = gross − full daily round-trip cost.
| Arm | Window | GROSS med (mean) | NET opt med (mean) | NET pess med (mean) | Absolute reading |
|---|---|--:|--:|--:|---|
| A | 15 | +13.1 (+12.9) | −74.0 (−76.9) | −219.4 (−231.5) | net-negative both bounds |
| A-Z | 15 | +12.6 (+12.2) | −73.8 (−75.5) | −216.9 (−225.8) | **net-negative both bounds** |
| A-Z | 30 | +9.6 (+9.0) | −76.1 (−78.6) | −221.4 (−230.0) | **net-negative both bounds** |

The two arms that *beat random* (A-Z 15/30) still **lose ~74–220 bps/day net**. Under the amended gate (absolute-net bar, §7.3) they therefore **KILL** — as do the four that already failed the excess stream. **All six arms KILL.** The gross edge is real (~+10 bps/day) but ~1/8 of even the optimistic cost.

## 5. Study results
### 5.1 — Selection alpha is real, but ~10 bps (Table 1 + gross of Table 2)
With the corrected null, the vol-adjusted **A-Z 15/30** beat the execution-matched random book on every excess-stream criterion at **both** cost bounds (DSR≈1.0 after effective-N deflation, CPCV median +1.6…+2.5, 10th-percentile **positive**, beat 100%). The mechanism is genuine: the ranker's picks earn a positive gross spread of **+9.6 to +12.6 bps/day** (median) that a random neutral book does not. **Cost-robustness tell:** for these arms opt-DSR ≈ pess-DSR (1.00≈1.00, 0.99≈0.99) — the excess is nearly invariant across a 2.7× cost swing because the excess ≈ gross selection alpha (the cost both books pay cancels). The **raw** A arms diverge across bounds (A-45 DSR 0.16→0.00) — their apparent edge is cost-fragile — so only the vol-adjusted, cost-robust selection survives *as selection*.

### 5.2 — Absolute economics kill it (Table 2)
The ~10 bps gross alpha is dwarfed by the round-trip cost. Full daily turnover (enter@window → exit@close, both legs) costs **~86 bps optimistic / ~230 bps pessimistic** per book, so NET is **−74 to −220 bps/day**. Break-even would require an all-in round-trip **≤ ~5 bps/name**; even a generous real-world NSE large-cap all-in (STT + fees + spread ≈ 15–25 bps) is 2–4× the gross alpha. The KILL is robust to the cost-model conservatism (§6), not an artifact of the Corwin-Schultz spread proxy.

**Window / cost reading:** more window / more cost → more absolute loss, monotonically — consistent with a small gross edge overwhelmed by turnover cost.

## 6. Capacity finding (first-class result) — the book is structurally small
The extreme-gap selection **systematically picks less-liquid names** (thin names gap most), and the neutral gross is the weakest-link `min` across the leg under a 1%-of-entry-window participation cap. Consequences, all **blind** (computed before any return):
- **Feasible neutral-book gross: median ₹2.7M (w15) → ₹5.3M (w45), fat low tail** (p10 ≈ ₹0.1–0.2M), max ~₹30–60M. The corrected null faces the **same** floor and forms a floor-clearing book on every surviving day (§7), so the beat-random comparison is on a shared, feasible day set.
- The **cost model is scale-invariant** (~16–23 bps flat across ₹20k→₹100M; no fixed component) → there is **no cost-mechanical floor**. The only small-size effect is integer-share **lot granularity**.
- The original ₹5M floor (`31cc292`) was **ill-posed** (assumed a cost floor that does not exist) and dropped 48–71% of days; superseded blind by **₹100,000** (`pre-registration-v2`) — the minimal floor at which every name forms a real whole-share position — before any return was seen.
- **Stamp glued to the verdict:** even the ~10 bps gross edge (§4) deploys only a **₹3–5M** median neutral book with ~10 bps integer-share tracking error. A real, low-capacity property of the idea that **follows into the Phase-4 mid-caps (likely worse there).**

## 7. Null-construction bug — **found, fixed, verified** (and the error trail)
### 7.1 What the bug was
The random long-k/short-k null selection was **infeasible on ~50% of draws** — a random 5-long/5-short book cannot form a valid **disjoint** pair under the ⌈k/2⌉=3 **sector cap** roughly half the time. The infeasible draw was dropped and **zero-padded** into that day's null distribution (`build_random_book` → `DayDropped` → `run_arm` appended `0.0`). A flat 0.0 book beats a real random book that pays cost, so the zero-padding pulled the null benchmark **up toward 0** and **manufactured a false, across-the-board KILL** on the excess stream.

### 7.2 The error trail (kept on the record, not erased)
- The **original excess-stream KILL was contaminated.** The first-recorded numbers (DSR 0.00, CPCV −11…−29, positive-fraction 0.00) were an artifact of the zero-padded null, not a real net-negativity of selection.
- **The originally-stated basis was false.** This record previously claimed the KILL "rested on DSR/CPCV net-negativity computed on the signal's own P&L, **independent of the null**." **That was wrong.** Per the operator's Ruling 1 the CPCV/DSR run on the **excess-over-null** stream, so they were fully exposed to the degraded null. With the null corrected, the excess stream **reverses**: A-Z 15/30 beat random (§4, Table 1). The verdict survived only because a *different*, null-independent basis (absolute economics) independently kills it.
- **A first fix was itself wrong and was corrected.** An interim fix set the null's gross floor to 0 (a relaxation *below* the signal's floor), which leaked thin sub-floor books and inflated the signal's apparent alpha. Both errors pushed toward a pass; both were removed.

### 7.3 The two methodology fixes (first-class — they protect every future candidate)
1. **Null construction — the new standard.** `build_random_book` now **rejection-samples a feasible, floor-clearing, ⌈k/2⌉-capped, disjoint** book that faces the **identical ₹100k floor** as the signal — no zero-pad, no relaxation. A day is dropped only if no floor-clearing book exists at all (shared with the signal). Verified: **0% zero-pad, 0 null-draw-drops on surviving days**, and the **sanity tell passes** — the true null median net is slightly-to-solidly negative (−86 opt / −234 pess bps), never ≈0/positive. Any future null must clear this tell. (`src/xsranker/null/panel.py`; `tests/test_null_panel.py`.)
2. **Absolute-net gate — the durable lesson.** Beat-random is **necessary but not sufficient**: this episode proved an arm can beat a cost-bled null on the excess stream yet bleed money net of cost. The verdict logic now requires, as a per-bound binding criterion alongside beat-random/DSR/CPCV, that the arm's **median daily absolute net return clear zero** (`absolute_net_min=0.0`, participating in the cost corridor). No future candidate can pass on excess-stream alone while net-negative. (`src/xsranker/gate/arm.py`, `config/default.yaml`; teeth: `tests/test_gate_arm.py::test_beats_a_bleeding_null_but_net_negative_is_killed_on_absolute_economics`.)

### 7.4 Cost symmetry (the KILL is not a null artifact)
The signal and null pass through the **identical** cost function (`_book_returns` → `_position_costs` → `cost_corridor`); confirmed both by code and empirically (per-name cost for a name held by both books agrees to <6 bps, the residual being different notional, not a different charge). Median per-name round-trip cost is essentially equal — signal ~42 bps opt / ~114 bps pess vs null ~43 / ~116 — so the signal does **not** escape a cost the null pays, and the pessimistic corridor (realized pess/opt ≈ 2.71×, consistent with the pre-registered 3× spread multiplier plus the fixed statutory charge) inflates both books alike.

## 8. Diagnostics (logged, not gates)
| arm | surviving days | signal day-drop (₹100k floor) | null-draw-drop | null median net (opt/pess) | short-ban | circuit-flag | sector-conc |
|---|--:|--:|--:|--:|--:|--:|--:|
| A / A-Z, w15 | 2507 / 2553 | 10.2% / 8.5% | **0.0%** | −86 / −234 bps | 0.0% | 6.0% | 0.44 |
| A / A-Z, w30 | 2580 / 2616 | 7.6% / 6.3% | **0.0%** | −86 / −235 bps | 0.0% | 16.4% | 0.44 |
| A / A-Z, w45 | 2631 / 2650 | 5.7% / 5.0% | **0.0%** | −86 / −236 bps | 0.0% | 25.8% | 0.44 |

Signal day-drop matches the ₹100k feasibility prediction (5–10%). **Null-draw-drop is now 0%** (the corrected null forms a floor-clearing book on every surviving day) — the signal is the binding arm; the beat-random comparison runs on the signal's surviving days, both books feasible there. **Short-ban 0%** (large-cap survivors). Circuit-flag rises with the entry window (6%→26%) — logged, not a gate. Sector concentration 0.44 (below the ⌈5/2⌉/5 = 0.6 cap). **Market-day conditioning: UNAVAILABLE** — no index series in the cache; deferred to Phase-4. Neutrality rests on the truncation mechanism, not this diagnostic.

## 9. Conclusion
On this survivor-cache upper bound, the cross-sectional overnight-gap-**reversal** ranker is a **KILL — all six arms**, on absolute economics. **What this claims, precisely:**
- The **selection has a real but tiny gross edge** (~+10 bps/day; the vol-adjusted A-Z 15/30 beat an execution-matched random book, cost-robustly). Not nothing — a genuine, if weak, cross-sectional signal.
- The **strategy loses money net of cost** (−74 to −220 bps/day; net-negative even at ~20 bps realistic cost), because daily full-turnover round-trip cost dwarfs the alpha. **Not executable as a directly-traded intraday strategy.**

**What it does not claim:** nothing about a real, delisted-inclusive universe (Phase 4); nothing about deployable capacity beyond the ₹3–5M finding.

**Carry-forward (open Phase-4 question, explicitly NOT licensed now):** the weak-but-real ~10 bps/day selection signal might be worth revisiting *only* in a form that does not pay ~100+ bps/day — i.e. **drastically lower turnover / longer hold**, where the gross edge is not consumed by daily round-trip cost. This is recorded as a lead to evaluate, not a decision; the gap family is **retired for direct intraday trading**, and per the roadmap this routes to candidate search.

## 10. Reproducibility appendix
- **Universe:** `config/universe/survivor_cache.yaml` (49 NIFTY-50 survivors). Cache read-only via `XSR_DATA_CACHE_PATH`; regular-session filtered 09:15–15:30 IST.
- **Frozen params (blind, in history):** k=5, N=1000, null-percentile=95, DSR≥0.95, PBO≤0.20, CPCV median>0, pos-frac>0.5 (`pre-registration-frozen` @ `31cc292`); CPCV n_groups=6/k_test=2, PBO n_splits=16, periods/yr=252 (`de6e1c3`); **gross floor ₹100,000** (`pre-registration-v2` @ `7e6a829`) — supersedes the ill-posed ₹5,000,000 @ `31cc292`, which remains in history.
- **Amendment (2026-07-12):** null-construction fix + absolute-net gate committed together with this corrected record. Absolute/gross economics (Table 2) computed through the identical book + cost code paths; corrected excess-stream run (Table 1) on the repaired null. **Stricter gate, added post-hoc — kills only.**
- **Machinery:** frozen harness vendored @ predecessor `0c5c592` (20 files, hash-tripwired); Layer-3 gate @ `982420d` (+ absolute-net bar, this amendment); run harness @ `b96fc18`. Null seed **20260711**.
- **Run:** single blind execution, 6 arms × both cost bounds, no tweak-and-rerun; re-run once on the corrected null (verdict change flagged to and ruled by the operator before any record was touched).
- **Stamps (never separable from any "it works" reading):** exploration-grade · survivorship-inflated upper bound · small-size / low-capacity (₹3–5M book, ~10 bps tracking error).
