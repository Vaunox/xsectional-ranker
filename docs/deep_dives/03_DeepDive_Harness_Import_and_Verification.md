# Deep Dive 03 — Harness Import & Verification (Layer 0)

*The single most dangerous moment in this program is importing code from `intraday-strategy-lab`. The harness (CPCV, DSR, PBO, effective-N ledger, Indian cost primitives, robustness battery) is the crown jewel — validated over 20 studies — and reusing it is the whole reason a new program is cheap. But an import that is subtly wrong, silently modified, or version-drifted would invalidate every verdict this program ever issues, invisibly. This deep dive is the gate that makes the import trustworthy. **Nothing in Phase 1+ may run until this gate is green.***

---

## Scope

Everything imported from the predecessor: `cpcv`, `dsr`/`psr`, `pbo` (CSCV), the effective-N trial ledger (correlation participation ratio), the Indian intraday cost model primitives, the two-engine reconciliation harness, and any feature/indicator primitives reused verbatim (ATR, gap measures, cross-sectional rank helpers). **Not** in scope: the new execution/null/eligibility layers, which are original to this repo and tested separately.

---

## The governing rule: VENDOR, FREEZE, VERIFY — never edit

1. **Vendor, don't re-implement.** Copy the exact source modules into `src/vendored/harness/` (or install the predecessor as a pinned git dependency). Re-implementing "the same" DSR by hand would silently fork the math — forbidden. The imported code is byte-identical to a pinned predecessor commit.
2. **Freeze.** `src/vendored/` is read-only by convention and by CI. Any behavioral change this program needs (the beat-random benchmark, the cost corridor) is a **new layer that wraps or composes** the frozen code — never an edit inside it. This is Inviolable Rule 5.
3. **Verify.** The import is not "done" until it passes every check below. Per the Completion Standard, each verification test **must fail if the vendored machinery is removed or altered** — a test that would pass against a stub certifies nothing.

---

## Provenance pinning (the `VENDORED_FROM` manifest)

A committed `src/vendored/VENDORED_FROM.md` records, per imported module:
- source repo + **exact commit SHA** it was lifted from,
- the SHA-256 of each vendored file at import time,
- the predecessor test(s) that certify it, and
- the date and the operator sign-off.

CI recomputes the file hashes and **fails if any vendored file drifts** from its recorded hash. This is the tripwire against silent local edits to frozen code.

---

## Verification Gate — four mandatory checks (all must be green)

### Check 1 — Re-run the predecessor's own unit tests, unmodified, in this repo
The predecessor shipped hand-computed tests: costs against hand-worked rupee figures, DSR/PSR against hand-worked values, PBO/CSCV on constructed cases, effective-N clustering on known correlation structures, two-engine reconciliation within tolerance. **Port these tests verbatim and run them here.** If any fails, the import environment differs from the source (dependency version, float behavior, RNG) and the harness is **not** safely imported. Green = the vendored code computes what it did at home.

### Check 2 — Golden-master reconciliation (bit-for-bit)
The strongest check, and the one that catches version/environment drift the unit tests miss:
1. In the **predecessor repo**, run each harness function on a small, fixed, committed input fixture (a canned return stream, a canned trial-correlation matrix, a canned cost scenario) and **freeze the outputs** as golden files (`tests/golden/*.json`), each tagged with the predecessor commit SHA.
2. In **this repo**, run the vendored function on the identical fixture and assert the output equals the golden file to full numeric tolerance (exact where integer/bit-stable; `rtol=0, atol=1e-12` where float).
3. A mismatch means the vendored code behaves differently here than at home — **hard stop**, investigate (usually a transitive dependency pin: numpy/scipy/pandas version). Do not proceed by "close enough."

Golden fixtures cover, at minimum: one CPCV path-distribution, one DSR at a known effective-N, one PBO/CSCV case, one effective-N clustering of a known correlated group, one full round-trip cost on a known notional.

### Check 3 — Machinery-removal falsification (per the Completion Standard)
For every vendored function wired into this program, its certifying test **must fail if the function is deleted or replaced by a passthrough stub.** Concretely: a CI job that monkeypatches each vendored entry point to `raise`/return a sentinel and asserts the dependent test **goes red**. If a test still passes with the machinery gone, it was certifying a stub — rewrite it. This is the direct defense against the predecessor's own historical failure mode (gate grading stubs, orphaned primitives).

### Check 4 — Dependency & determinism lock
- Pin every transitive numeric dependency (numpy, scipy, pandas, TA-Lib) to the **exact versions** the predecessor used; record them in `VENDORED_FROM.md`. Golden-master equality is only meaningful against a locked numeric stack.
- Every stochastic harness path (CPCV fold generation, any bootstrap/MC in the battery) is **seeded and reproducible**; the seed is config, logged, and part of the golden fixtures. Two runs on the same input produce identical output, here and at home.

---

## The adapter boundary (isolation)

Nothing in this program imports vendored internals directly. A thin `HarnessAdapter` exposes exactly the functions Layer 3 needs (`cpcv_paths`, `deflated_sharpe`, `pbo`, `ledger_effective_n`, `round_trip_cost`, `robustness_battery`). Benefits:
- the new code depends on a **stable surface**, so a future harness version bump is a single adapter change, re-verified against golden masters;
- it makes the freeze enforceable — grep proves no module outside the adapter reaches into `src/vendored/`;
- it is where the **new layers compose** the frozen core (e.g. the cost corridor calls the frozen `round_trip_cost` twice, with optimistic and pessimistic spread inputs — the frozen function is unchanged; the corridor is the new wrapper).

---

## What is NOT imported (built fresh, tested independently)

These are original to this program and must **not** be smuggled in as "harness":
- the **beat-random benchmark** semantics (the predecessor's gate is beat-zero) — new Layer-3 code;
- the **cost corridor** (optimistic/pessimistic bounding) — a new wrapper over the frozen cost primitive;
- **Execution-Aware Dollar Neutrality**, truncation, the dual masks, the sector cap, the circuit filter — new Layer-1/2 code;
- the **Global Null Panel** generator — new Layer-2 code.

Each gets its own hand-computed tests (Deep Dives 02 & 04). The line is bright: **frozen imported math vs new original plumbing**, and the verification regime differs — golden-master reconciliation for the former, hand-computed correctness for the latter.

---

## Import gate — definition of done

GATE 0 (harness) is green iff: predecessor unit tests re-run green here (Check 1); every golden master reconciles bit-for-bit (Check 2); every vendored function fails its test when removed (Check 3); the numeric stack and seeds are locked and reproducible (Check 4); `VENDORED_FROM.md` is complete with SHAs and operator sign-off; and CI enforces the vendored-file hash tripwire. Only then may Phase 1 open.

## To expand later (as tasks demand)
- Harness version-bump runbook (re-vendor → re-hash → re-reconcile → re-sign).
- Golden-fixture regeneration procedure (must be run in the predecessor repo, never here).
