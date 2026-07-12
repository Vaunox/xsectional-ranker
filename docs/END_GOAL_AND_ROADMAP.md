# End Goal & Roadmap — Where This Program Is Going

*Record-only. This document states the **intended destination** so it is not lost, and deliberately **walls it off** from the current build. Nothing here changes the frozen Phase-1 spec (`MASTER_BLUEPRINT.md`) or licenses any classifier work now. It is a roadmap, not a task. Read it to understand the arc; do not build from it until a verdict authorizes it.*

---

## The end goal (the operator's actual mental model)

The intended full system is a **supervised, calibrated probabilistic ranker** in the same family as the operator's existing **IPO Listing-Gains Advisor** (`Vaunox/ipo-advisor`). That system labels past events with real outcomes, fuses several features through a transparent weighted score into a **calibrated probability**, emits a decisive verdict + reason, and **abstains when blind** — with calibration as its sacred, load-bearing gate (no probability shown until predicted-vs-actual tracks and a look-ahead shuffle collapses skill to chance).

Applied to intraday cross-sectional equities, the destination is: a model that fuses several cross-sectional features (gap, gap/ATR, sector-relative gap, overnight volume, prior-day range, market regime, …) into one calibrated **P(stock ends the session up)**, ranks the universe by it, longs the top / shorts the bottom in a market-neutral book, and **abstains on unreadable days**.

## Why we are NOT building that first (the discipline)

For a **ranking** strategy with a **single** strong feature (the overnight gap), a calibrated classifier adds **nothing** over the raw sort — ranking by `P(up)` equals ranking by the gap, because calibration is a monotonic transform that cannot reorder the list. A classifier earns its keep only when it **combines multiple features** into one score.

Therefore, per the IPO advisor's own sacred rule — *never show a probability you haven't earned* — the honest order is:

1. **Prove a raw signal has any life, cheaply, blind, standalone.** A signal that has no cross-sectional edge net of cost on its own does not get to join a fusion model — building feature-engineering + calibration + walk-forward around dead inputs is the expensive-first mistake the advisor's architecture explicitly warns against.
2. **Assemble a small stable of individually-vetted signals.**
3. **Only then build the classifier** — fusing signals each already shown to have life.

## The destination is signal-agnostic (a KILL retires the signal, not the program)

**Important reframe.** The end-goal system does **not** depend on the overnight-gap signal surviving. It depends on having *a stable of cross-sectional signals worth fusing*. So a trustworthy KILL of the gap signal means **"cross that candidate off and go source more,"** not "abandon the destination." The gap is simply **candidate #1** — tested first because it is the strongest a-priori and the cheapest to check.

So the real precursor question is not "does the gap signal alone survive," but: **can we assemble a small set of cross-sectional signals, each with at least a little *independent* edge, worth fusing?**

## The staged arc

| Stage | What | Authorized by |
|---|---|---|
| **Phase 1 — Upper-Bound Smoke Test** | blind gap-sort (A / A-Z) beats random on the survivor cache? | now (frozen spec) |
| **Phase 2 — Point-in-Time Crucible** | blind gap-sort beats random on the clean point-in-time mid-cap universe? | a Phase-1 pass |
| **Candidate search** *(if gap dies, or in parallel)* | source **more** candidate cross-sectional signals; blind-test each **standalone**, one at a time; each earns its place only by showing independent edge on its own | a gap KILL, or operator direction |
| **Phase 3 — The Calibrated Classifier** *(the end goal)* | IPO-advisor-style multi-feature, walk-forward, calibrated, abstaining ranker, fusing the vetted stable | **a stable of ≥N individually-vetted signals — not before** |

A trustworthy KILL at Phase 1/2 retires the **gap signal**; the program continues by sourcing new candidates. The program only truly ends if repeated, honestly-tested candidates all die — at which point the honest conclusion is "no cross-sectional intraday edge is assemblable on this universe with this data," which is itself a valid, valuable result.

## The feature-zoo guardrail (the trap on this exact path)

"Go find more strategies to feed the classifier" is **one step from the feature-zoo overfitting trap.** The discipline that prevents it:

- **Every candidate signal is blind-tested standalone first**, on the same cheap smoke test, and must show *some* independent edge on its own **before** it is allowed into the fusion model. No signal enters on a hunch.
- **A small number of individually-vetted signals, not a large pile of weak ones.** You do not collect 30 features and let a model sort them out — that overfits and the DSR/PBO gate correctly kills it.
- **The IPO advisor already embodies this:** GMP was *removed* because it failed its calibration gate, despite "feeling" predictive. Same rule here — a signal joins the stable only by earning it alone, and stays only if it measurably helps on held-out data.

## What transfers from the IPO advisor (if Phase 3 is ever authorized)

- The **supervised, walk-forward** discipline (as-of feature snapshots; calibrator fit on held-out folds).
- The **abstention** path (`INSUFFICIENT_SIGNAL` → drop unreadable days).
- The **transparent weighted score → calibrator** shape (every reason traceable to a feature value).
- The **feature-gate discipline** (a feature stays only if it measurably improves the metric on held-out data — cf. GMP being *removed* from the advisor for failing its calibration gate).

## One honest caveat (do not over-import the advisor)

For a **market-neutral ranker** you act on relative **rank**, not an absolute probability threshold — so *calibration itself* (the advisor's centre of gravity, its per-IPO APPLY/SKIP cutoff) is **secondary** here. What the intraday system actually needs is **rank-ordering skill**. Calibration re-enters usefully for **day-abstention** (no name's P far from 0.5 → drop the day) and **confidence sizing** — real value, but a means, not the end. Phase 3, if reached, is scored on rank-ordering skill first, calibration second.

---

# The Candidate / Feature Backlog

*Every information source, its role, its build cost, and its queue position. This is the queue of candidates to test **one at a time**, not a pile to feed a model. Added to the record so the plan survives outside the chat.*

## The hard architectural constraint (decides what can ever be a feature)

The end-goal classifier **decides once, in the morning (~09:30)**: it reads each stock, outputs P(stock ends the session up), ranks, places a market-neutral book, and holds. Therefore:

- **Every feature must be computable at ~09:30 from morning + overnight information.** A "midday signal" or "close signal" that must *observe* afternoon action before firing **cannot be a feature** — that is future data at decision time.
- **Diversity comes from *what morning information each feature reads*** (gap / flow / volatility / sector / positioning), **not from time-of-day.** Time-of-day specialization is architecturally incompatible with a single morning decision.
- **The exit horizon *is* a morning-decided output.** The model may decide at 09:30 to exit a position at noon rather than at close. This is where the operator's exit-timing hypothesis legitimately lives — as a morning-decided parameter, not a midday observation.

## The bar for a feature (NOT the bar for a standalone strategy)

A candidate's job is **not** to be a deployable strategy alone. It is to carry a **real, independent** edge worth fusing. **Small is fine — that is the entire design.** The bar is:

1. **Real** — survives the honest null (beats random) *and* the absolute-net-return gate.
2. **Independent** — reads a genuinely different morning information source; not the same bet in disguise (a correlated feature adds nothing to a fusion and collapses effective-N).

**But note the cost truth (learned from candidate #1):** fusion stacks *edge*, it does **not** lower the *cost floor*. Every trade pays ~9 bps statutory fees + spread regardless of how many features agree. So the **fused** result must clear ~15–20 bps all-in — which is only achievable if the stacked features are genuinely uncorrelated. Independence is therefore not a nicety; it is the mechanism by which the ensemble clears cost.

## The backlog

| # | Candidate | Morning info read | Role | Data | Build cost | Status |
|---|---|---|---|---|---|---|
| 1 | **Overnight gap reversal** (A / A-Z) | overnight gap (price) | standalone feature | OHLCV ✓ | cheap | **RETIRED.** Real but tiny gross edge (~10 bps/day, z-scored beats random) — dead on cost (gross ≈ the ~9 bps fee floor) and survivorship-inflated. Rejected as a feature: too small *and* not independent enough to earn a seat. |
| 2 | **Volume-delta / abnormal participation** | 09:15→entry order-flow asymmetry (up-bar vs down-bar volume), vs trailing per-name baseline | standalone feature | OHLCV ✓ | cheap | **NEXT.** Mechanically orthogonal to price-gap selection (flow, not price) — the independence the ensemble needs. Direction pre-registered **continuation** (TWAP/VWAP-slicing persistence), *not* signed by an opening price move (that would smuggle in dead momentum). |
| 3 | **Sector-relative** | stock's morning move relative to its sector index | standalone feature | Kite sector indices ✓ (free) | cheap | Queued. *Caution:* the **strength/momentum** form has no intraday-accrual story (momentum accrues overnight) — if tested, it must be the **intraday sector-relative reversal** form (sector-spread arbitrage closes in-session), or it is disqualified a-priori. |
| 4 | **Realized-volatility / range** | overnight + morning volatility, prior-day range | standalone feature *or* regime conditioner | OHLCV ✓ | cheap | Queued. Predecessor found a vol filter "helps directionally, rescues nothing" — so likely stronger as a **conditioner** than a ranking feature. |
| 5 | **Options positioning (OI)** | prior-day close OI: put-call ratio, OI-change-vs-price quadrant, max-pain / dealer-gamma sign | standalone feature | **Kite provides OI** ("OHLCV +OI where applicable") ✓ | **expensive** (per-contract chain aggregation, expiry rolls, point-in-time strike listings) | Queued — **the strongest orthogonality candidate** (positioning, not price — genuinely new information axis). Deferred until the cheap OHLCV candidates are exhausted, because the build cost is only justified if the cheap stable shows life. *Caution:* effect is **expiry-concentrated**, so it likely needs days-to-expiry conditioning, which fragments an already-limited sample. |
| 6 | **Nifty / index + India VIX** | market-wide morning gap, index level, VIX | **REGIME CONDITIONER — not a ranking feature** | Kite ✓ | cheap | Queued for the **classifier stage**. In a market-neutral book the market cancels, so index direction is not a per-stock ranking input. Its role is **day-level**: how much to trust the signals today, and **when to abstain** (the IPO advisor's `INSUFFICIENT_SIGNAL` path). |
| 7 | ~~Order-flow imbalance / depth (OFI, L2)~~ | — | — | **NOT AVAILABLE** | — | **PERMANENTLY DATA-GATED.** `MASTER_BLUEPRINT.md`: no live 5-level depth (live-stream product, not historical) → OFI / depth-imbalance features are **out of scope** for this program. Recorded as data-gated, never faked. |

**Queue order (cheap-first, by design):** #2 volume-delta → #3 sector-relative (reversal form) → #4 volatility → **then** #5 options/OI if the cheap stable has *any* life. #6 enters at the classifier stage as a conditioner. #7 is closed.

**Rationale for cheap-first:** if the cheap OHLCV-derivable candidates *all* die, that is a strong, cheap signal that no assemblable edge exists here — and you learn it *before* paying for options-chain engineering.

## Capstone constraints inherited from the predecessor (`POST_PROJECT_DIRECTIONS.md` §2)

These bind the eventual ensemble/classifier and are recorded here so they are not rediscovered late:

- **Components may be weak — decisiveness is demanded at the *ensemble*, not the component.** Killing every slightly-positive component individually **destroys the building blocks the ensemble is made of.** (This is the formal statement of "we are hunting small edges to feed the engine.")
- **Independence is earned and measured, never assumed.** √N diversification is proportional to *actual* uncorrelatedness. Genuine independence comes from **structurally distinct edge sources that fail at different times** — not variants of the same bet. The effective-N machinery prices this: fake diversification collapses effective-N and is killed.
- **1/N equal weighting for the gate test.** Zero allocation parameters. **Mean-variance/Markowitz is banned as the gate allocator** (error-maximizer that exploits lucky in-sample non-correlation). Inverse-vol parity is a *deferred refinement, never a rescue* — if the ensemble only lives under vol-parity, be suspicious.
- **Pre-committed membership.** Every edge meeting the blind inclusion criterion goes in; **you may not drop members to flatter the aggregate** — that is selection overfitting migrating from weights to membership.
- **Effective-N-penalized DSR at the aggregate.** Genuine diversification clears the bar; fake diversification is killed.
- **The through-line:** if a blindly equal-weighted ensemble of structurally-distinct edges with pre-committed membership cannot decisively clear the effective-N-penalized gate, **the edges are too weak or too correlated — and it dies.** No reweighting, no membership-pruning, no vol-parity lifeline.

## Open threads (carried, not lost)

- **Exit-timing hypothesis (operator's, pre-registered).** Holding to EOD square-off may not synergize with a fast-reversal signal; the edge may be front-loaded and given back by close. **Moot for candidate #1** (its ~10 bps gross edge is eaten by the ~9 bps fee floor — below the level exit timing could move). **Carried forward:** live again for any future candidate whose edge is marginal on *spread/timing* rather than crushed by fees. Its architectural home is the **morning-decided exit horizon** (see the hard constraint above).
- **Point-in-time universe (Phase-2 crucible data).** Constituent-history replay + delisted/suspended backfill + real ASM/GSM status. Not yet built; required before *any* true PASS on *any* candidate.
- **Broader / less-efficient universe** (NIFTY 200/500, thinner-name cost). The predecessor's "highest-value next experiment" — isolates *is the null the strategy, or the universe?* Caution: the illiquidity that creates the edge endangers the execution; the backtest is **least reliable exactly where the edge looks best.**

---

## Standing rule

Until a stable of individually-vetted signals exists, this document is **record-only**. It must not influence any blind pre-registration, leak features into a construction, or be treated as a licensed task. The current build is the candidate search (candidate #1 retired; #2 next); the classifier waits behind a stable of signals each earned standalone. A KILL retires a signal and sends us to source the next candidate — it does not license skipping the blind, standalone test for any of them.
