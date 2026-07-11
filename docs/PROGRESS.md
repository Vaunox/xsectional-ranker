# PROGRESS — Cross-Sectional Intraday Long-Short Ranker

*Program log. One appended entry per session; never edited retroactively. HEAD is the source of truth; gate tags are deliverable snapshots.*

*Status: **Phase 1 (Data & Universe layer) built; GATE 1 green; holding before Phase 2 (uncommitted, pending review).** Data seam (`BrokerAdapter`/`Repository` over the inherited external Parquet cache, config path, no ingestion), hygiene (calendar/session, corp-action raw+adjusted, bad-tick, gap, liquidity), survivor-cache universe stub, full dual eligibility masks (~0% fire logged), static sector map, conservative circuit filter, gate-zero integrity, and the two load-bearing leakage suites (prefix-invariance + train/serve-skew) are in place. No signal/execution/null/gate code. GATE 0 remains signed off + committed (`gate-0`).***

**Phase-1 stamps (on every artifact).** (1) survivorship-inflated upper bound — universe is a survivor-cache stub, real point-in-time reconstruction deferred to Phase 4; (2) split/bonus-adjusted, cash dividends unadjusted — bounded ex-div residual accepted for the survivor upper bound, dividend adjustment deferred to Phase 4; (3) dual masks architecturally complete but empirically unexercised (~0% fire on large-cap survivors is the correct signature, logged); (4) no Kite ingestion this phase — data read from the external Parquet cache read-only.

**Gate 0 semantics (do not over-read).** GATE 0 = **verified + frozen**, *not* wired into the research pipeline. The Phase-0 call site for every vendored function is the **verification harness itself** (ported tests, golden runners, the machinery-removal registry). Real research call sites arrive in Phase 2/3. The single-name vendored backtester is frozen/verified but deliberately **not** surfaced on the adapter — the cross-sectional book's two-engine reconciliation is new Phase-2 code (`src/vendored/VENDORED_FROM.md`).

---

## Gate checklist

| Gate | Deliverable | Status |
|---|---|---|
| Gate 0 | Scaffolding + **harness import verified** (golden-master reconciliation + predecessor tests green + provenance pinned) | ☑ green — operator signed off 2026-07-11 (`gate-0` tag) |
| Gate 1 | Data & universe layer (point-in-time, dual masks, sector map, circuit filter, gate-zero integrity) | ☑ green — committed + **CI green** (140 passed, 3 cache-dependent skipped) on the clean Windows runner; `gate-1` tag |
| Gate 2 | Signal + execution + null layer (A/A-Z, truncation, cost corridor, Global Null Panel) | ☐ |
| Gate 3 | Phase-1 Upper-Bound Smoke Test complete (verdict exploration-grade) | ☐ |
| Gate 4 | Phase-2 Point-in-Time Crucible *(only if Gate 3 passed)* — the sole true-PASS gate | ☐ |
| Gate 5 | Synthesis (`RESEARCH_FINDINGS.md`) | ☐ |

## Frozen-at-implementation values (commit before the first run)
*Still unset after Phase 0 — none of these were touched (they gate the first run, not the harness import).*
- `k` (names per leg)
- gross-exposure floor (₹ threshold)
- `N` (null draws per day)
- ~~liquidity floor (min median daily traded value)~~ — **committed in Phase 1**: ₹5 cr median daily traded value over a 20-day trailing lookback (`config/default.yaml` `hygiene.liquidity_floor`).
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
| 2026-07-11 | Phase 1 | Data & Universe layer: `BrokerAdapter`/`Repository` over external Parquet cache (config path, read-only, no ingestion); hygiene (NSE calendar+IST session, corp-action raw+adjusted, bad-tick, gap, trailing liquidity floor); survivor-cache universe stub; full dual eligibility masks; static sector map; conservative circuit filter | Reconciliation cleared (49/5-min/2015–2026/split-bonus-adjusted; div residual accepted). GATE ZERO green (6 checks incl known-split no-spurious-gap: max adj gap 0.029 « split-scale; adjusted==raw identity; masks ~0% fire). Leakage suites green in CI (prefix-invariance + train/serve-skew, synthetic). Full gate **143 passed** (3 cache-dependent skip in CI); ruff/black/mypy-strict clean; freeze tripwire + boundary intact; predecessor `src/lab` untouched | `src/xsranker/{data,features}/`; `config/{default,sectors,integrity_reference}.yaml` + `universe/survivor_cache.yaml` | **GATE 1 green.** Liquidity floor committed (₹5cr/20d). Stamps applied (survivorship upper bound; split/bonus-adj + div deferred; masks unexercised ~0%; no ingestion). No signal/execution/null/gate code. **Bug caught + fixed:** `daily_open_close` mis-computed the last-bar-per-day index (a reverse-`np.unique` trick), which corrupts `overnight_gap` and thus both gate-zero AND the Phase-2 gap signal's foundation; caught by `test_split_removes_the_spurious_gap` (the corp-action teeth test, 0.14 → 0.0289); post-fix split-gap **0.0289 stable across 3 independent re-runs** — live proof the integrity suite can go red. Cache path is config (env-var `XSR_DATA_CACHE_PATH` override + relative placeholder; no absolute machine path committed). **Two issues CI caught that local missed** (local ruff/black/mypy honor `.gitignore` and ran against the installed editable package, masking both): (a) an unanchored `.gitignore` `data/` pattern silently excluded the entire `src/xsranker/data/` source from commits — fixed by anchoring to `/data/` and committing the 19 files; (b) environment-dependent isort classification (I001) — fixed with `known-first-party` + `detect-same-package=false`, verified on a `git archive` + fresh `uv sync` extract (the true CI-equivalent). Final green commit `cf39d04`. |
