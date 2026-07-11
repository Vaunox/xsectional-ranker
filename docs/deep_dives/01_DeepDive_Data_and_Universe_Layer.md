# Deep Dive 01 — Data & Universe Layer (Layer 1)

*The cross-sectional ranker lives or dies on the integrity of its universe. Every hard-won lesson from the predecessor (point-in-time, no lookahead, no train/serve skew) applies — plus three new, cross-sectional-specific hazards the predecessor never faced.*

## Scope
Kite ingestion, storage, hygiene, the point-in-time universe, the dual eligibility masks, the sector map, the circuit-lock filter, and gate-zero data-integrity validation. Feature primitives reused from the predecessor are imported and verified per Deep Dive 03.

## The silent killers (design out structurally, not by discipline)
1. **Lookahead leakage** — any feature/signal touching data unavailable at the entry instant. Defended by pure point-in-time functions, trailing/expanding normalization, prefix-invariance tests in CI. *New surface:* the morning entry window (09:15→entry) is where leakage hides; the prefix-invariance test is load-bearing, not a formality.
2. **Survivorship bias** — and here it is *worse than usual*. The signal goes **long the biggest gap-downs** — the profile of a dying stock — so survivor-only data deletes exactly the catastrophic long trades and *inflates* long-leg P&L. Defended by point-in-time constituents including delisted/suspended names (Phase 2). In Phase 1 it is deliberately *exploited* (a survivor-only KILL is hyper-trustworthy) and stamped, never trusted for a PASS.
3. **Train/serve skew** — vectorized backfill computing a feature differently from an incremental path. Defended by the dual-path harness (vectorized == bar-by-bar).
4. **Liquidity-selection masquerading as alpha** *(new, cross-sectional)* — if the signal basket sits in more-fillable names than the null, "beats random" measures liquidity, not skill. Defended by symmetric execution on signal and null (Deep Dive 02), not in this layer — but the universe must expose the same eligibility to both.

## Connectivity & storage (Kite historical)
Behind `BrokerAdapter`; ~3 req/s; paginate; intraday depth is bounded — verify available minute-bar depth before committing a date range (it caps CPCV/DSR power). Daily TOTP auth; token in a git-ignored path. Parquet partitioned by symbol/date; immutable raw + derived layers behind `Repository`; corrections are new versions, never mutations.

## Point-in-time universe (the load-bearing data task)
The eligible universe on each historical day is reconstructed **as known that morning**, including names that later delisted, merged, or were suspended — the random hat on a 2017 Tuesday must be able to draw a stock that later went to zero.
- **Phase 1:** the inherited survivor cache (49 large-caps) — a *machinery prototype only*, stamped survivorship-inflated upper bound.
- **Phase 2:** reconstruct mid-cap index constituent history by replaying NSE reconstitution change-lists backward from a known recent membership; backfill delisted/suspended OHLCV (the likely paid/hard-to-source step); model per-day tradability state.

## Dual eligibility masks (asymmetric constraints — a structural upgrade over the predecessor)
Short-bans are asymmetric: a T2T (Series BE/BZ) or elevated-ASM/GSM name may be legally un-shortable intraday yet perfectly valid as a 100%-cash long. Eligibility is therefore **two point-in-time masks**:
- `short_eligible` — EQ-series (from daily Bhavcopy), non-ASM/non-GSM, shortable intraday; where clean historical surveillance lists are unavailable, **proxy** via that day's margin/leverage (100% margin / 1× leverage ⇒ short-ineligible).
- `long_eligible` — listed, EQ-series, tradable long.
The ranker draws shorts strictly from `short_eligible`, longs strictly from `long_eligible`. **Phase-1 honesty stamp:** unexercised on large-cap survivors (expected ~0% fire-rate, logged); load-bearing only in the Phase-2 mid-cap crucible.

## Sector map (for the ex-ante sector cap)
A static point-in-time sector classification (a label map, not a price series — cheap). Feeds the ⌈k/2⌉-per-sector-per-leg cap in Layer 2. Justification is mechanism enforcement: a clustered sector gap is macro repricing, not idiosyncratic overreaction, so fading it violates the signal's core hypothesis.

## Circuit-lock detection (ghost-fill defense)
At the entry instant, flag a name untradeable if: the entry-window bar has near-zero range **relative to the name's own recent intraday range** (catches full *and* intermittent locks), OR price sits within tolerance of a plausible per-symbol band with abnormally low time-of-day volume. **Conservative — when in doubt, drop:** a dropped tradeable name costs a little breadth; a kept locked name fabricates alpha. Flagged fraction logged.

## Hygiene jobs (idempotent, tested, logged)
NSE calendar + IST + session tagging; corporate-action adjustment (store raw *and* adjusted — critical for a clean gap = prior-adjusted-close → open); bad-tick filtering (log every correction); gap detection; the two eligibility masks; the sector map; circuit detection; liquidity floor (min median daily traded value — never rank a name you can't exit).

## GATE ZERO — data-integrity validation (before any signal trusts a number)
Spot-check opens, split/dividend adjustments, and known corporate actions against a second source; verify tradability state; confirm the point-in-time universe reconstructs correctly on sampled historical dates. A cross-sectional edge on dirty gaps is worthless and the failure is invisible unless checked.

## To expand later
- Constituent-history replay procedure and source list.
- Delisted-OHLCV acquisition options and cost.
- Per-symbol circuit-band table (assigned 5/10/20% limits shift with surveillance stage).
