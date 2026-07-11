# Research Findings — Cross-Sectional Intraday Long-Short Ranker (NSE)

> **How this document is maintained.** A *living research paper*, authored by the engineer/agent as each phase completes — **not pre-filled**. The scaffolds below are replaced with real, cost-inclusive, gate-computed numbers and honest verdicts only when produced by an actual validated run. An honest KILL is a complete result. Do not write results that have not been produced.

## Abstract
*‹filled at synthesis›* — a market-neutral, cross-sectional intraday ranker (overnight-gap reversal) tested for a cost-surviving edge on NSE, against a random long-short null enduring the identical execution model.

## 1. Objective & scope
Does a cross-sectional overnight-gap-reversal ranker, held entry-to-close in a market-neutral book, beat a random long-k/short-k selection net of cost — on a less-efficient (mid-cap) NSE universe? Scoped to this signal family, this universe, 5-min OHLCV, and the two-phase (survivor smoke test → point-in-time crucible) validation. Exploration-grade until Phase 2.

## 2. Data
*‹filled›* — Kite historical; Phase 1 survivor cache (stamped upper-bound); Phase 2 point-in-time mid-cap universe with delisted/suspended names.
### 2.1 Known limitation — survivorship (Phase 1)
The signal longs the biggest gap-downs; survivor-only data deletes those catastrophic longs and *inflates* long-leg P&L. Phase-1 results are survivorship-inflated upper bounds: a KILL is hyper-trustworthy, a PASS is meaningless until Phase 2.

## 3. Methodology
Imported, frozen statistical harness (CPCV/DSR/PBO/effective-N ledger — verified per Deep Dive 03); new benchmark = Global Null Panel percentile; Execution-Aware Dollar Neutrality; cost corridor; dual eligibility masks; ex-ante sector cap. Full spec in `MASTER_BLUEPRINT.md`.

## 4. Signal slate & results scorecard
| ID | Signal | Window | Cost bound | Beat-random percentile | Verdict | §ref |
|---|---|---|---|---|---|---|
| A | raw gap | ‹15/30/45› | ‹opt/pess› | ‹—› | ‹—› | §5.1 |
| A-Z | gap/ATR-20 | ‹15/30/45› | ‹opt/pess› | ‹—› | ‹—› | §5.2 |

## 5. Study results
### 5.1 — Signal A (raw gap) *‹filled›*
### 5.2 — Signal A-Z (vol-adjusted gap) *‹filled›*

## 6. Phase-2 crucible results *(only if Phase 1 passed)*
*‹filled›*

## 7. Synthesis
*‹filled›* — the sign-vs-magnitude question (A vs A-Z) and the window trade-off recorded as observations, not conclusions.

## 8. Conclusion
*‹filled›* — the null or the edge, scoped precisely; what it does and does not claim.

## 9. Reproducibility appendix
*‹filled›* — harness commit SHA + golden-master set; frozen params; null seed; universe reconstruction procedure.
