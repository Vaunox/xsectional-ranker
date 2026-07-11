# Cross-Sectional Intraday Long-Short Ranker

*An honest-null research program testing whether a market-neutral, cross-sectional intraday ranker holds a cost-surviving edge on the Indian equity market. A sibling program to `intraday-strategy-lab`, grown out of its clean single-factor/multi-factor null — reusing that program's validated statistical harness as a frozen imported library, with an entirely new architecture (cross-sectional, market-neutral, beat-random) and data layer (point-in-time, mid-cap).*

---

## What this is

The predecessor program tested classic intraday *directional, single-name* strategies and returned a clean null: no classic intraday price-pattern strategy survives cost on efficient large-caps, because the gross per-trade move sits below the fixed round-trip cost, and any edge is competed away on the most-arbitraged names.

This program attacks that null on three axes it never tested:

1. **Relative-value, not directional** — a market-neutral long-short book strips out the market factor and isolates cross-sectional signal.
2. **Less-efficient universe** — mid-caps, where intraday gross dispersion is larger relative to cost.
3. **Intraday-accruing signal** — cross-sectional overnight-gap reversal, the one strong cross-sectional effect that earns its edge in the held (entry-to-close) session.

**The research question is singular:** does the ranker beat a random long-k/short-k selection that endures the identical execution model, net of cost? Everything else is plumbing.

## The honest expectation

Given everything the predecessor program found, the disciplined prior is that this **also** returns a null. The program is built to be able to report that cleanly. A trustworthy KILL is the primary, valuable outcome; a PASS must clear a deliberately hostile, bias-bounded, execution-aware gate before it means anything.

## Two-phase validation (read this before running anything)

- **Phase 1 — Upper-Bound Smoke Test.** Runs on the *survivor-biased* cache inherited from the predecessor. Because the signal goes *long the biggest gap-downs* (the profile of a dying stock), survivor-only data secretly *subsidizes* the long leg. A **KILL here is hyper-trustworthy** (it failed even while subsidized) → walk away. A **PASS is provisional** and earns *only* the right to trigger Phase 2.
- **Phase 2 — Point-in-Time Crucible.** Rebuilds the universe correctly (constituent history + delisted backfill + real ASM/GSM status), reruns identically. The **only** gate authorized to issue a true PASS.

Phase 1 gates Phase 2. Phase 2's expensive data acquisition is pointless if the padded-room test already killed the strategy.

## Repository map

| Path | Purpose |
|---|---|
| `MASTER_BLUEPRINT.md` | Self-contained build & research spec (Parts I–VII). Sufficient to build every phase from. |
| `docs/deep_dives/01_…Data_and_Universe_Layer.md` | Point-in-time universe, dual eligibility masks, sector map, circuit filter, data-integrity gate zero. |
| `docs/deep_dives/02_…Execution_and_Null_Layer.md` | Execution-Aware Dollar Neutrality, risk-parity sizing, cost corridor, Global Null Panel. |
| `docs/deep_dives/03_…Harness_Import_and_Verification.md` | **How imported predecessor code is vendored, frozen, and rigorously re-verified.** Read before importing anything. |
| `docs/deep_dives/04_…Validation_and_Gate_Layer.md` | Beat-random gate, DSR deflation across arms, phased validation. |
| `docs/MURDER_BOARD.md` | Frozen adversarial-review audit trail (7 concessions + standing principles). The *why* welded to the *how*. |
| `docs/PROGRESS.md` | Program log; gate checklist. |
| `docs/RESEARCH_FINDINGS.md` | Living-paper scaffold; filled only by validated runs. |

## Non-negotiable inheritances from the predecessor

- **The kill-gate is sacred** — no tweaking-until-it-passes; every variant charged to the effective-N trial ledger.
- **Point-in-time correctness, always** — decision on bar *t* executes at *t+1*; trailing/expanding normalization only; leakage tests in CI.
- **Costs are always modeled** — no gross-only backtests, ever.
- **Honest cumulative effective-N trial counting** — correlated variants clustered, never a raw count.
- **The imported harness is frozen** — vendored as a versioned library, re-verified against golden masters, and **never edited** (Deep Dive 03).

## Status

Pre-registration frozen (see `MASTER_BLUEPRINT.md` and `docs/MURDER_BOARD.md`). **No code written, no phase executed.** Phase 0 (scaffolding + harness import & verification) is the first build.
