# Durable trial ledger (Inviolable Rule 4)

This directory is the **durable, committed** effective-N trial ledger. It holds one JSON per
trial (a strategy arm's realized return stream) plus [`MANIFEST.yaml`](MANIFEST.yaml), which
declares the prior-candidate streams that **must** be present before the gate may judge a new
candidate.

## Why it exists (the R2 defect)

Candidate #1's smoke run wrote its six arm streams to an **ephemeral** temp directory that was
never committed. The streams were lost; only the number *effective-N ≈ 5.98* survived, as prose
in `docs/RESEARCH_FINDINGS.md`. That silently broke Rule 4's cross-session guarantee — every
future candidate would have deflated its DSR against an unreconstructable, under-counted trial
history. Found and fixed 2026-07-12 (same class as the null-construction bug).

## How it is kept honest

`xsranker.ledger.verify_ledger_integrity()` **fails closed**: if any manifest-required stream is
missing or empty at gate time, it raises `LedgerIntegrityError` rather than let the gate silently
undercount effective-N. `scripts/regenerate_ledger.py` deterministically regenerates candidate
#1's streams (seed `20260711`, frozen machinery) + the cost-realism re-runs, writes them here,
and arms the manifest — this must be green **before** candidate #2's run.

Trial-id scheme: `cand1__<arm>__<window>` for a base arm (e.g. `cand1__A-Z__30`), using `__`
(not `:`) so the id is a valid filename on Windows (the ledger writes `<trial_id>.json`).

## Reproduction verified (2026-07-12) — a first-class finding

The R2 defect cost us candidate #1's original streams, **but the numbers survive verification.**
`scripts/regenerate_ledger.py` reproduces RESEARCH_FINDINGS §8 **exactly** (every surviving-day
count, signal-drop %, null-draw-drop 0%, null median ≈ −234 bps pessimistic, short-ban 0) and
recomputes **effective-N = 5.9816 at N=1000** (5.9831 at the N=50 validation) — matching the
historically-reported ~5.98 with no material divergence. Candidate #1's corrected Phase-3 KILL is
therefore now **verified reproducible from committed code** (it was not before — the ad-hoc run's
streams were ephemeral), which retroactively validates the corrected Phase-3 close.

## Ledger composition (operator ruling, 2026-07-12)

The ledger counts **independent looks, not re-pricings.** Candidate #1 is **six** streams (six
selections, each once), regenerated under the original Corwin-Schultz corridor. The cost-realism
re-runs (fees-only / fees+5bps / fees+AR) were re-pricings of the same six selections — recorded
in each stream's `params.cost_realism_reruns`, **never as their own rows** (an 18-row ledger would
inflate the effective-N that sets every future candidate's DSR bar).

## Cumulative composition (2026-07-12) — 15 streams across 3 candidates

Every arm here was **RUN and evaluated on returns** → CHARGED (the standing bright line: return-blind
screens are not charged; return-evaluated runs always are). Return-blind rejections (V/V-A at D8) are
**absent by design**, not omitted.

| candidate | streams | trial-ids | verdict |
|---|---|---|---|
| `candidate-1-gap-reversal` | 6 | `cand1__{A,A-Z}__{15,30,45}` | KILL (banked provisional feature) |
| `candidate-2r-vresid` | 3 | `cand2r__V_resid__{15,30,45}` | KILL (empty) |
| `candidate-3-sector-relative` | 6 | `cand3__{SR,SR-Z}__{15,30,45}` | KILL (independent but empty) |

**Cumulative effective-N = 13.48** at N=1000 (15 raw arms; the correlation-clustered look count that
deflates every future candidate's DSR bar). Candidate #3 charged under the RE-PINNED corridor
(RESEARCH_FINDINGS §7.5): size-aware fees @ ₹10k deployment notional + NSE-impact spread 1/5 bps.
