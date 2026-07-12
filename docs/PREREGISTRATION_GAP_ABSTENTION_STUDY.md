# Pre-registration — Gap Regime-Abstention Study (FROZEN, blind)

**Status: FROZEN 2026-07-12 (operator sign-off; all five decisions accepted + two binding additions). Nothing run. No verdict seen. The freeze commit + tag precede the verdict run (provenance). `src/vendored/` pristine; recorded verdicts untouched.**

This is a **refinement of the BANKED candidate #1** (gap A-Z), not a new independent candidate. It graduates from the 2026-07-12 gross-edge screen (RESEARCH_FINDINGS "Gap regime-conditioning" block), which showed the gap edge is regime-conditional four independent ways. A screen can authorize a study; it cannot be one. **Everything below is pinned from MECHANISM, before any gated verdict exists — explicitly NOT from the eyeballed top-25% cell.**

---

## 1. Hypothesis (a-priori mechanism)

The overnight gap is an **overreaction**; the intraday reversal **harvests the reversion**. More overreaction → more reversion to harvest → **the edge concentrates on days of largest cross-sectional dislocation**. A market-neutral book cancels the common (index) move, so the harvestable quantity is the **cross-sectional DISPERSION of the gap** — how far the extremes are spread — not its level/magnitude. On low-dislocation days there is little to revert, and the fixed fee floor (10.6 bps) dominates the thin gross; abstaining on those days should raise the **net** edge.

**Falsifiable prediction:** gating the banked A-Z_15 book to trade ONLY above-normal-dislocation days yields a **net (post-cost) median > 0** and clears the effective-N-deflated bar — where the un-gated book does not (it nets ~breakeven, §4/§5.2). If the gated net is also ~0, or a survivorship artifact (§9), conditioning is dead and candidate #1 stays a standalone-KILL.

## 2. Base signal & execution — PINNED (inherited, unchanged)

| item | value | source |
|---|---|---|
| Signal | **A-Z_15** = gap% ÷ ATR%, entry 09:30 (the banked arm with the best edge) | candidate #1 |
| Direction | **REVERSAL** (long biggest gap-downs, short biggest gap-ups) | candidate #1 |
| **Exit** | **hold to CLOSE** — PINNED, not swept: Probe 4 falsified front-loading (edge accrues monotonically to close). The 4-exit look is *charged* (§8) but the exit is fixed by the falsified hypothesis. | Probe 4 |
| k / sizing / neutrality / sector-cap / masks / gross-floor ₹100k | inherited | Phase-2 freeze |
| Cost corridor | **re-pinned** (`cost-corridor-repin`): size-aware fees @ ₹10k + NSE impact 1/5 bps; **break-even 11.6 / 15.6 bps** | §7.5 |

## 3. The GATE — mechanism-derived (the study's one new degree of freedom)

**Gate axis (PINNED — RULED D2: raw-gap dispersion): cross-sectional dispersion of the morning gap** — the cross-sectional **standard deviation of the raw overnight gap% across the eligible universe at entry**, point-in-time.

**Why dispersion, not magnitude — the axis EXPLAINS the screen rather than copying it (on the record, operator ruling).** The screen gated on market-gap *magnitude* (mean|gap|). But a **market-neutral book cancels the common (index) move** — so mean magnitude is largely irrelevant to what the book actually earns. The **dispersion** — the spread between the extremes — is precisely what a long-short book eats: it longs the low tail and shorts the high tail, and its P&L scales with how far apart those tails are. So magnitude "worked" in the screen only because magnitude *correlates* with dispersion; dispersion is the mechanism that **explains** that result, derived from the book's structure rather than lifted from the winning cell. (RULED over A-Z dispersion: raw-gap dispersion is the more interpretable price-dislocation conditioner and avoids subtle circularity — gating on a transform of the very quantity the book ranks by.)

**Gate threshold (PINNED — RULED D1: above trailing median): trade day _t_ iff dispersion _D_t_ > trailing rolling median of _D_ over L = 60 trading days.** Rationale: "above-normal dislocation" is the least-arbitrary a-priori cut — adaptive/regime-relative (no full-sample percentile, which would leak the future), derived from the mechanism ("trade when there is above-typical fuel"), not tuned to a screen cell. It preserves ~50% of days, which **matters enormously given the widened-CI problem (§6)** — a stricter top-tercile cut would shrink an already-thin sample further. L = 60 (~one quarter, RULED D4): long enough to define "normal," short enough to track the current dislocation regime. Days without 60 priors are dropped (burn-in).

## 4. Ledger charge — the full search (NON-NEGOTIABLE; effective-N must rise)

The screen *looked at* many gate configurations to find this effect; the primary hypothesis must be deflated for that search. **Charged as trial streams (excess-over-null, both bounds):**
- **3 regime axes** (gap-dispersion · market-vol ATR% · gap-magnitude) **× 4 gate levels** (trade all / top-75% / top-50% / top-25%) = **12 gate arms**, all on the A-Z_15 base.
- **4 exit points** (11:00 / 12:30 / 14:00 / 15:20) = **4 exit arms**.
- **1 primary** mechanism gate (§3).

**≈ 17 new arms** added to the durable ledger (namespace `cand1abs__*`), all tight variants of the banked gap book → they cluster hard, so cumulative **effective-N rises modestly** from 13.48 but MUST rise; the primary's DSR bar (≥ 0.95) is deflated by the new cumulative effective-N over (15 prior + 17). Return-evaluated → CHARGED (the standing bright line). Report the recomputed effective-N.

## 5. Survivorship-interaction test — THE MAIN THREAT (pinned as a first-class GATE, quantified before any verdict is believed)

The gap longs the biggest gap-**downs** (dying-stock profile); the survivor-only universe **deletes** exactly the delisted disasters, so the long leg is inflated (§2.1). **If that inflation concentrates on high-dislocation days, the gate is selecting precisely the days where the bias is largest, and the entire gated edge could be a survivorship artifact.** This must be settled before the DSR is believed.

**Mandatory pre-registered diagnostics (computed and reported with the verdict):**
1. **Leg decomposition on gated days, by dislocation tercile** — split the gated gross into LONG-leg vs SHORT-leg contribution. A short-leg-driven or leg-balanced edge is credible; a **long-leg-dominated** edge whose dominance **rises with dislocation** is the artifact signature.
2. **Dislocation ↔ long-leg extremity** — correlate the gate variable (dispersion) with the extremity of the long leg's gaps (how far into the gap-down tail the longs sit). A high positive correlation means the gate preferentially trades the most survivorship-vulnerable longs.

**HOLD rule (PINNED, binding — can only kill/hold, never bless):** if the long leg contributes **> 60%** of the gated median gross **AND** that share **rises monotonically across dislocation terciles**, the verdict is **HELD** (not a PASS) pending Phase-4 point-in-time, delisting-inclusive data — because the effect cannot be distinguished from survivorship inflation on this universe.

> **KEY SIGN-OFF DECISION (3):** the 60% long-leg HOLD threshold and the "rises monotonically" condition — confirm or re-pin.

## 6. Widened confidence interval — a BINDING gate (can KILL on its own)

The gated sample is **~1,277 days (above-median primary)**, not 2,553 — and on that thinner sample, behind a ~17-arm search, **the point estimate is the least-trustworthy number in the study.** The bootstrap CI is the honest one, and it must be able to kill independently.

**BINDING GATE (pinned): the bootstrap 95% CI on the gated net median must EXCLUDE 0 at BOTH cost bounds.** This is a standalone criterion — **it KILLs regardless of every other gate**, including a high point estimate, a passing DSR, or a clean survivorship test. Method: pin the bootstrap as a stationary/block bootstrap over gated trading days (block ~ 5 days to respect autocorrelation), 10,000 resamples, seed 20260711; report the 2.5/97.5 percentiles of the median-net distribution at each bound. Also report the gated effective sample size and the un-gated CI alongside, so the precision cost of abstention is explicit.

## 7. Verdict criteria — inherited + the new gates

**READ FIRST — what a PASS is, and is NOT.** A PASS here **does NOT produce a tradeable strategy.** It reclassifies candidate #1 from "standalone-KILL; banked provisional feature" to **"conditionally tradeable, survivorship-asterisked" — still gated behind Phase-4 point-in-time (delisting-inclusive) data before anyone trades or believes it.** It banks no new feature; it feeds the fusion story with a conditional read of the existing member. A **KILL or HOLD leaves candidate #1 exactly where it is.** No outcome of this study puts capital at risk.

All computed on the **gated** stream (traded days only), both cost bounds. Every criterion is binding:
- beat-random ≥ 95th percentile of the execution-matched null (gated days),
- **DSR ≥ 0.95**, deflated by the new cumulative effective-N (§4),
- CPCV median > 0, positive-fraction > 0.5,
- **absolute-net median > 0** — the gated book must make money NET at both bounds,
- **bootstrap 95% CI on gated net EXCLUDES 0 at both bounds (§6)** — a standalone gate that KILLs on its own, independent of the point estimate and every other criterion,
- **survivorship-interaction HOLD rule (§5) not triggered.**

## 8. What KILLs · what a PASS means
- **KILL** if the gated absolute-net median ≤ 0 at either bound, or DSR < 0.95 after deflation, or the CI includes 0.
- **HOLD** (not pass) if the survivorship-interaction rule triggers — the effect is real in-sample but indistinguishable from bias.
- **PASS** only if net > 0 both bounds, DSR ≥ 0.95 deflated, CI excludes 0, AND survivorship-clean. Even then: exploration-grade, survivorship-asterisked, capital-dependent (₹1L), integer-share-drag-stamped (§7.5 stamps carry over).

## 9. Frozen parameter ledger (pin at sign-off)

| Parameter | Value | Swept? | Charged? |
|---|---|---|---|
| Base signal / direction / entry / exit | A-Z_15 / REVERSAL / 09:30 / **close** | No | — |
| **Gate axis** | **cross-sectional dispersion of raw gap%** | No (1 primary) | primary + 2 axes in search |
| **Gate threshold** | **> trailing-60d median** | No (1 primary) | primary + 4 levels in search |
| Search charged | 3 axes × 4 levels + 4 exits ≈ 17 arms | (charged) | **Yes** |
| Cost corridor | fees @ ₹10k + 1/5 bps (break-even 11.6/15.6) | No | — |
| Null / gate bars / seed / N | inherited (20260711 / 1000 / 95th / DSR .95 / abs-net) | No | — |
| Survivorship HOLD (§5) | long-leg > 60% & rising with dislocation → HOLD | No | — |
| **CI gate (§6)** | bootstrap 95% CI on gated net **excludes 0** both bounds (KILLs alone) | No | — |
| Ledger | cumulative: 15 prior + ~17 new (`cand1abs__*`) | — | Yes |

## 10. Decisions — RULED (operator sign-off 2026-07-12; all accepted)
1. **D1 Gate threshold — above trailing median.** ACCEPTED (least arbitrary; preserves ~50% of days, which matters given the widened-CI problem; top-tercile would shrink an already-thin sample).
2. **D2 Gate axis — raw-gap dispersion.** ACCEPTED (interpretable; a charged axis so ledger accounting is clean; avoids the subtle circularity of gating on a transform of the ranking quantity).
3. **D3 Survivorship HOLD — long-leg > 60% AND rising monotonically with dislocation → HELD.** CONFIRMED as written — the most important pin in the document; the make-or-break test.
4. **D4 Lookback L = 60 days.** ACCEPTED (adaptive, regime-relative, no full-sample leakage).
5. **D5 Charge scope — 3 axes × 4 levels + 4 exits ≈ 17 arms.** ACCEPTED, not negotiated down; the searched space gets charged; the modest effective-N rise (tight clustering, same base book) is the honest outcome, not a loophole.

**TWO BINDING ADDITIONS (operator):** (a) the widened-CI rule (§6) is an explicit **binding gate that KILLs on its own** — not a note; (b) the verdict section (§7) states plainly that a PASS is a **reclassification, not a tradeable strategy** (still Phase-4-gated).

**This is the first study in the program with a genuinely promising prior — which is exactly why it gets the strictest treatment.** If it survives the survivorship test (§5) and the CI (§6), there is something real; if it does not, the ~23 bps was the search talking. Either way it is the honest answer.

**Nothing is run until this freeze is committed + tagged. `src/vendored/` pristine; recorded verdicts untouched.**
