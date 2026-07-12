# Pre-Registration — Candidate #2: Proxy Cumulative Volume Delta (Abnormal Directional Participation)

> **STATUS: FROZEN pre-registration — operator sign-off 2026-07-12. All 7 §14 decisions
> accepted as recommended. BLIND.**
> Every parameter below was pinned **BLIND**: no candidate-#2 result exists, and none will
> be produced until the **build** (the §8.2 cost swap + the signal implementation) lands
> against this frozen spec and only *then* the single blind run executes — a strictly
> **later** commit, the provenance proof that the bar preceded the experiment. This freeze
> commits the pinned spec; the build follows; the run follows that. `src/vendored/`
> pristine; recorded verdicts (RESEARCH_FINDINGS, PROGRESS, prior config freezes) untouched.

---

## 0. Provenance, inheritance, and the missing-doc note

**Inherited UNCHANGED from Phases 0–3** (HEAD `2ccbb64`): the vendored statistical
harness (`src/vendored/` @ predecessor `0c5c592`, hash-tripwired), the data & universe
layer (49 NIFTY-50 survivors, dual eligibility masks, circuit filter, sector map,
gate-zero integrity), the execution layer (risk-parity sizing, Execution-Aware Dollar
Neutrality truncation, ⌈k/2⌉ sector cap, gross floor), the Global Null Panel machinery
(`src/xsranker/null/panel.py`), the Layer-3 gate (`src/xsranker/gate/`) including the
absolute-net bar, the CPCV/PBO structural params, the P&L entry→close engine
(`src/xsranker/backtest/`), and the determinism seed `20260711`.

**The ONLY new or changed elements in this candidate** (everything else is verbatim):
1. a new **signal feature** — proxy cumulative volume delta, arms **V** and **V-A** — and its **trailing per-name volume baseline** (§2, §6);
2. a **CONTINUATION leg-assignment** (long the highest flow, short the lowest — the *opposite* mapping to candidate #1's reversal) (§3);
3. the **cost-corridor swap** from Corwin-Schultz ×{1,3} to **verified fees + a pinned fixed spread** (§8) — the one open item the operator pre-approved, pinned blind here;
4. a **cumulative ledger charge** — candidate #2's arms charged on top of candidate #1's retired arms, plus the previously-uncharged cost-realism re-runs (§9.1–9.2);
5. a **momentum-proxy / gap-re-skin hard pre-run gate (D8, §10.1)** with blind-pinned bands — because V is bar-sign (a price measure), it must prove it is not price/gap in disguise;
6. a **found-and-fixed Rule-4 defect** — candidate #1's ledger streams were written ephemerally and lost; the durable-ledger regeneration + a fail-closed teeth test are a hard build prerequisite before candidate #2's run (§9.3).

**Roadmap reconciliation (resolved).** `docs/END_GOAL_AND_ROADMAP.md` was supplied by the
operator and placed in the repo (uncommitted, record-only). Its **backlog row #2**
pre-commits candidate #2 exactly as built here: *"09:15→entry order-flow asymmetry (up-bar
vs down-bar volume), vs trailing per-name baseline… flow, not price… direction
pre-registered **continuation** (TWAP/VWAP-slicing persistence), not signed by an opening
price move (that would smuggle in dead momentum)."* This draft is consistent on every
point. The roadmap's feature bar (**real + independent, small is fine**) and its capstone
(*"the effective-N machinery prices [independence]… fake diversification collapses
effective-N and is killed"*) directly endorse §9.1 (cumulative ledger, D6) and §10
(independence diagnostic). **Compliance with the roadmap's standing rule** (*"record-only…
must not influence any blind pre-registration [or] leak features into a construction"*):
this construction draws **only** from the in-session signal spec + the frozen machinery;
the roadmap is used to *confirm* candidate identity and independence framing, never to add
a feature or alter the blind construction. Two roadmap open threads are engaged where they
touch this candidate: exit-timing (§5) and the 1/N-ensemble-vs-within-book-sizing
distinction (§9.1).

---

## 1. Objective & the backlog frame (read this first — it sets the bar)

We are **not** hunting a standalone winning strategy. Candidate #2 is one **small,
individually-vetted, independent, morning-computable** signal destined for a fusion
ensemble (an IPO-advisor-style calibrated classifier). **A candidate's bar is
real + independent, not big.** Independence is load-bearing: correlated features collapse
effective-N and add nothing to the fused book's ability to clear the cost floor.

The single research question is unchanged in *form* from candidate #1: **does the ranker
beat a random long-k/short-k selection that endures the identical execution model, net of
cost — and make money in absolute terms?** The information axis is new: **directional
participation (volume flow)**, not overnight price gap.

---

## 2. Signal definition (blind, a-priori, mechanism-first)

### 2.1 Bars, classification, and the delta
- Slice the entry window (09:15 → entry instant, §4) into its constituent **5-minute
  bars** (the cache interval, `data.interval: "5minute"`).
- **Classify each bar by its own close-vs-open** (strict inequalities):
  - **up** ⟺ `close > open`
  - **down** ⟺ `close < open`
  - **flat** ⟺ `close == open` (a doji: genuine no-conviction participation)
- Let `ΣV_up`, `ΣV_down`, `ΣV_flat` be the summed **bar volumes** in each class over the
  window, and `ΣV_total = ΣV_up + ΣV_down + ΣV_flat` (all bars, flat included).

> **Why "proxy" CVD.** True cumulative volume delta needs tick-level buy/sell
> classification (Level-2 / trade-direction data), which this program does **not** have
> (roadmap backlog #7, OFI/L2 depth, is *permanently data-gated* — recorded, never faked).
> Candidate #2 approximates it from **5-minute OHLCV bar volume + each bar's own
> close-vs-open sign** — no L2, no tick data. That is exactly why it is a **cheap, OHLCV ✓**
> candidate (backlog row #2) rather than a data-gated one.

### 2.2 Two pre-registered arms (parallel to candidate #1's A / A-Z)
Both arms are signed **only** by directional volume; neither uses any price move (§3
hard constraint). Both are charged to the ledger.

- **V — raw proxy CVD (directional participation fraction).**
  `V = (ΣV_up − ΣV_down) / ΣV_total`  ∈ [−1, +1].
  The within-day net directional share. Flat volume sits in the denominator only, so it
  correctly dilutes conviction toward 0. Magnitude-blind across names (a name barely
  trading and a name in a frenzy both cap at ±1) — the **sign/direction** arm.

- **V-A — abnormal proxy CVD (baseline-relative directional participation).**
  `V-A = (ΣV_up − ΣV_down) / V_baseline`, where `V_baseline` is the name's **trailing
  per-name entry-window-volume baseline** (§6).
  This is the **magnitude/anomaly** arm — "abnormal directional participation." It is
  algebraically `V × (ΣV_total / V_baseline)` = the raw directional fraction scaled by
  how abnormal today's window volume is versus the name's own normal. It exceeds ±1 when
  the name trades an abnormal multiple of its baseline one-sidedly — the institutional
  order-slicing signature. Price-neutral by construction (pure volume, per-name
  normalized).

**Why two arms, not one.** The spec gives *both* the raw formula (`/ΣV_total`) *and* the
"abnormal relative to a trailing baseline" concept. A single arm would use only one. V/V-A
honor both and mirror the settled A/A-Z structure exactly — the magnitude hypothesis tested
in the **alpha logic**, not the sizing (murder-board concession #5). This keeps the arm
count at 2×3 = 6, so **no machinery change to the arm-count/ledger plumbing**.
**Confirmed at sign-off (D1 accepted):** on candidate #1 it was the **normalized** arm
(A-Z) that carried the real edge while raw A did not — *direct evidence the normalization
axis matters* — so V (raw) vs V-A (baseline-normalized) is the same sign-vs-magnitude test,
justified. V-A is the mechanistically-favored ("abnormal") arm; V is the raw sign arm.

### 2.3 Selection
Rank the eligible cross-section by the arm's value via the frozen
`cross_sectional_rank` (reuse `src/xsranker/signals/ranker.py`). **CONTINUATION (§3):
LONG the highest-k, SHORT the lowest-k.** Non-finite values are dropped (a name we cannot
rank is not tradeable) — the existing finite-filter in `rank_panel`.

### 2.4 Edge cases & feasibility guards (point-in-time, fail-closed)
- `ΣV_total = 0` (name did not trade in the window) ⇒ `V` non-finite ⇒ dropped.
- `V_baseline = 0` or `< 20` complete prior-day window volumes ⇒ `V-A` non-finite ⇒ dropped (§6).
- All-flat window ⇒ numerator 0 ⇒ `V = V-A = 0` (finite; ranks mid — correct: no conviction).
- **Phase-1 honesty stamp:** on the large-cap survivor cache these guards fire ~0% (large
  caps always trade the morning window and have full history); logged like the ~0%
  eligibility-mask fire-rate. They go load-bearing in the Phase-4 mid-cap crucible.

---

## 3. Direction + mechanism (CONTINUATION) + the hard constraint

**Direction (pre-registered): CONTINUATION.** LONG the names with the highest
(most net-buying) directional flow; SHORT the names with the lowest (most net-selling).

**A-priori mechanism.** Institutional VWAP/TWAP execution algorithms slice large parent
orders into child orders spread across the session. Sustained one-sided child-order flow
in the morning window is a *fingerprint of an unfinished large order* that persists into
the afternoon — so morning net-buying predicts continued net-buying (price drift up) and
vice-versa. This is a **participation-persistence** hypothesis, mechanistically distinct
from price momentum.

> **HARD CONSTRAINT (inviolable): direction is signed by the FLOW ITSELF, never by a
> price move.** No opening-return gate, no close-in-range filter, no VWAP-position, no
> breakout-direction, no gap sign. The sign of the signal comes *only* from
> `ΣV_up − ΣV_down` (bars classified by their own close-vs-open, weighted by volume). Any
> price-signed variant smuggles back the already-dead momentum/gap axis and is
> **forbidden**. (Bar-level close-vs-open classifies a *bar's* volume as buy- or
> sell-initiated — a microstructure proxy for trade direction; it is **not** a price
> predictor and never gates the cross-sectional direction, which is flow.)

**Independence from candidate #1 by construction.** Candidate #1 (retired) ranked on the
**overnight price gap** and traded **reversal** (long the biggest gap-downs). Candidate #2
ranks on **intraday directional volume** and trades **continuation** (long the highest
flow). Different information axis, opposite direction, disjoint construction. This is the
independence bar met a-priori; the empirical confirmation is §10. **Explicitly excluded**
(re-tests the dead axis): any residualized / sector-adjusted / market-adjusted **gap**
variant.

---

## 4. Measurement window + prefix-invariance (HARD GATE)

- **Windows swept `{15, 30, 45}` minutes** after 09:15 (inherit
  `calendar.entry_window_default_min: 30` as the default; the machinery is parametrized).
  Each window is a distinct arm/label.
- The window is the half-open interval **[09:15, entry_instant)**, `entry_instant =
  09:15 + W min`. Include **exactly** the 5-minute bars whose **close ≤ entry_instant**
  (equivalently, bar open-stamp `< entry_instant`): W=15 → 3 bars (09:15/20/25); W=30 → 6
  bars; W=45 → 9 bars. A bar stamped **at or past** the entry instant (whose close is not
  yet observable at entry) is **excluded**.
- Unlike candidate #1 (gap is known at the open, constant within the day), candidate #2's
  signal **genuinely consumes the intra-window bars**, so the window now governs *both*
  the signal computation and the entry→close label — a cleaner, single meaning ("observe
  09:15→entry, act at entry, hold to close").

**Prefix-invariance is the load-bearing leakage gate** (per Deep Dive 02, Layer-1 killer
#1). Pre-registered teeth for candidate #2 (new, mirroring the candidate-#1 suite):
1. Appending arbitrary **post-entry bars** to the trading day must **not** change `V`,
   `V-A`, or any name's rank (the numerator/denominator sum only bars with close ≤ entry).
2. The baseline uses only days **strictly < D** (appending future days is a no-op).
3. A bar stamped exactly at the entry instant is **excluded** (boundary teeth).
Plus the inherited train/serve-skew suite. Scope limit carried verbatim from candidate #1:
the sweep cannot test sub-15-min entry, so if the entire edge lives in the first ~10 min
it reads as an (honest) null, not a flaw.

---

## 5. Entry / exit / execution (INHERITED UNCHANGED)

All of the following are program-wide execution properties tied to the **universe and
liquidity structure**, not to the signal — inherited verbatim, **not** re-picked for this
candidate (re-picking would be a new researcher degree of freedom):

| Element | Value | Source |
|---|---|---|
| Entry | at window close (~09:45 for W=30), executed via the frozen entry→close engine | `src/xsranker/backtest/pnl.py` |
| Exit | session close (square-off 15:30 IST) | inherited |
| `k` per leg | **5** | `execution.k_per_leg` (frozen blind, `31cc292`) |
| Sizing | inverse-vol / risk-parity (mandatory hygiene) | `execution/sizing.py` |
| Neutrality | Execution-Aware Dollar Neutrality (fixed-k pro-rata truncation, weakest-leg gross) | `execution/truncation.py` |
| Sector cap | ⌈k/2⌉ = 3 per leg | `execution.sector_cap_divisor: 2` |
| Participation cap | ≤ 1% entry-window volume (book formation only — see §8 note) | `execution.participation_cap: 0.01` |
| Eligibility | dual `long_eligible` / `short_eligible` masks; circuit-lock filter | `data/universe/` |
| Gross floor | **₹100,000** (v2, `7e6a829`) | `execution.gross_floor_inr` |

**Why inheriting the floor and k is not peeking.** The ₹100k floor was derived
*mechanically* from universe price structure (the minimal notional at which every selected
name forms a whole-share position on the 49-name universe) with **zero sight of any
return** — it is name-selection-agnostic and holds for *any* selection on this universe,
including candidate #2's. `k=5` is the top-~10% tail of a 49-name universe. Neither was
tuned to candidate #1's outcome, so inheriting carries no outcome-informed hazard.
Candidate #2's **capacity** (which names it picks may be more liquid than the extreme-gap
thin-name selection) is an **outcome to be measured blind**, not assumed.

**Exit = session close is retained (roadmap open-thread engaged, not activated).** The
roadmap carries an exit-timing hypothesis — that a *fast-reversal* edge may be front-loaded
and given back by close, with its home in a morning-decided exit horizon. For candidate #2
this concern is **weaker, not stronger**: the mechanism is **continuation** (persistent
institutional flow), which predicts the move *persists through the session*, so holding to
close is the mechanistically-aligned horizon — not a mismatch. Introducing a variable
morning-decided exit horizon now would add a new researcher degree of freedom (which
horizon?) and new machinery to a blind standalone smoke test. So exit = close is kept
(inherited); the exit-timing hypothesis stays a **carried-forward open thread**, live for a
future candidate whose edge is marginal on *timing* rather than crushed by fees — not this
one. All three windows {15,30,45} enter at 09:30 / 09:45 / 10:00 — morning-computable,
consistent with the roadmap's single-morning-decision constraint.

---

## 6. Trailing baseline (BLIND PIN) — detail

`V_baseline` for name *s* on day *D*, window *W*:

> the **median** of `{ ΣV_total(s, W, d) : d ∈ the 20 trading days strictly before D }` —
> i.e. the same 09:15→entry window's total volume on each of the prior 20 completed
> trading days, taken as a robust central value.

Pinned choices, each a-priori:
- **Statistic = median** (not mean/EWMA). Rationale: the lookback *will* contain the
  name's own prior event/earnings volume spikes; a **mean** baseline is inflated by
  exactly the abnormal days we are trying to measure deviation *from*, biasing V-A
  downward heteroscedastically. Median is the honest "typical" level and matches the
  house robustness convention (median across pairs in the spread estimators). *(D2 — accepted.)*
- **Lookback N = 20 trading days.** Inherits the program's existing normalization horizon
  (`signal.atr_period: 20`, the frozen ATR-20) and the standard ~1-month ADV convention.
  Reusing the frozen horizon avoids introducing a *new* free constant. *(D3 — accepted.)*
- **Window-matched & point-in-time.** The baseline for the W-minute arm uses the W-minute
  window on prior days only (never the full day, never full-sample, never day D or later).
- **Minimum-history guard:** require all **20** complete prior-day window volumes; else
  the name is non-finite for V-A that day and dropped (§2.4). Mirrors ATR-20 needing 20
  days.

This is the sole locus where "abnormal" enters, and it is purely a **volume** baseline —
no price, preserving the §3 hard constraint.

---

## 7. The null (INHERITED machinery, RE-COSTED)

The benchmark is the **Global Null Panel** (`src/xsranker/null/panel.py`), unchanged:
random long-k/short-k books drawn under **constraints identical to the signal** — same
dual masks, ⌈k/2⌉ sector cap, disjoint legs, risk-parity sizing, Execution-Aware
truncation, and the **same ₹100k floor** — via rejection-sampled, feasible,
floor-clearing draws (**0% zero-pad**, the fixed null-construction bug). Only *selection*
differs (random vs ranked), so "beats random" measures selection skill alone.

- **Seed `20260711`, N = 1000 draws/day** — inherited determinism + percentile-resolution
  params (not research DOFs). The random *selection* panel is regenerated **byte-identical**
  to candidate #1's (same universe + cfg + seed) — the null is memoryless and
  selection-only, so it does **not** depend on candidate #2's ranking. *(Inheriting the
  seed is recommended for reproducibility consistency; a fresh seed is a trivial
  alternative — D4: inherit, accepted.)*
- **Re-costed** under the new corridor (§8): the null's per-day net returns are recomputed
  through the *same* fees+fixed-spread cost path as the signal. **Cost symmetry re-asserted**
  — both signal `build_book` and null `build_random_book` route through the identical
  `finalize` → cost path (the monkeypatch-spy symmetry proof re-runs green).
- **Sanity tell (whole error class):** the true null median net must be **slightly
  negative on both bounds** (random books pay cost with worthless selection). Because the
  new corridor's costs are *lower* than candidate #1's CS corridor, the null median will be
  **less negative** than candidate #1's −86/−234 bps — but must remain **< 0**. A null
  median ≈ 0 or positive ⇒ **STOP** (a zero-pad / floor-relaxation regression).

---

## 8. The cost corridor (NEWLY PINNED BLIND — the swap)

This executes the operator-pre-approved swap: **retire Corwin-Schultz ×{1,3}; adopt the
standard cost model = verified statutory fees + a pinned, defensible fixed spread**
(RESEARCH_FINDINGS §7.3). Pinned blind, before any candidate-#2 result.

### 8.1 The two bounds
| Bound | Composition | Round-trip spread pinned |
|---|---|---|
| **Optimistic** | verified fees + fixed conservative spread | **5 bps** |
| **Pessimistic** | verified fees + fixed AR-median-magnitude spread | **18 bps** |

- **Verified fees** = the frozen, Zerodha-verified statutory schedule (`config/costs.yaml`,
  unchanged): brokerage 0.03% / ₹20 cap, STT 0.025% sell, exchange 0.00297%/side, SEBI
  0.0001%/side, stamp 0.003% buy, GST 18% → ~4.5 bps/name @ ₹500k → ~8.2 bps @ ₹100k.
- **Optimistic spread = 5 bps round-trip.** A genuine, conservative lower bound — tighter
  than any measured NSE large-cap spread, generous-but-not-fantasy.
- **Pessimistic spread = 18 bps round-trip.** Anchored to the **AR-median spread
  *magnitude*** of this large-cap universe (RESEARCH_FINDINGS §5.3: AR median 18.5 / 19.3 /
  11.8 bps on the traded names; midpoint of the user's 16–20 bps band). Applied as a
  **uniform fixed constant** — **explicitly NOT per-name Abdi-Ranaldo**, whose p90–95 ≈
  108–142 bps tail and ~656 bps max are **estimator noise**, not tradeable cost, and whose
  per-name form would make the corridor selection-dependent. *(D5 — accepted, confirmed as reasoned.)*

**Not outcome-informed.** 18 bps describes a **universe liquidity property** (the typical
AR spread level of NSE large-cap survivors), measured incidentally during candidate #1's
cost work — it is **not** candidate #1's edge/return/verdict, and it is pinned blind to any
candidate #2 return (there is none). A fixed constant cannot be reverse-engineered from
candidate #2's selection.

**Estimator-free & symmetric.** Neither bound calls any spread estimator at run time — the
spread is a pinned constant. Signal and null pass through the identical cost function, so
cost symmetry (RESEARCH_FINDINGS §7.4) holds under this corridor as under any.

### 8.2 Exact implementation delta (applied in the build — §15.2; the pinned values below ARE the blind provenance, frozen in this doc now; the code lands post-freeze, pre-run)
**`config/default.yaml` `cost:` block** — retire the CS multipliers, add fixed spreads:
```yaml
cost:
  # Candidate #2 standard cost model (RESEARCH_FINDINGS §7.3): verified statutory fees +
  # a pinned defensible FIXED spread. Corwin-Schultz is RETIRED from the active cost path
  # (it over-reads ~2-3x on selected names, §5.3). Spreads are round-trip proportional, bps.
  optimistic_spread_bps: 5      # conservative lower-bound spread (fixed, uniform)
  pessimistic_spread_bps: 18    # AR-MEDIAN-magnitude spread (fixed, uniform); NOT per-name AR
```
**`src/xsranker/execution/cost.py::cost_corridor`** — replace the CS-`spread`×multiplier
mechanism with the two fixed round-trip spreads and **zero the square-root impact term**,
so each bound is cleanly *fees + fixed spread*:
- optimistic  = `replace(base, slippage_base_rate = opt_bps/2·1e-4, slippage_impact_coefficient = 0.0)`
- pessimistic = `replace(base, slippage_base_rate = pess_bps/2·1e-4, slippage_impact_coefficient = 0.0)`
- round-trip = per-side `slippage_base_rate` × 2 (buy+sell) = the pinned spread; statutory
  fees unchanged; **no CS/AR call**, participation no longer feeds slippage (impact = 0).

**Why impact_coefficient → 0.** The old sqrt-impact add-on was part of the retired
CS-corridor apparatus. The fixed 18 bps pessimistic spread (3–9× real large-cap quotes)
*is* the conservative envelope; a separate participation-scaled term would double-count and
re-introduce the very participation-sensitivity the swap removes. **The 1%-participation
cap keeps its book-formation role** (per-name `max_fill_inr`, truncation, gross floor,
capacity) — it simply no longer also drives a slippage add-on. `config/costs.yaml`
`slippage:` stays as the frozen statutory reference; the corridor sets these fields
explicitly via `replace` (the vendored `CostModel` is composed, never edited).

---

## 9. The gate (INHERITED) + the absolute-net gate + the ledger

Per arm × per cost bound (`src/xsranker/gate/arm.py::evaluate_arm`), unchanged machinery,
all bars inherited with provenance:

| Criterion | Bar | Stream | Source |
|---|---|---|---|
| beat-random percentile | ≥ **95th** (α = 0.05) | excess-over-null (Ruling 1) | `gate.null_percentile` |
| DSR | ≥ **0.95** | excess, deflated by **cumulative** effective-N | `gate.dsr_min` |
| CPCV median path-Sharpe | **> 0** | excess | `gate.cpcv_median_min` |
| CPCV positive fraction | **> 0.5** | excess | `gate.positive_fraction_min` |
| PBO (cross-arm) | ≤ **0.20** | program-level, `gate/program.py` | `gate.pbo_max` |
| **absolute-net** | median daily net **> 0**, **per bound** | **raw net** (not excess) | `gate.absolute_net_min` |

- **The absolute-net gate is the one that retired candidate #1** and is inherited
  **verbatim**: beat-random is *necessary but not sufficient*; an arm can beat a cost-bled
  null yet lose money net of cost. It binds per bound and rides the corridor. This is the
  gate candidate #2 must clear in *absolute* rupees, not merely versus random.
- **CPCV/PBO structural params inherited:** `cpcv_n_groups=6`, `cpcv_k_test=2`,
  `pbo_n_splits=16`, `periods_per_year=252`. Near-threshold STOP-and-flag bands inherited
  (`near_margin_*`, incl. ±2 bps on absolute-net → NEAR_THRESHOLD → operator rules).

### 9.1 Ledger — CUMULATIVE across candidates (Inviolable Rule 4)
Candidate #2 charges **2 signals (V, V-A) × 3 windows {15,30,45} = 6 arms** to the
**program-wide, persistent** effective-N ledger — **on top of** candidate #1's already-charged
6 retired arms. The DSR deflates by the **cumulative cluster-adjusted effective-N over all
arms ever run** (Rule 4: "the ledger persists across sessions and phases"). The cost
corridor is a mandatory both-bounds robustness range, **not** a search dimension (Ruling
3) — not 12 trials.

**The independence tension, stated honestly:** because candidate #2 is on a *genuinely
independent* axis (§3, §10), the correlation-participation-ratio clustering will **not**
collapse it into candidate #1 — so the cumulative effective count rises toward ~11–12, and
candidate #2 faces a **materially higher DSR deflation** than a standalone 6-arm charge
would impose. That is the correct, conservative price of having taken a prior look, and it
is exactly what the ledger exists to charge — the roadmap capstone endorses precisely this:
*"the effective-N machinery prices this: fake diversification collapses effective-N and is
killed."*

> **Not to be conflated with the roadmap's 1/N rule.** The roadmap bans mean-variance and
> defers inverse-vol *as the **ensemble** allocator* (how the Phase-3 classifier weights
> **candidates** against each other — 1/N for the gate test). That is a different layer from
> candidate #2's **within-book name sizing**, which is inverse-vol/risk-parity by settled
> mandatory hygiene (murder-board concession #5) and is inherited unchanged here. No tension:
> component-vs-component weighting (Phase 3, 1/N) ≠ name-vs-name sizing inside one book.

*(D6 — accepted.)*

### 9.2 What is charged, and why a near-zero increment is CORRECT (R1, operator-ruled 2026-07-12)

The ledger charges each trial's **pessimistic excess-over-null stream** (`report.py`), the
same selection-alpha stream the DSR runs on (Ruling 1). The previously-uncharged
**cost-realism re-runs** (fees-only / fees+5 bps / fees+AR, the post-hoc re-costings that
re-based the candidate-#1 KILL) **are now charged** — for Rule-4 completeness (every swing
recorded).

**Their marginal effective-N is ≈ 0, and that is the mechanism working, not failing.** A
re-costed run is *the same selection at a different cost* — not a new bet. Cost **cancels in
the excess stream** (signal and null pay ~the same cost — the identical reason
RESEARCH_FINDINGS §5.1 records *opt-DSR ≈ pess-DSR*), so a re-costing is a ~99%-correlated
near-duplicate stream, and the correlation-participation-ratio **correctly recognises it as
not an independent look** and barely moves effective-N. Charging these on the *net* stream
to force them to move the bar would invent a penalty for something that is not an
independent look and would contradict DSR-on-excess (Ruling 1). **The ledger counts
independent looks, not re-pricings.** A future reader must not mistake this near-zero
increment for the ledger *failing to charge* — it is charged, and it clusters to ~zero
because that is the honest verdict on a re-priced duplicate.

**effective-N is a gate-time quantity, never a pinned literal** (Rule 4): it is computed
from the actual stream set when the gate judges candidate #2 (which needs candidate #2's own
6 streams, non-existent until the run). The freeze pins the **charging policy** (this
section + §12) and the **DSR threshold** (0.95) — not an effective-N number. The
load-bearing driver of the cumulative figure is **D8 (§10.1)**: if V/V-A are independent of
the gap axis, candidate #2's 6 arms add ~fully (cumulative eff-N ≈ 12, a higher bar); if D8
finds V is a price re-skin, they cluster with candidate #1's arms — but then the signal dies
on the independence finding itself.

### 9.3 Ledger-persistence — a found-and-fixed Rule-4 defect (R2, hard build prerequisite)

**Defect (found this session).** The ledger's stated purpose is a *durable, cumulative,
reproducible* record of every trial stream across sessions (`ledger.py` docstring; Inviolable
Rule 4). But candidate #1's run wrote its six streams to an **ephemeral `storage_dir` that
was never committed** — they are **gone**; only the `effective-N ≈ 5.98` figure survives, as
prose in RESEARCH_FINDINGS. **An anecdote does not discharge the ledger's purpose.** This is
the **same class of silent hole as the null-construction bug** (§7-class): a defect that
would quietly **rot the DSR bar across candidates** — every future candidate would deflate
against an unreconstructable, under-counted trial history.

**Fix (lands in the build; MUST be green BEFORE candidate #2's run — not after):**
1. **Regenerate candidate #1's 6 arm streams deterministically** (seed `20260711`, the frozen
   machinery — the run is reproducible) **plus the cost-realism re-runs**, and **durably
   persist + commit the ledger** into the repo, so the cumulative charge is *real and
   reproducible at the moment the gate judges candidate #2*.
2. **Teeth test — fail closed.** The gate MUST raise (never silently proceed) if any prior
   candidate's streams are missing from the durable ledger at gate time. **No
   silently-undercounted effective-N, ever.** A test that stubs the ledger empty must make
   the gate go red.

Recorded here as a found-and-fixed defect so it enters the program record with the same
weight as the null bug — a correction that protects every future candidate's DSR bar.

---

## 10. Independence — the backlog bar (pre-registered checks)

- **A-priori (primary):** different information axis + opposite direction + disjoint
  construction + the §3 hard constraint (flow-signed, never price). *Necessary but NOT
  sufficient* — see D8: the bar-level close-vs-open classification imports intra-bar price
  direction, so construction alone cannot certify independence; D8 is the empirical backstop.

### 10.1 D8 — momentum-proxy / gap-re-skin gate (HARD PRE-RUN GATE, pinned blind)

**The threat (operator, accepted).** V classifies each bar by **close-vs-open — a price
measure**. A stock drifting up all morning yields mostly up-bars → high V → long. So V (and
to a lesser degree V-A) **may substantially be volume-weighted morning momentum in disguise**
— a *price re-skin*, not an independent flow signal. The §3 "flow-signed" argument governs
the cross-sectional *direction* (no single price move signs a leg) but does **not** neutralize
this, because the bar sign is itself a price measure. This threatens **two** things:
- the **independence claim** (a fusion stable needs independent signals, not a price re-skin); and
- **D6's clustering assumption** — if V is really price, candidate #2's trials **cluster** with
  candidate #1's gap arms, the cumulative effective-N does **not** rise as D6 assumes, and the
  DSR accounting is wrong.

**What is computed (BLIND, before any run).** A signal-construction diagnostic — correlations
of the *signal values*, no P&L — so it runs *before* the strategy run and its bands are pinned
here sight-unseen. **Per window {15,30,45}**, report **both Pearson and Spearman**; the **gate
is on the Spearman (rank) correlation**, because *ranking* is what the strategy acts on:
- `corr(V, morning return open→entry)` and `corr(V-A, morning return open→entry)`
- `corr(V, candidate #1's gap%)` and `corr(V-A, candidate #1's gap% ÷ ATR%)` (matched normalization)

**Pinned interpretation bands (BOTH sets, blind, on rank-corr):**

| Comparison | rank-corr ≥ 0.8 | rank-corr < 0.5 | 0.5 ≤ rank-corr < 0.8 |
|---|---|---|---|
| **vs morning return** | V is a **momentum proxy** — record as a finding; the independence claim **and** D6's clustering assumption **must be revised before any verdict is trusted** | independence stands | **STOP — bring to operator** |
| **vs candidate #1's gap** | V is substantially a **gap re-skin** — fusion value ≈ nil; record as a **finding, not a feature** | independence from the retired signal stands | **STOP — bring to operator** |

- **Hard pre-run gate.** ≥ 0.8 on either comparison ⇒ record the proxy/re-skin finding and
  revise the independence + D6 accounting **before** any P&L verdict is trusted; 0.5–0.8 ⇒
  **STOP** for operator ruling; only an all-`< 0.5` result clears independence and lets the
  D6 cumulative-ledger assumption stand as pinned. Pearson is reported alongside (linear-vs-
  monotone divergence is itself a tell), but the *gate* is the rank correlation.

### 10.2 Post-run independence complement (logged diagnostic)

After the run, additionally compute (a) the correlation of candidate #2's per-day
selection-alpha (excess-over-null) stream with candidate #1's, and (b) the mean daily
name-overlap (Jaccard) between the two books' selections — fusion-readiness diagnostics.
|ρ| > 0.5 ⇒ flag for operator ruling before any "keep for the ensemble" reading. The a-priori
construction (§3) is the primary guarantee; **D8 (§10.1) is the pinned pre-run gate**; this is
the post-run confirmation.

---

## 11. Survivorship direction — **INVERTED vs candidate #1** (RULED, D7, 2026-07-12)

Candidate #1's phased logic — "a Phase-1 survivor-cache **KILL is hyper-trustworthy**" —
rested entirely on it **longing the biggest gap-downs**: dying names gap down, the ranker
*buys* them, survivor-only *deletes* exactly those catastrophic longs ⇒ the long leg is
**inflated** ⇒ Phase-1 is a subsidized **upper bound** ⇒ a KILL "ends it for free."

**That logic does NOT transfer to candidate #2, and its sign flips:**
- Candidate #2 is **continuation, flow-signed**. It does **not** long the gap-downs.
- It **shorts** names in heavy morning **net-selling** — which is precisely the
  distribution/panic profile of a name heading toward delisting. Survivor-only **deletes**
  those names, i.e. deletes candidate #2's **systematically profitable shorts**.
- ⇒ Survivor-only **penalizes** (not subsidizes) candidate #2. Phase-1 is closer to a
  **lower bound** than an upper bound.

**Consequence for the verdict matrix (candidate #2 specific):**
- A Phase-1 **KILL is *not* conclusive** — the strategy was handicapped, not subsidized —
  so it does **not** "end it for free." It routes to Phase-4 rather than closing the book.
- A Phase-1 **PASS is *more* trustworthy** (it cleared the bar despite the handicap) — but
  still **provisional** per the standing rule that only the Phase-4 point-in-time crucible
  issues a true PASS.

Caveat: on the **large-cap survivor cache** delistings are ~nil, so the Phase-1
survivorship *magnitude* is small for candidate #2 (as it was modest for candidate #1); the
bias **direction** bites at Phase-4. But the direction is what governs how a verdict is
*read*, and it is now settled.

**RULED — adopted 2026-07-12 (D7, operator sign-off).** The trust logic **flips** for
candidate #2: a Phase-1 **PASS is the trustworthy outcome** (it won *despite* a survivorship
handicap); a Phase-1 **KILL is NOT conclusive** and **routes to Phase-4** — it **cannot
retire the signal for free** the way candidate #1's KILL did. This is carried prominently
into the verdict section (§13.0) so no future reader mistakes a Phase-1 KILL for definitive.

---

## 12. Frozen parameter ledger (the blind table — PINNED, sign-off 2026-07-12)

| Parameter | Frozen value | Swept? | Charged? | New/Inherited |
|---|---|---|---|---|
| Signal arms | **V** (raw), **V-A** (abnormal) | both run | Yes (2) | **New** |
| Direction | **CONTINUATION** (long highest, short lowest) | No | — | **New** |
| Entry window | 30 default | `{15,30,45}` | Yes | Inherited |
| Bar interval | 5-minute | No | — | Inherited |
| Bar class tie | `close==open` ⇒ flat (num 0, denom incl.) | No | — | **New** |
| Baseline statistic | **median** | No | — | **New** |
| Baseline lookback | **20 trading days**, window-matched, prior-only | No | — | **New** |
| `k` per leg | 5 | No | — | Inherited |
| Sizing / neutrality / sector cap / masks / circuit | inverse-vol / truncation / ⌈k/2⌉=3 / dual / conservative | No | — | Inherited |
| Gross floor | ₹100,000 | No | — | Inherited |
| Participation cap | 1% (book formation only) | No | — | Inherited |
| **Optimistic spread** | **5 bps** round-trip, fixed | No | — | **New (swap)** |
| **Pessimistic spread** | **18 bps** round-trip, fixed | No | — | **New (swap)** |
| Slippage impact coeff | **0** (spread carries slippage) | No | — | **New (swap)** |
| Statutory fees | verified Zerodha schedule | No | — | Inherited |
| Null seed / N | 20260711 / 1000 | No | — | Inherited |
| null-percentile | 95th (α=0.05) | No | — | Inherited |
| DSR / PBO / CPCV-median / pos-frac | 0.95 / 0.20 / >0 / >0.5 | No | — | Inherited |
| absolute-net | median net > 0 per bound | No | — | Inherited |
| CPCV/PBO structural | 6 / 2 / 16 / 252 | No | — | Inherited |
| Ledger | **cumulative**: cand-#1 6 arms + **post-hoc cost-realism re-runs** (fees-only / fees+5 / fees+AR) + cand-#2 6, cluster-adjusted; **eff-N computed from streams at gate time, never a pinned literal** (Rule 4) | — | Yes | **New policy** |

---

## 13. Verdict logic & STOP-and-flag

### 13.0 ⚠️ Survivorship INVERTS for this candidate — a Phase-1 KILL is NOT definitive (operator-ruled 2026-07-12)

> **Read this before interpreting any Phase-1 verdict for candidate #2.** Candidate #1's
> rule — *"a Phase-1 survivor-cache KILL is hyper-trustworthy"* — **does NOT apply here, and
> its trust logic flips.**
>
> - Candidate #1 **longed** the gap-downs (dying-stock profile) → survivor-only deleted its
>   **disasters** → **subsidized** → a KILL was hyper-trustworthy (it failed even while helped).
> - Candidate #2 **shorts** the heaviest morning net-sellers (**same** dying-stock profile),
>   but **continuation makes those shorts profitable** → survivor-only deletes its **winners**
>   → **penalized** (it is *handicapped*, not helped).
>
> **Therefore, for candidate #2:**
> - a **Phase-1 PASS is the trustworthy outcome** — it won *despite* a survivorship handicap
>   (still provisional; only the Phase-4 crucible issues a true PASS);
> - a **Phase-1 KILL is NOT conclusive** — it **routes to Phase-4** and **cannot retire the
>   signal "for free."** Do **not** read a Phase-1 KILL as definitive. This is the exact
>   inverse of candidate #1, where a KILL *did* end it for free.

### 13.1 Per-arm / per-bound decision

- An arm PASSES a bound iff **all** binding criteria pass at that bound (beat-random, DSR,
  CPCV-median, positive-fraction, PBO, **and absolute-net**). A verdict counts only if
  robust **across both corridor bounds** (survives-optimistic-dies-pessimistic ⇒ the sole
  L2-spend trigger, per the corridor matrix).
- **D8 is a hard PRE-run gate (§10.1):** the momentum-proxy / gap-re-skin rank-correlations
  are computed and adjudicated against the pinned bands **before** the strategy run; ≥ 0.8
  records a proxy/re-skin finding and revises the independence + D6 accounting; 0.5–0.8 STOPS.
- **STOP-and-flag to the operator before recording** on: any PASS, any NEAR_THRESHOLD,
  any INSUFFICIENT, the null-median-sanity tell failing (§7), a **D8 rank-corr ≥ 0.5** (§10.1),
  the |ρ|>0.5 post-run independence flag (§10.2), or the survivorship-direction ruling (§11).
  No tweak-to-pass; single blind run; every arm charged.
- All results **exploration-grade** until the Phase-4 crucible.

---

## 14. Decisions — RESOLVED (operator sign-off 2026-07-12)

**All seven accepted as recommended.** D5/D6 confirmed as reasoned (not negotiated): the
AR-median-as-uniform-constant correctly dodges the ~656 bps per-name estimator tail, and
because flow and price are independent axes the clustering won't collapse them, so
candidate #2 rightly faces a higher DSR bar. D7 is the load-bearing ruling (verdict trust
inverts — §11, §13.0).

| # | Decision | Ruling (accepted as recommended) | Bar impact |
|---|---|---|---|
| **D1** | Two arms **V/V-A** vs a single abnormal arm | **Two** (honors the in-session raw formula *and* the baseline; mirrors A/A-Z; 6-arm plumbing reused). *Note:* backlog row #2's terser "vs trailing baseline" phrasing leans toward V-A as the core arm — if you prefer a single arm, drop V and keep V-A (the mechanistically-favored "abnormal" one). | arm count / ledger |
| **D2** | Baseline statistic: **median** vs mean/EWMA | **Median** (lookback contains the name's own spikes; mean self-biases V-A) | signal def |
| **D3** | Baseline lookback **N=20** | **20** (inherits the frozen ATR-20 horizon; ~1-month ADV; no new constant) | signal def |
| **D4** | Null seed: **inherit 20260711** vs fresh | **Inherit** (reproducibility consistency; null is selection-only) | none (determinism) |
| **D5** | Pessimistic spread **18 bps** (fixed, uniform) | **18** (AR-median magnitude; NOT per-name AR; NOT outcome-informed) | cost floor |
| **D6** | Ledger **cumulative** vs standalone-6 | **Cumulative** (Inviolable Rule 4; roadmap capstone: effective-N prices independence; raises DSR bar; honest) | DSR deflation |
| **D7** | Survivorship **inverted → Phase-1 KILL not conclusive** | **Adopt** (candidate #1's subsidy does not transfer; cand-#2 is penalized) | verdict trust |
| **D8** | Momentum-proxy / gap-re-skin **hard pre-run gate** (both band sets, §10.1) | **Adopt & pin** — V uses close-vs-open (a price measure), so it must *prove* it is not price/gap in disguise before its independence (and D6's clustering) is trusted | independence / D6 |

---

## 15. Provenance & build plan (operator-sequenced 2026-07-12)

### 15.1 The freeze commit (now — pins the spec, ahead of any run)
- This document (decisions resolved, banner FROZEN) **+** `docs/END_GOAL_AND_ROADMAP.md`
  (the record-only backlog housing the candidate-#2 pre-commitment) — committed together.
- **Tag `candidate-2-preregistration`** on the freeze commit. `gate-3` is cut first, onto
  `2ccbb64` (the corrected, final KILL), with the supersession of `ddbe621` noted in the tag.
- No code/config changes in this commit — the pinned values live in §8/§12 as the blind
  provenance; the code is the build (§15.2). Provenance chain: **spec-freeze → build → run**,
  each strictly later.

### 15.2 The build (AFTER the freeze, BEFORE any candidate-#2 run — all fresh-checkout green)
1. **Ledger persistence (R2, hard prerequisite — §9.3).** Regenerate candidate #1's 6 arms
   (seed `20260711`) + the cost-realism re-runs deterministically; **durably persist + commit
   the ledger**; add the **fail-closed teeth test** (gate goes red if a prior candidate's
   streams are missing). Green **before** candidate #2's run.
2. **Cost-swap wiring (§8.2).** `config` fixed spreads (5 / 18 bps) + the `cost_corridor`
   refactor (fixed spread, `impact_coefficient = 0`, no CS) — CI-sensitive, fresh-checkout verified.
3. **Candidate #2 feature/signal code.** V / V-A + the trailing-median-20d baseline, the
   CONTINUATION leg-assignment, the prefix-invariance / train-serve teeth (§4), and the
   cumulative-ledger plumbing (§9) — TOY-stamped, synthetic/teeth-tested; real values already
   fixed by §12.
4. **D8 independence check (§10.1) — runs BEFORE the verdict run**, blind, against the
   pre-committed bands. A 0.5–0.8 rank-corr ⇒ **STOP** and bring to the operator; ≥ 0.8 ⇒
   record the proxy/re-skin finding and revise the independence + D6 accounting first.

**Then, and only then: the single blind candidate-#2 run** — a strictly later commit.
**Until then: run nothing. Freeze line armed. `src/vendored/` pristine. Recorded verdicts untouched.**
