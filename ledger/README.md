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

Trial-id scheme: `cand1:<arm>:<window>` for a base arm (e.g. `cand1:A-Z:30`);
`cand1:<arm>:<window>:<cost>` for a cost-realism re-run.
