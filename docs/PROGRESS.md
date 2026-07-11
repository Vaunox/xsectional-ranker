# PROGRESS — Cross-Sectional Intraday Long-Short Ranker

*Program log. One appended entry per session; never edited retroactively. HEAD is the source of truth; gate tags are deliverable snapshots.*

*Status: **Phase 0 complete; GATE 0 signed off (2026-07-11) and committed.** Scaffolding (config, logging, CI) and the frozen vendored harness (`src/vendored/lab`, pinned to predecessor `0c5c592`) are in place behind `HarnessAdapter`; all four Deep-Dive-03 checks pass; provenance independently verified against source and operator-signed (`src/vendored/VENDORED_FROM.md`). Next action: Phase 1 — data & universe layer. **Phase 1 remains closed pending separate operator sign-off.***

**Gate 0 semantics (do not over-read).** GATE 0 = **verified + frozen**, *not* wired into the research pipeline. The Phase-0 call site for every vendored function is the **verification harness itself** (ported tests, golden runners, the machinery-removal registry). Real research call sites arrive in Phase 2/3. The single-name vendored backtester is frozen/verified but deliberately **not** surfaced on the adapter — the cross-sectional book's two-engine reconciliation is new Phase-2 code (`src/vendored/VENDORED_FROM.md`).

---

## Gate checklist

| Gate | Deliverable | Status |
|---|---|---|
| Gate 0 | Scaffolding + **harness import verified** (golden-master reconciliation + predecessor tests green + provenance pinned) | ☑ green — operator signed off 2026-07-11 (`gate-0` tag) |
| Gate 1 | Data & universe layer (point-in-time, dual masks, sector map, circuit filter, gate-zero integrity) | ☐ |
| Gate 2 | Signal + execution + null layer (A/A-Z, truncation, cost corridor, Global Null Panel) | ☐ |
| Gate 3 | Phase-1 Upper-Bound Smoke Test complete (verdict exploration-grade) | ☐ |
| Gate 4 | Phase-2 Point-in-Time Crucible *(only if Gate 3 passed)* — the sole true-PASS gate | ☐ |
| Gate 5 | Synthesis (`RESEARCH_FINDINGS.md`) | ☐ |

## Frozen-at-implementation values (commit before the first run)
*Still unset after Phase 0 — none of these were touched (they gate the first run, not the harness import).*
- `k` (names per leg)
- gross-exposure floor (₹ threshold)
- `N` (null draws per day)
- liquidity floor (min median daily traded value)
- null-percentile pass threshold

## Deferred to later phases (recorded so they are not forgotten)
- **Feature primitives** (`ATR`, `gap`, `cross_sectional_rank`) — vendor from the *same* pin `0c5c592` into `src/vendored/VENDORED_FROM.md` in **Phase 1**, when the data/signal layer gives them a real call site (identical freeze/adapter/golden pattern).
- **Literal-N guard test** — the predecessor's `test_no_caller_passes_a_literal_trial_count` (a source-scan that business code never hard-codes the trial count) was omitted from the Check-1 port (no DSR business call sites exist yet). Re-add it in **Phase 2**, scoped to `src/xsranker`, when the gate acquires real DSR call sites.

## Standing constraints (from `MASTER_BLUEPRINT.md` Part I)
- Kill-gate sacred; no tweak-to-pass; every arm charged to the effective-N ledger.
- Point-in-time correctness always; leakage tests in CI.
- Costs always modeled — as a corridor.
- Imported harness frozen; never edited; verified per Deep Dive 03.
- Phase 1 gates Phase 2; a Phase-1 pass is provisional only.

---

## Session log

| Date | Phase | What | Verification | Artifacts | Verdict/Notes |
|---|---|---|---|---|---|
| 2026-07-11 | Phase 0 | Scaffolding (config/logging/CI) + vendored harness (16 files @ pin `0c5c592`) behind `HarnessAdapter` | 4 checks green: Check 1 (52 ported tests), Check 2 (6 goldens, drift 0.0), Check 3 (14 surface fns falsified 14/14), Check 4 (stack pinned Py3.11/numpy2.4.6/scipy1.17.1, seed reproducible). Full gate: **104 passed**; ruff/black/mypy-strict clean. Baseline proven at pin (predecessor `375 passed`) | `src/vendored/` + `VENDORED_FROM.md` (operator-signed) + `vendored_hashes.txt`; `tests/golden/` (6); CI + hash tripwire + freeze boundary | **Gate 0 green; operator signed off 2026-07-11; `gate-0` tag cut.** Documented omissions accepted: 1 vacuous ledger source-scan guard removed (re-add Phase 2, scoped to `src/xsranker`); 2 strategy-layer-coupled robustness tests deferred (two-engine reconciliation still covered by `test_validation_core.py`). Feature primitives deferred to Phase 1 from same pin. Phase 1 closed pending separate sign-off. |
