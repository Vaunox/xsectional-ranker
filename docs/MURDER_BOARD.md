# The Murder Board — Frozen Adversarial-Review Audit Trail

*Non-negotiable for an institutional-grade program. This records not just the spec but the adversarial process that hardened it — every challenge, every position held, and every concession — so future maintainers cannot re-litigate settled calls or unknowingly re-introduce a purged ghost. When a system is this lean, the* why *is what keeps the* how *from drifting.*

The pilot design was subjected to an adversarial review. The exchanges below are recorded as challenge → position → resolution. Seven reversals materially changed the spec; they are flagged **[CONCESSION]**.

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
