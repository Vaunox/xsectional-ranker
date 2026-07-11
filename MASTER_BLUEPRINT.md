# MASTER BLUEPRINT — Cross-Sectional Intraday Long-Short Ranker
### Build & Research Handoff Document

*A sibling research program to `intraday-strategy-lab`. Same honest-null ethos, same pre-registration discipline, same statistical harness (imported and frozen, never edited). New architecture: cross-sectional, market-neutral, beat-random. This document is self-contained and sufficient to build every phase from; the `docs/deep_dives/` files are optional expanded reference. Frozen after a full adversarial murder board (`docs/MURDER_BOARD.md`).*

---

## HOW TO USE THIS DOCUMENT

- **Part I** — engineering ground rules (inherited verbatim from the predecessor; they bind every change here too).
- **Part II** — system overview & locked decisions (what we build and the decisions frozen by the murder board).
- **Part III** — technical reference by layer (self-contained; build from this).
- **Part IV** — the build program, one phase per session.
- **Part V** — the signal & parameter catalog (the frozen pre-registration).
- **Part VI** — progress log.
- **Part VII** — reference files.

Ground every decision in this document and cite it in PRs. If Part III is genuinely silent or self-contradictory on a decision, STOP and surface it with options — do not guess.

---

# PART I — ENGINEERING GROUND RULES

These are inherited from the predecessor program and bind every change here. Summarized; the predecessor's `MASTER_BLUEPRINT.md` Part I is the canonical long form.

## 1. Modularity, no hard-coding, standard structure
Layered architecture; every threshold and parameter in config, never a literal in code; access external systems (Kite, the imported harness) only behind an adapter/protocol.

## 2. No temporary patch fixes; professional standards; proper logging
No happy-path shortcuts; structured logging (IST, correlation IDs, redaction); ruff + black + mypy(strict) + pytest green and pre-commit clean on every PR.

## 3. Completion Standard — "done" means proven at the call site
Inherited verbatim, because it is the rule that catches label-vs-behavior gaps:
- **(a) Claimed at a call site.** Every capability a name/docstring claims is invoked at a real call site (cite `file:line`), not merely defined.
- **(b) Certified against real machinery.** The certifying test feeds real machinery-computed inputs and **must fail if the underlying machinery is removed.** A test that still passes with the machinery deleted certifies nothing.
- Names/docstrings are claims and must be true at HEAD; gate tags are deliverable snapshots; evaluators fail closed; claims stated in bounded form, never rounded up; "harmless iff X" caveats verify X before X is relied on.

## Project-Specific Inviolable Rules (override convenience)

1. **The kill-gate is sacred.** No signal is called a real edge without passing all gate criteria. No tweaking-until-it-passes. Every variant charged to the effective-N ledger. **Most signals should die at the gate — that is success.**
2. **Point-in-time correctness, always.** No feature/signal uses data unavailable at the entry instant. Decision at the entry bar executes at the next bar's open. Trailing/expanding normalization only. Leakage tests in CI.
3. **Costs are always modeled.** No gross-only backtests. Full Indian intraday cost model + realistic slippage on every simulation — here, as a **corridor** (Part III).
4. **Honest cumulative *effective* trial counting.** Every variant ever run is charged to the program-wide ledger; DSR deflates by the effective (cluster-adjusted) count, never a raw integer. The ledger persists across sessions and phases.
5. **The imported harness is frozen.** Predecessor machinery (CPCV/DSR/PBO/ledger/cost core) is vendored as a versioned library, re-verified against golden masters (Deep Dive 03), and **never edited.** New behavior is a new layer on top, never a modification of the crown jewels.
6. **Honesty about outcomes.** The system must be able to conclude "no edge." A trustworthy KILL is the valuable outcome.
7. **Build in dependency order; respect the gates.** Harness import + data layer before any signal is run; Phase 1 before Phase 2.
8. **Ground every decision in this document, and cite it.**

---

# PART II — SYSTEM OVERVIEW & LOCKED DECISIONS

## What we are building
A daily, cross-sectional, market-neutral intraday long-short ranker on a less-efficient (mid-cap) NSE universe. Each day: rank the eligible universe by predicted entry-to-close direction; short the top-k gap-ups, long the bottom-k gap-downs; size to equal risk; enforce neutrality through execution-aware truncation; hold intraday; square off at close.

## The one research question
Does the ranker beat a random long-k/short-k selection that endures the **identical** execution model, net of cost? Selection skill is the only variable under test; everything else is nulled out by construction.

## Realistic-expectations frame (keep visible)
The predecessor returned a clean null on efficient large-caps. The disciplined prior here is another null. A KILL is the expected, valuable result. A PASS must survive a hostile, bias-bounded, execution-aware gate before it means anything, and only the Phase-2 crucible can issue a true PASS.

## The signal filter (why these signals, not the famous ones)
Many cross-sectional effects accrue *entirely overnight* or *entirely intraday* (the tug-of-war). Because this book holds entry-to-close only, overnight-accruing effects are useless. This **rules out cross-sectional momentum and classic multi-day reversal** (both accrue overnight; reversal is also cost-eaten and, in India, lives only in the most illiquid names). What survives is **intraday-accruing overnight-gap reversal** — the source of the signal.

## Locked decisions (frozen by the murder board — see `docs/MURDER_BOARD.md`)
- **Signals:** two arms — **A** (raw gap) and **A-Z** (gap ÷ ATR-20). Short top-k gap-ups, long bottom-k gap-downs.
- **Entry window:** 30-min default (enter ~09:45), swept {15, 30, 45}. Label defined from the entry instant.
- **Sizing:** inverse-vol / risk-parity within each leg — mandatory hygiene, not swept.
- **Neutrality:** Execution-Aware Dollar Neutrality via fixed-k pro-rata truncation to the smaller leg; gross-floor → drop the day. Never drop names to rebalance.
- **Eligibility:** dual point-in-time masks (`long_eligible` / `short_eligible`); circuit-lock filter; ex-ante ⌈k/2⌉ sector cap per leg.
- **Cost:** a corridor (optimistic Corwin-Schultz / pessimistic 3× + 1%-volume cap), with the survives-optimistic-dies-pessimistic band as the sole Level-2 purchase trigger.
- **Null:** Global Null Panel — N seeded random books/day through the identical execution model, generated once, sliced to the signal's surviving days; not purged (memoryless).
- **Data:** Kite-only for research; Phase 1 on the inherited survivor cache; Phase 2 on a point-in-time mid-cap universe. Buy nothing until the corridor earns it.
- **Repo:** this is a **fresh standalone repo seeded from the predecessor harness, not a GitHub fork.** Phase 1 and Phase 2 both live here; Phase 1 gates Phase 2.

## Data policy — Kite historical only (research)
No paid alternative feeds, no scraped fundamentals, no live depth in the research program. If a signal *requires* data Kite doesn't provide, it is data-gated, not faked. (Global-macro / L2 are out of research scope until a corridor result earns them.)

---

# PART III — TECHNICAL REFERENCE

Four layers. Layer 0 (the imported harness) is frozen; Layers 1–3 are new and built on top.

## Layer 0 — Imported statistical harness (FROZEN)
Vendored from the predecessor: CPCV path distribution, DSR (deflated by effective-N), PBO via CSCV, the effective-N trial ledger (correlation participation ratio), the Indian intraday cost primitives, and the robustness-battery scaffolding. **Imported as a versioned library, accessed only behind an adapter, and never edited.** Its correctness is re-established in the new repo by golden-master reconciliation and by re-running the predecessor's own hand-computed unit tests as an **import gate** (Deep Dive 03). New benchmark semantics (beat-random) and new cost layers (the corridor) are added *around* this core, never inside it.

## Layer 1 — Data & Universe
Kite historical ingestion behind `BrokerAdapter`; immutable raw + derived layers behind `Repository`. **Point-in-time universe** with delisted/suspended names included; **dual eligibility masks** (`long_eligible`/`short_eligible`, EQ-only + non-ASM/GSM + margin proxy); **static sector map** for the sector cap; **circuit-lock detection** (near-zero range relative to own recent range, or price-at-band + low volume). Gate-zero data-integrity validation before any signal trusts a number. Detail: Deep Dive 01.

## Layer 2 — Signal, Execution & Null
Ranking (A / A-Z) within masks; ex-ante sector cap; risk-parity sizing; Execution-Aware Dollar Neutrality (cap → sum per leg → smaller leg sets gross → pro-rata scale larger leg → gross-floor day-drop); cost corridor (optimistic/pessimistic two-bound runs, per-symbol Corwin-Schultz/Abdi-Ranaldo spread); the **Global Null Panel** generator. Detail: Deep Dive 02.

## Layer 3 — Validation & Gate
The imported gate criteria, unchanged, **plus** the beat-random-percentile benchmark as a new layer; DSR deflated across all arms (2 signals × window sweep); logged diagnostics (market-day conditioning, sector-concentration, circuit-flag fraction, short-ban fire-rate, day-drop fraction). Detail: Deep Dive 04.

---

# PART IV — THE BUILD PROGRAM (one phase per session)

## PHASE 0 — Scaffolding & Harness Import + Verification
Package skeleton, config, logging, CI. **Import the predecessor harness as a frozen vendored library and pass the full verification gate (Deep Dive 03): golden-master reconciliation + re-run of the predecessor's hand-computed unit tests, all green, provenance pinned.** GATE 0 = harness verified + scaffolding green.

## PHASE 1 — Data & Universe Layer
Kite ingestion; hygiene; point-in-time universe (Phase-1 stub uses the inherited survivor cache, stamped as such); dual masks (empirically unexercised in Phase 1 — logged ~0% fire-rate); sector map; circuit filter; gate-zero integrity validation. GATE 1 = data layer proven (leakage suite + integrity checks green).

## PHASE 2 — Signal, Execution & Null Layer
Signals A/A-Z; sector cap; risk-parity sizing; Execution-Aware Dollar Neutrality; cost corridor; Global Null Panel generator (seeded, reproducible). GATE 2 = execution + null proven (hand-checked truncation, symmetric-cost null, no-lookahead prefix-invariance on signals).

## PHASE 3 — Upper-Bound Smoke Test (survivor cache)
Run A/A-Z × {15,30,45} through the gate against the Global Null Panel, both cost bounds, on the inherited survivor cache. **KILL → hyper-trustworthy; stop. PASS → provisional; triggers Phase 4.** GATE 3 = smoke test complete, verdict recorded exploration-grade.

## PHASE 4 — Point-in-Time Crucible *(gated: only on a Phase-3 pass)*
Reconstruct constituent history; backfill delisted/suspended OHLCV; real ASM/GSM status; rerun identically on the clean mid-cap universe. **The only gate authorized to issue a true PASS.** GATE 4 = true verdict.

## PHASE 5 — Synthesis
Write up the finding (null or edge) in `RESEARCH_FINDINGS.md`; the two conditional sub-questions (which window, A vs A-Z) recorded as observations, not conclusions.

---

# PART V — SIGNAL & PARAMETER CATALOG (frozen pre-registration)

## Signals
| ID | Definition | Mechanism (a-priori) |
|---|---|---|
| **A** | rank by `(Open − PriorClose)/PriorClose`; short top-k, long bottom-k, hold to close | overnight overreaction corrected intraday (tug-of-war); strong India overnight-up/intraday-down asymmetry |
| **A-Z** | rank by **gap% ÷ ATR%** (`(Open−PriorClose)/PriorClose` ÷ `ATR(20)/price`) | tests the *anomaly-magnitude* hypothesis in the alpha logic (not the weights) |

A vs A-Z is the sign-vs-magnitude test; both charged to the ledger.

### Ambiguity resolved — A-Z normalization (2026-07-11)
`raw_gap / ATR(20)` was under-specified on units. **Resolved and frozen 2026-07-11:**
A-Z = **gap% ÷ ATR%** — the gap as a fraction divided by ATR-20 expressed in return
units (ATR ÷ price). **Rationale (on the record):** the gap measured in units of the
stock's normal daily move; **price-neutral by construction**. Note the two
unit-consistent spellings are algebraically identical for ranking — `gap_₹ ÷ ATR_₹ =
gap% ÷ ATR%` because `gap_₹ = gap%·price` and `ATR_₹ = ATR%·price`, so price cancels;
there is no absolute-vs-relative *ranking* choice. **FORBIDDEN form:** the units-mixed
`gap_fraction ÷ ATR_absolute_₹` (a fraction over a rupee figure), which is
1/price-dependent and tilts the ranking toward high/low-priced names — that is the
misbehavior guarded against. Implementation may use any algebraically-equivalent,
unit-consistent spelling, but the recorded definition is gap% ÷ ATR%. A-Z also
requires an **intraday→daily resample** before `atr(daily, 20)` (new Layer-2 code,
carrying its own point-in-time test: no future bars in the entry day's daily
aggregation).

## Frozen parameter ledger (blind, a-priori)
| Parameter | Value | Swept? |
|---|---|---|
| Signal arms | A, A-Z | both run |
| Entry window | 30 min default | {15, 30, 45} |
| k per leg | fixed (commit before first run) | No |
| Sizing | inverse-vol / risk-parity | No (hygiene) |
| Neutrality | Execution-Aware Dollar Neutrality (truncation) | No |
| Participation cap (pessimistic) | ≤ 1% entry-window volume | No |
| Spread model | Corwin-Schultz (× Abdi-Ranaldo check) | No |
| Pessimistic spread multiplier | ~3× | No |
| Gross-exposure floor | pre-registered ₹ threshold (commit before first run) | No |
| Sector cap per leg | ⌈k/2⌉ from one NSE sector | No |
| Eligibility masks | dual `long_eligible`/`short_eligible` | No |
| Null draws/day (N) | fixed, seeded (commit before first run) | No |
| Cost runs | optimistic + pessimistic bounds | both |

## Parked (each its own pre-registered study, later)
Sector-relative gap; residual reversal; options open-interest / gamma / max-pain positioning; macro-gating. Not in this program's first pass.

## Ruled out (with reason)
Cross-sectional momentum & classic multi-day reversal (overnight-accruing); equal-dollar weighting (measures variance, not skill); rank-preserving truncation / floating k (corrupts the null); unhedged imbalance & construction-time beta-neutrality (fail on execution reality); the "OI wall / front-run MM defense" pattern (widely-watched-level myth); ML feature-zoo ranker (~250 obs/yr overfits).

---

# PART VI — PROGRESS LOG

See `docs/PROGRESS.md`. Status at freeze: **pre-registration complete; no phase executed.** Next action: Phase 0 (scaffolding + harness import & verification).

---

# PART VII — REFERENCE FILES

- `docs/deep_dives/01_DeepDive_Data_and_Universe_Layer.md`
- `docs/deep_dives/02_DeepDive_Execution_and_Null_Layer.md`
- `docs/deep_dives/03_DeepDive_Harness_Import_and_Verification.md`
- `docs/deep_dives/04_DeepDive_Validation_and_Gate_Layer.md`
- `docs/MURDER_BOARD.md` — frozen adversarial-review audit trail
- `docs/PROGRESS.md`, `docs/RESEARCH_FINDINGS.md`
