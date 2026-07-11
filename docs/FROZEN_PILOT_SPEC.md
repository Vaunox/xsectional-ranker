# Definitive Blueprint — Cross-Sectional Intraday Long-Short Ranker

## Phase 1 Frozen Pre-Registration Spec

*A separate, exploratory research program grown out of the intraday single-factor/multi-factor null. Same honest-null ethos, same pre-registration discipline, same validation harness — new architecture (cross-sectional, market-neutral) and new information axis. This is the frozen spec Claude Code builds the pilot branch against. It supersedes the earlier draft blueprint and decision log, which are subsumed here. Nothing in this document touches the main program's `main` or its Phase-5 synthesis.*

**Status:** Pre-registration frozen after a full adversarial murder board (Appendix A). Parameters below are committed blind and a-priori. Everything is exploration-grade until Phase 2.

---

## 1. Thesis & motivation

**Thesis.** Rank a tradeable, less-efficient NSE universe each day by predicted *entry-to-close* direction; go long the top-k gap-downs and short the top-k gap-ups in a risk-parity, execution-aware, dollar-neutral book; hold intraday; square off at close. **The entire research question: does the ranker beat a random long-k/short-k selection that endures the identical execution model, net of cost?**

**Why, off the null.** The main program produced a clean null — no classic intraday price-pattern strategy survives cost on efficient large-caps, because the gross per-trade move (~0.13%) sits below the fixed round-trip cost (~0.18%), and the edge is competed away on the most-arbitraged names. This pilot attacks that on three axes it never tested: relative-value (strips the market, isolates cross-sectional signal); a less-efficient universe (larger gross dispersion vs cost); and an intraday-*accruing* cross-sectional effect (edge earned in the session we hold).

---

## 2. The signal filter: intraday vs overnight accrual

Many cross-sectional effects earn their returns *entirely overnight* or *entirely intraday* (the "tug of war"). Because this system holds **entry-to-close only**, any overnight-accruing signal is useless regardless of strength. This disqualifies the two obvious candidates:

- **Cross-sectional momentum** — accrues overnight. RULED OUT.
- **Classic multi-day short-term reversal** — accrues overnight; cost-eaten; concentrated in illiquid names; in India appears only among the most illiquid and does not persist. RULED OUT.

What survives is **intraday-accruing overreaction-reversal** — the source of Signal A.

---

## 3. Signals (blind, a-priori, mechanism-first)

Two pre-registered signal arms, both testing the same mechanism (overnight overreaction corrected intraday), differing only in whether the overreaction is measured raw or volatility-normalized:

- **Signal A — raw gap.** Rank by `(Open − PriorClose) / PriorClose`. **Short the largest gap-ups, long the largest gap-downs.** Hold to close.
- **Signal A-Z — volatility-adjusted gap.** Rank by `raw_gap / ATR(20)`. Guarantees the top-k/bottom-k are the names in the most statistically violent overreaction *relative to their own normal* — the honest test of the "magnitude/anomaly" hypothesis, placed in the **alpha logic**, not the sizing logic.

**Mechanism (a-priori, both arms).** Overnight returns reverse intraday: retail/noise-trader buying concentrates and overshoots at the open; daytime arbitrageurs correct it over the session. The reversal accrues in the held session. India evidence is unusually strong (pronounced overnight-up / intraday-down asymmetry). Signal A is also the market-neutral, cross-sectional evolution of the main program's own least-bad result (the gap pair).

**A vs A-Z is the sign-vs-magnitude test** and costs two trials — both charged to the ledger; DSR deflates accordingly (see §11).

**Parked signals (NOT in Phase 1):** sector-relative gap; residual reversal; options open-interest / gamma / max-pain positioning features; macro-gating. Each earns its own pre-registered study only after the machinery is proven. (Rationale in Appendix A / the superseded decision log.)

---

## 4. Causal spine — entry window & label

- **Combined ranker.** Observe everything through yesterday's close plus today's first N minutes; enter at the window close; exit at close; predict (window-close → close). Yesterday's data is additional features; using both is causal iff entry is at/after the window close.
- **Entry window — FROZEN: 30-min default (enter ~09:45), swept `{15, 30, 45}`.** First ~15 min is noisiest (news/pre-market flush, widest mid-cap spreads); 30 balances a settled signal against move-left-to-trade; the sweep lets the gate adjudicate, not the prior. Every window counts against the ledger.
- **Label defined FROM the entry instant** (e.g. 09:45→close), not from the open. Each window is a distinct label/spec.
- **Causal feature cutoff is a HARD PRECONDITION.** Every feature computable strictly before entry; prefix-invariance test load-bearing (the morning window is where look-ahead hides). **Scope limit (pre-declared):** the sweep cannot test sub-15-min entry because spread/impact there is prohibitive, so if the *entire* edge lives in the first ~10 min it is untradeable and will read as a null — a valid honest finding ("edge exists only where you can't trade it"), not a design flaw.

---

## 5. Universe & the point-in-time problem

- **Character.** Less-efficient (mid-cap), tradeable, shortable — not the large-caps already killed.
- **Eligibility filters.** EQ series only (no BE / Trade-to-Trade); not under ASM/GSM surveillance; minimum median daily traded value (a hard **liquidity floor** — never rank a name you cannot exit); F&O membership (shortability + liquidity + robustness screen).
- **Point-in-time membership is the load-bearing data problem.** The universe on each historical day must be reconstructed *as known that morning*, **including names that later delisted/merged/were suspended** — the random hat on a 2017 Tuesday must be able to draw a stock that later went to zero, because a trader that morning could have. Ranking on today's survivors over history is a fatal, symmetric contamination (see §12 and Appendix A: the survivorship sign-flip).
- **Dual eligibility masks (asymmetric constraints).** Short-bans are asymmetric — a name in Trade-to-Trade (Series BE/BZ) or elevated ASM/GSM can be legally un-shortable intraday yet perfectly valid as a 100%-cash long. Eligibility is therefore **two point-in-time masks, not one**: `long_eligible` and `short_eligible`. The ranker draws shorts (top-k gap-ups) strictly from `short_eligible` and longs (bottom-k gap-downs) strictly from `long_eligible`. Filter: `EQ`-series only (from daily Bhavcopy) and non-ASM/non-GSM for short-eligibility; where clean historical ASM/GSM lists are unavailable, **proxy via that day's margin/leverage** (100% margin / 1× leverage ⇒ short-ineligible). **Phase-1 honesty stamp:** architecturally complete but **empirically unexercised in Phase 1** — large-cap survivors do not go T2T/GSM, so this filter logs a ~0% fire-rate here; it is a load-bearing gate that only goes live in the Phase-2 mid-cap crucible. The ~0% Phase-1 fire-rate is the expected signature, logged and checkable.
- **Ex-ante sector cap (mechanism enforcement, not just risk).** No leg may hold more than ⌈k/2⌉ names from a single NSE sector; if the raw top-k/bottom-k violates it, the ranker skips to the next eligible name. Justification: a *clustered* sector gap (e.g. four PSU banks down 4% on an RBI surprise) is **by the signal's own economics not idiosyncratic** — it is macro repricing that institutional flow trends all day, so fading it violates the core hypothesis. The cap forces the ranker to hunt isolated stock-specific overreactions rather than step in front of directional sector flow. Requires a static sector-mapping file (cheap; point-in-time easy — a classification map, not a price series) on Day 1. A post-hoc sector-concentration flag remains as a *secondary* check (§11), not the primary defense.

---

## 6. Data layer — Kite-first, free-until-earned

- **Source: Zerodha Kite** (integrated via `kite_adapter.py`; cleaner than free feeds for NSE — avoids dirty opens, retroactive-adjustment leakage, patchy intraday, timezone slips, all of which would poison a gap signal).
- **Phase 1 runs on the existing survivor-only cache** (49 large-caps, 5-min, 2015→2026) — sufficient for the Upper-Bound Smoke Test (§12), which is *designed* to exploit the survivor bias rather than be defeated by it.
- **GATE ZERO — data-integrity validation** before trusting any number: spot-check opens, split/dividend adjustments, corporate actions; verify tradability state. A cross-sectional edge on dirty gaps is worthless and the failure is invisible unless checked. Hooks: `corp_actions.py`, `survivorship.py`, `quality.py`.
- **Buy nothing until earned.** Paid tiers (Kite CDS/MCX; global-macro API; Level-2) are gated on the cost-corridor outcome (§9) and the phase sequencing (§12).

---

## 7. Sizing — inverse-vol / risk-parity (mandatory hygiene)

- **Each name sized to contribute equal risk within its leg** (inverse-vol / inverse-ATR). This is **not a swept parameter** — it is required hygiene for a cross-sectional ranker. Equal-*dollar* weighting is structurally wrong here: it hands the P&L to the highest-variance name and measures idiosyncratic noise, not ranking skill (Appendix A: risk-parity/alpha separation). Gap *magnitude* and asset *volatility* are distinct; the magnitude hypothesis is tested in the signal (A vs A-Z), not the weights.

---

## 8. Execution model — Execution-Aware Dollar Neutrality

Neutrality is enforced at construction through truncation, because both unhedged imbalance and construction-time beta-neutrality fail on execution reality (Appendix A: the beta-attribution reversal & the truncation reversal).

0. **Eligibility resolves before ranking, in this order:** apply the point-in-time `long_eligible` / `short_eligible` dual masks (§5); apply the circuit-lock filter (below); rank each leg only within its mask; then apply the ex-ante ⌈k/2⌉ sector cap per leg (§5), skipping to the next eligible name on violation. Only then do sizing/truncation (steps 2–5) run.
1. **Circuit-lock / untradeable eligibility filter (applied before ranking).** Drop any name that, at the entry instant, has near-zero range *relative to its own recent intraday range* (catches full and intermittent locks) OR sits within tolerance of a plausible price band with abnormally low time-of-day volume. **Conservative — when in doubt, drop:** a dropped tradeable name costs a little breadth; a kept locked name fabricates alpha (ghost fill). Flagged-fraction logged as a diagnostic.
2. **Cap each name** at the pessimistic participation rule (≤ 1% of the entry-window volume — a frozen parameter).
3. **Sum the max permitted dollar fill per leg**; the **smaller leg sets gross exposure**.
4. **Scale the larger leg down pro-rata** so every name keeps its intended relative (risk-parity) weight and the legs match in dollars. **k stays fixed; never drop names to rebalance** (dropping names floats k, injects conditional volatility, and — critically — breaks the random-null comparison; Appendix A).
5. **Gross-exposure floor → drop the day.** If the pro-rata scale-down forces book gross below a pre-registered dollar floor (liquidity too thin to field a diversified neutral book), the day is **untradeable and dropped from the sample**. Day-drop fraction logged as the market-thinness diagnostic.

---

## 9. Cost as a corridor (and the Level-2 purchase trigger)

OHLCV cannot *measure* market impact (volume ≠ book depth). So cost is **bounded, not point-estimated** — every study runs twice:

- **Optimistic bound:** raw Corwin-Schultz (cross-checked Abdi-Ranaldo) implied spread; assume full fill.
- **Pessimistic bound:** ~3× the implied spread and the ≤1%-volume cap with partial fills eating maximum slippage.

**Decision matrix (also the data-spend trigger):**
- **Dies in the optimistic bound** → dead; walk away; **do not buy L2**.
- **Survives the pessimistic bound** → robust; L2 is a later optimization, not a prerequisite.
- **Survives optimistic, dies pessimistic** → viability lives in the depth you can't see; **this is the sole trigger to authorize the L2 spend.**

A verdict counts only if it is robust across the corridor. The participation cap and spread multiplier are pre-registered (frozen), never swept to conjure a fill rate that flatters the edge.

---

## 10. The null — the Global Null Panel

- **Benchmark is a random long-k/short-k draw enduring the IDENTICAL execution model** — same universe/day (already eligibility-filtered), same spread corridor, same 1%-volume caps, same fixed-k pro-rata truncation, same gross floor. Only the *selection* differs: ranked vs random. This isolates the one variable under test — selection skill — and nulls out liquidity-selection effects (an asymmetric cost treatment would measure "does the signal sit in more-fillable names," not skill).
- **A distribution, not a single draw:** N random books per day (fixed, logged seed → reproducible, versioned artifact). The signal must beat a real percentile of that distribution, feeding DSR/percentile logic honestly.
- **Global Null Panel construction:** generate N draws per day across all 11 years **once**, push through the identical pessimistic execution model **once** → an immutable per-day null distribution. The signal's CPCV path dictates surviving days; the panel is **sliced** to match. The null is **not purged/embargoed** — a random draw has zero parameters and cannot learn, so it cannot leak; redrawing it inside each CPCV path is statistically identical compute-burn. This collapses O(days×draws×paths) → O(days×draws) and makes the shared day-drop fall out mechanically (the signal dictates day-drops; the panel is masked to them).

---

## 11. The gate — reuse the harness, change only the benchmark

- **Reuse the validated machinery UNCHANGED** — CPCV path distribution, DSR (deflated by the ledger's effective-N), PBO, breadth across days, the strict decisive bar, exploration-grade stamping, held-out reserved for confirming a positive only.
- **Add the random-percentile bar as a new layer; never edit the validated code.** The crown jewels stay frozen; the different benchmark bolts on top.
- **DSR deflation counts every arm:** 2 signals (A, A-Z) × window sweep `{15,30,45}` = the full trial set; the deflated bar rises for every swing taken. No reporting the winning arm as if it were the only test.
- **Logged diagnostics (not gates):** market-day conditioning (split P&L by index intraday direction — a residual-tilt tell; note OLS attribution averages out *conditional* tail-beta, so this is a diagnostic, not the neutrality mechanism); **post-hoc sector-concentration** (flag P&L on days a leg was sector-clustered — secondary check behind the ex-ante cap); circuit-flag fraction; **short-ban fire-rate** (expected ~0% in Phase 1); day-drop fraction; effective-N per checkpoint.

---

## 12. Phased validation & verdict matrix

**Phase 1 — Upper-Bound Smoke Test (execute now).**
- Data: existing survivor-only Kite cache.
- Full execution model, Global Null Panel, both cost bounds.
- **The survivor bias SUBSIDIZES this signal.** Signal A/A-Z goes *long the biggest gap-downs* — exactly the profile of a mid-cap dying on an overnight disclosure. Survivor-only silently deletes those catastrophic long trades, so long-leg performance is artificially *inflated* — a padded room where the worst realities are nerfed.
- **Verdict matrix:**
  - **KILL** → **hyper-trustworthy.** A strategy that can't beat random even while secretly subsidized by survivorship is annihilated in reality. Walk away for the cost of a branch.
  - **PASS** → **provisional / untrustworthy.** Earns *only* the right to trigger Phase 2. Never greenlights production.

**Phase 2 — Point-in-Time Crucible (triggered only by a Phase 1 pass).**
- Data acquisition: reconstruct index constituent history (replay NSE reconstitution change-lists backward from a known membership) + acquire delisted/suspended OHLCV + per-day tradability state. This is the real, one-time, load-bearing data project — and the most likely (justified) spend.
- Rerun Phase 1 identically on the clean point-in-time universe.
- **The only gate authorized to issue a true PASS and greenlight a production repo.**

---

## 13. Branch, fork & sequencing

- **Now:** branch `feature/cross-sectional-ranker` off the current repo; reuse the harness in place; wall off from `main`; **do not merge pilot code into `main`.**
- **Later:** a fresh standalone repo *only if Phase 2 earns it* — seeded from (imported) the validated harness, **not** a GitHub fork.
- **Sequencing:** independent of the main program's Phase-5 synthesis (which proceeds on `main`). Parked directions come later, each pre-registered.

---

## 14. Failure modes guarded (this design specifically)

1. **Look-ahead in the morning window** — prefix-invariance is load-bearing.
2. **Beating random by luck** (~250 obs/yr) — the N-draw null distribution + DSR deflation prices it.
3. **Survivorship / point-in-time** — Phase 2 crucible; Phase 1 stamped upper-bound.
4. **Ghost fills (circuit locks)** — conservative over-drop eligibility filter.
5. **Liquidity-selection masquerading as alpha** — symmetric execution on signal and null.
6. **Conditional tail-beta from imbalance** — Execution-Aware Dollar Neutrality (truncation), not unhedged imbalance, not fragile construction-time beta-neutrality.
7. **Variance dominance** — risk-parity sizing; magnitude tested in signal (A-Z), not weights.
8. **Feature-zoo overfitting** — two mechanism arms only; no model handed a feature pile.
9. **Sector-repricing ghost** — a clustered sector gap is macro flow, not idiosyncratic overreaction; ex-ante ⌈k/2⌉ sector cap enforces the mechanism (+ post-hoc flag).
10. **Simulated un-shortable shorts** — dual `long_eligible`/`short_eligible` masks (EQ-only, non-ASM/GSM, margin-proxy); load-bearing in Phase 2, stamped unexercised in Phase 1.

---

## 15. Frozen parameter ledger (pre-registered, blind)

| Parameter | Frozen value | Swept? | Charged to ledger |
|---|---|---|---|
| Signal arms | A (raw gap), A-Z (gap/ATR-20) | — (both run) | Yes (2) |
| Entry window | 30 min default | `{15, 30, 45}` | Yes |
| k (names per leg) | fixed (e.g. 5) | No | — |
| Leg sizing | inverse-vol / risk-parity | No (hygiene) | — |
| Neutrality | Execution-Aware Dollar Neutrality (truncation) | No | — |
| Participation cap (pessimistic) | ≤ 1% entry-window volume | No | — |
| Spread model | Corwin-Schultz (× Abdi-Ranaldo check) | No | — |
| Pessimistic spread multiplier | ~3× | No | — |
| Gross-exposure floor | pre-registered ₹ threshold | No | — |
| Null draws per day (N) | fixed, seeded | No | — |
| Cost runs | optimistic + pessimistic bounds | Both | — |
| Sector cap per leg | ⌈k/2⌉ from one NSE sector | No | — |
| Eligibility masks | dual: `long_eligible` / `short_eligible` (EQ-only, non-ASM/GSM, margin-proxy) | No | — |

*k, the gross floor, N, and the exact liquidity floor are frozen at implementation and recorded here before the first run.*

---

## 16. Discipline carried from the main program (unchanged)

Pre-registration before any run; params blind, a-priori, mechanism-first; nothing from the main program's observed sub-patterns may leak into a construction (stop-and-flag, don't import); every parameter charged to the ledger with automatic DSR deflation; STOP-and-flag on any PASS / near-threshold / INSUFFICIENT / contradiction; operator sign-off gate is real; all results exploration-grade until the Phase-2 crucible; doc-grounded rulings over verbal summaries.

---
---

# Appendix A — The Murder Board (frozen audit trail)

*Non-negotiable for an institutional-grade program. This records not just the spec but the adversarial process that hardened it — every challenge, every position held, and every concession — so future maintainers cannot re-litigate settled calls or unknowingly re-introduce a purged ghost. When a system is this lean, the* why *is what keeps the* how *from drifting.*

The pilot design was subjected to an adversarial review. The exchanges below are recorded as challenge → position → resolution. Five reversals materially changed the spec; they are flagged **[CONCESSION]**.

### Round 1 — Beta, cost, entry window, benchmark purity

- **Entry-window decay.** Challenge: gap-fade alpha decays in the first ~10–15 min, so a 09:45 entry may harvest only the tail. Resolution: kept the swept window (the {15} arm tests exactly this); added the pre-declared **scope limit** — if the edge lives only sub-15-min, it is untradeable and reads as a null, which is a valid finding, not a flaw.
- **Market impact vs implied spread.** Challenge: Corwin-Schultz estimates spread width, not book depth; mid-cap books are hollow. Resolution: **[CONCESSION]** — replaced the (incoherent) "depth-aware impact model" with the **cost corridor** (§9). See Round 2 for why OHLCV can't measure impact at all.
- **Benchmark purity.** Challenge: a hat-draw random baseline is too loose (measures "volatile names differ," not skill); proposed a fully characteristic-matched baseline. Resolution: rejected the *single matched* baseline (it can subtract the alpha itself) in favor of a **ladder** — hat-draw ("anything here?") then characteristic-matched ("skill beyond risk loadings?"). Later superseded by the symmetric-execution null (Round 3), which achieves the same purity by construction.
- **Beta tilt.** Challenge: ranking by gap size is not beta-orthogonal; a dollar-neutral book carries a hidden beta tilt that spikes on tail days. Resolution: **[CONCESSION #1 — the beta-attribution reversal]** — see Round 2.

### Round 2 — The beta-attribution reversal & the truncation reversal

- **[CONCESSION #1 — beta-attribution reversal].** My proposed defense (measure the tilt post-hoc via a single full-sample OLS regression) was shown insufficient: the liquidity constraint is *positively correlated with the signal* and bites on tail days, so the book goes violently net-long exactly when the market rips. A full-sample OLS averages out this **conditional tail-beta** and mislabels the tail windfall as alpha. Post-hoc attribution cannot see what it averages away. Beta-attribution demoted to a *logged diagnostic* (§11), not the neutrality mechanism.
- **Beta-neutral construction also rejected as the fix.** A β=0 book at the instant of intent becomes β-positive the moment the highest-beta short partial-fills — construction-time neutrality is a fiction execution can't honor.
- **[CONCESSION #2 — the truncation reversal].** I had labeled "scale the book to the smaller leg" as *dishonest survivorship-by-liquidity*. Corrected: **survivorship-by-liquidity is the empirical truth of a market-neutral mandate.** If the edge needs a ₹100 long paired against a ₹10 short you couldn't source, it was never a market-neutral edge. Adopted **Execution-Aware Dollar Neutrality** (§8): truncate the larger leg pro-rata to the smaller; the pessimistic run then asks the right question — does the ranker beat random *on the lowest common denominator of available liquidity?*

### Round 3 — Fixed-k, and the symmetric null

- **Rank-preserving vs pro-rata truncation.** I initially favored rank-preserving truncation (drop lowest-conviction names, keep a k-floor). Resolution: **[CONCESSION #3 — fixed-k]** — rank-preserving *floats k*, which (a) **corrupts the random null** (the baseline would have to float its own k to stay apples-to-apples — a nightmare), and (b) force-concentrates risk on illiquid days. Corrected to **fixed-k equal-weight, pro-rata scaling** (conviction is binary bucket inclusion, so pro-rata preserves relative concentration; only gross leverage shrinks). Below a **gross floor → drop the day**, not names.
- **Null must endure identical execution.** Established: the random baseline passes through the *same* caps, spreads, truncation, and day-drops as the signal — only selection differs — else "beats random" measures liquidity-selection, not skill (and, because the signal selects the *least*-liquid names, asymmetry would bias toward a false negative). Null is an N-draw distribution, not a single draw.

### Round 4 — CPCV collision (over-paranoia corrected)

- **[Correction — not a concession to a flaw, a correction of over-paranoia].** I argued the null must be redrawn inside every CPCV path for symmetry. Corrected: **a memoryless process cannot leak** — a random draw has zero parameters and learns nothing, so purge/embargo is irrelevant to it. Adopted the **Global Null Panel**: generate + cost-model all random draws once across 11 years, then *slice* to the signal's surviving days. Collapses compute O(days×draws×paths)→O(days×draws) and makes shared day-drops mechanical. Principle recorded: **purge what can learn; a null that can't learn doesn't need purging.** (Added: fixed logged seed → reproducible, versioned null artifact.)

### Round 5 — The survivorship sign-flip & the weighting/alpha separation

- **[CONCESSION #4 — the survivorship sign-flip].** I claimed survivor-only *understates* profit (delisted names cratered → you'd have shorted them). Wrong for *this* signal: **Signal A goes LONG the gap-downs.** Dying mid-caps gap *down*, so the ranker *buys* them — and survivor-only deletes exactly those catastrophic longs, **inflating** long-leg performance. This inverts the smoke-test logic in our favor: a survivor-only **KILL is hyper-trustworthy** (the strategy failed even while subsidized), a **PASS is meaningless** (padded room). This *decided the phased sequencing* (§12) — run the subsidized test first; a KILL ends it for free.
- **[CONCESSION #5 — risk-parity / alpha separation].** I proposed sweeping equal-dollar vs inverse-vol weighting to test "sign vs magnitude." Corrected: that conflates **gap magnitude with asset volatility** (a 5% gap on a 1.5%-vol utility is apocalyptic; a 5% gap on a 9%-vol biotech is Tuesday). Equal-dollar weighting doesn't test magnitude — it hands the P&L to the loudest stock and measures noise. Resolution: **inverse-vol/risk-parity is mandatory hygiene** (off the ledger); the sign-vs-magnitude hypothesis moves into the **signal** as **A (raw) vs A-Z (gap/ATR)** — testing the hypothesis where it actually lives (alpha logic), not the sizing.

### Round 6 — Implementation-level ghosts (sector clustering & asymmetric short-bans)

- **[CONCESSION #6 — sector cap over flag].** Challenge: on macro mornings the ranker's top-k can be one sector, turning it from an idiosyncratic-overreaction trade into an accidental macro pair trade (fading a sector that institutional flow trends all day). I noted a post-hoc *flag* is only a diagnostic and forces an illegitimate post-hoc sample filter on a pass; I raised the counter that a hard cap might suppress genuine sector-clustered idiosyncratic signal. Resolution: the counter dissolves under the signal's own economics — **a clustered sector gap is by definition not idiosyncratic** (it's macro repricing), so fading it *violates the core hypothesis*. The ex-ante ⌈k/2⌉ sector cap is therefore **mechanism enforcement, not signal suppression**. Adopted as construction rule (needs only a cheap static sector-label map); post-hoc flag demoted to secondary check.
- **[CONCESSION #7 — dual eligibility masks].** Challenge: a name can be liquid and un-locked yet legally un-shortable intraday (T2T Series BE/BZ, elevated ASM/GSM), so a volume+circuit filter simulates broker-rejected shorts. I added that the constraint is **asymmetric** — an un-shortable gap-down is still a valid *long* — so single-flag eligibility mis-models it. Resolution: **two point-in-time masks** (`long_eligible` / `short_eligible`), each leg drawn from its own; EQ-only + non-ASM/GSM with a margin/leverage proxy where historical surveillance lists are unavailable. Honesty stamp: **unexercised in Phase 1** (large-cap survivors don't trip it; expected ~0% fire-rate), a load-bearing gate that goes live only in the Phase-2 mid-cap crucible.

### Standing principles crystallized by the debate

1. Purge what can learn; a memoryless null needs no purging.
2. Survivorship-by-liquidity is the truth of a market-neutral mandate, not a bias to smooth.
3. Enforce neutrality in execution (truncation), not in intent (construction) or after the fact (attribution).
4. Test a hypothesis in the layer where it is a hypothesis — magnitude belongs in the signal, not the weights.
5. The null must suffer everything the signal suffers; symmetry is the only thing that makes "beats random" mean skill.
6. A biased dataset can still yield a trustworthy result if the bias direction is known — a subsidized KILL is bulletproof; a subsidized PASS is worthless.
7. Prevent in construction what you'd otherwise have to filter post-hoc — a post-hoc filter on an outcome-correlated variable is a researcher degree of freedom; an ex-ante cap is not.
8. Model constraints at their true granularity — short-bans are asymmetric, so eligibility is two masks, not one; collapsing them mis-states reality.
9. Build a gate before you can test it, but stamp it unexercised — Phase 1 can't validate the short-ban filter, so it says so rather than pretending coverage.
