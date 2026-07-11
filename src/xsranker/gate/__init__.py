"""Layer 3 — the Validation & Gate layer.

The imported kill-gate (CPCV / DSR / PBO / effective-N ledger / path-positivity),
reached UNEDITED through :class:`~xsranker.harness.adapter.HarnessAdapter`, plus
exactly ONE new criterion: the **beat-random-percentile** benchmark. "Positive" is
not zero but the Global Null Panel percentile.

Operator rulings (2026-07-11):

* **Composition (Ruling 1).** Each arm's per-day quantity is redefined as *net minus
  the null median* — the selection alpha over an execution-matched random book,
  stripped of the per-day structure/liquidity/survivorship luck that ranked and
  random both enjoy. That EXCESS stream feeds the imported CPCV/DSR/PBO; the raw net
  is never deflated (it would bank survivorship as alpha). The beat-random percentile
  is the per-arm significance bar; the DSR owns cross-arm multiplicity. Orthogonal
  axes → no double-penalty, no double-credit.
* **Diagnostics (Ruling 2).** DD04 listed profit factor / expectancy / regime
  stability as gate criteria, but they are ABSENT from the frozen harness. Resolved as
  LOGGED DIAGNOSTICS, not gates (regime stability folds into market-day conditioning).
  The binding gate is {beat-random, DSR, PBO, CPCV median/10th, path-positivity} — the
  only new criterion is beat-random.
* **Ledger charging (Ruling 3).** The 6 signalxwindow arms are the search axes; the
  cost corridor is a mandatory both-bounds robustness range, not a selectable trial.
  Effective-N clusters the 6 from the actual streams (never a raw 6).

This layer is tested on SYNTHETIC fixtures only; its correctness is established on
constructed inputs, never by running it on the real signal.
"""

from __future__ import annotations
