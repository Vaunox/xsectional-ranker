# Deep Dive 02 — Execution & Null Layer (Layer 2)

*Where the murder board did most of its work. Every rule here exists because a naïve alternative was shown to manufacture fake alpha. The `docs/MURDER_BOARD.md` records which alternative each rule replaced.*

## Scope
Ranking, the ex-ante sector cap, risk-parity sizing, Execution-Aware Dollar Neutrality (truncation), the cost corridor, and the Global Null Panel. Built on the frozen imported harness (Deep Dive 03), never inside it.

## Ranking & the two signal arms
Within the eligibility masks, rank the day's names:
- **Signal A:** `(Open − PriorClose)/PriorClose` (raw gap).
- **Signal A-Z:** `raw_gap / ATR(20)` (volatility-adjusted).
Short the top-k (largest gap-ups) from `short_eligible`; long the bottom-k (largest gap-downs) from `long_eligible`. Entry at the frozen window close (~09:45; window swept {15,30,45}); exit at square-off. **A vs A-Z is the sign-vs-magnitude test, in the alpha logic — not the weights.**

## Order of operations (frozen)
`dual masks → circuit filter → rank within mask → ex-ante ⌈k/2⌉ sector cap (skip to next eligible on violation) → risk-parity sizing → Execution-Aware truncation → gross-floor day-drop.`

## Risk-parity sizing (mandatory hygiene, NOT swept)
Each name sized to contribute **equal risk** within its leg (inverse-vol / inverse-ATR). Equal-*dollar* weighting is structurally wrong for a cross-sectional ranker: it hands the P&L to the highest-variance name and measures idiosyncratic noise, not ranking skill. Gap *magnitude* ≠ asset *volatility*; the magnitude hypothesis is tested in the signal (A-Z), never the sizing. (Murder board concession #5.)

## Execution-Aware Dollar Neutrality (truncation — the neutrality mechanism)
Neutrality is enforced in *execution*, because unhedged imbalance leaks conditional tail-beta and construction-time beta-neutrality breaks the instant a high-beta short partial-fills (concessions #1, #2). Steps:
1. **Cap** each name at the pessimistic participation rule (≤ 1% of entry-window volume — frozen).
2. **Sum** the max permitted dollar fill per leg.
3. The **smaller leg sets gross exposure.**
4. **Scale the larger leg down pro-rata** — every name keeps its risk-parity weight; only gross leverage shrinks. **k stays fixed; never drop names** (rank-preserving truncation floats k, which corrupts the null and force-concentrates risk — concession #3).
5. **Gross-exposure floor → drop the day.** If the scaled book falls below the pre-registered ₹ floor, the day is untradeable and dropped from the sample. Day-drop fraction logged.
The pessimistic run thereby answers the real question: *does the ranker beat random on the lowest common denominator of available liquidity?*

### Ambiguity resolved — leg gross under risk-parity weights (2026-07-11)
Step 2's literal "sum the caps per leg" is under-specified once risk-parity weights (Concession #5) enter: summing the per-name caps and then redistributing the leg gross by weight can hand a name **more than its own 1%-participation cap** — placing an un-fillable order, the exact fantasy-liquidity trade the pessimistic bound exists to forbid. **Resolved and frozen 2026-07-11:** a leg's gross is `G_leg = min_i(cap_i / weight_i)` — the largest gross at which **no name breaches its cap at its risk-parity weight**. The book gross is `min(G_long, G_short)` (smaller leg sets it; larger scales pro-rata, weights preserved, k fixed). This is the only reading that honors BOTH the participation cap AND the risk-parity weights; it reconciles with the worked example (short binds at S1: ₹300k/0.5 → ₹600k; both legs scale to ₹600k, dollar-neutral, no cap breached). Implementation: `src/xsranker/execution/truncation.py`.

## Cost corridor (and the Level-2 purchase trigger)
OHLCV cannot measure book depth (volume ≠ depth), so cost is **bounded, not estimated**. Every study runs twice, composing the frozen `round_trip_cost` with two spread inputs:
- **Optimistic:** raw Corwin-Schultz (× Abdi-Ranaldo cross-check) implied spread; full fill.
- **Pessimistic:** ~3× implied spread + the 1%-volume cap with partial fills eating max slippage.

Decision matrix (also the data-spend trigger):
| Outcome | Meaning | Action |
|---|---|---|
| Dies in optimistic | edge can't clear the most generous spread | dead; walk away; do **not** buy L2 |
| Survives pessimistic | robust to draconian slippage | L2 is later optimization, not prerequisite |
| Survives optimistic, dies pessimistic | viability lives in unseen depth | **the sole trigger to authorize the L2 spend** |

A verdict counts only if robust across the corridor. Cap and multiplier are frozen, never swept to conjure a flattering fill rate.

## The Global Null Panel (the benchmark)
The benchmark is a random long-k/short-k draw enduring the **identical** execution model — same masks, circuit filter, sector cap, risk-parity sizing, caps, spread corridor, truncation, gross-floor. **Only selection differs: ranked vs random.** This nulls out liquidity-selection (an asymmetric cost treatment would measure fillability, not skill — and because the signal selects the *least*-liquid extreme-gap names, asymmetry would bias toward a false negative).

Construction:
- **Generate once, globally.** For every trading day across the full history, draw **N** random k-name books (fixed, logged seed → reproducible, versioned artifact) and push each through the identical pessimistic execution model. Result: an immutable per-day null **distribution**.
- **Slice, don't regenerate.** The signal's CPCV path dictates its surviving days; the panel is sliced to those exact days. The signal dictates day-drops; the baseline is masked to them — shared-day-drop by construction.
- **Not purged.** A random draw has zero parameters and cannot learn, so purge/embargo is irrelevant to it; redrawing per CPCV path is statistically identical compute-burn. Principle: *purge what can learn.* This collapses O(days×draws×paths) → O(days×draws).
- The signal must beat a real **percentile** of the null distribution, feeding the DSR/percentile logic honestly (Deep Dive 04).

## No-lookahead precondition (hard gate on the signals)
Prefix-invariance test on A and A-Z: a signal at the entry bar uses only bars ≤ entry; ATR(20), the gap, and any normalization are trailing/point-in-time. Load-bearing, per Layer-1 killer #1.

## To expand later
- Sector-cap tie-breaking when the (k+1)-th name is itself capped.
- Partial-fill accounting inside the pessimistic run (realized fill vs intended, charged).
- N sizing vs null-distribution stability.
