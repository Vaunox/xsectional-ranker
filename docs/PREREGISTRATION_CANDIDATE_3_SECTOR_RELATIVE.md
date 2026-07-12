# Pre-Registration — Candidate #3: Sector-Relative Intraday Reversal

> **STATUS: FROZEN — operator sign-off 2026-07-12 (D1–D3 ruled, distinctness band pinned). BLIND.**
> Third candidate (roadmap backlog #3). Every parameter pinned BLIND, and the **distinctness band**
> (§7) is pinned **before** the independence screen is computed. The **intraday-reversal** form only
> — the strength/**momentum** form is disqualified a-priori (sector-relative momentum accrues
> overnight; this book holds entry→close). Candidate #1 gap A-Z: standalone-KILL, **BANKED provisional**
> (the stable's 1 member); candidate #2 volume-delta: fully dead. Machinery reusable. `src/vendored/`
> pristine. Next: implement the SR feature + prefix-invariance teeth → run the independence screen
> BLIND against the pinned band → bring the numbers → only if it clears the distinctness gate does the
> single verdict run follow (a strictly later commit).

---

## 1. Objective & the backlog frame

A small, independent, morning-computable signal for the fusion stable — **real + independent, not
big**. Candidate #3 reads a *different morning information source* from the retired candidates:
not the overnight gap (candidate #1) and not directional volume flow (candidate #2), but a stock's
**idiosyncratic morning move relative to its sector**.

## 2. Signal (blind, a-priori, mechanism-first)

**The sector-relative morning move.** For each stock on each day:

```
SR(name) = morning_return(name) − mean_{peers}( morning_return(peer) )
```

- **`morning_return`** = the open→entry return (`entry_window_return`), the same window / entry the
  trade uses.
- **peers** = the OTHER names in the stock's NSE sector (static sector map), **leave-one-out** (the
  stock is excluded from its own benchmark, so its move never contaminates its baseline). A stock
  needs **≥ 2 sector peers** (a ≥3-name sector) for a meaningful benchmark; stocks in smaller
  sectors are dropped. On the 49-name survivor cache this yields ~**37 tradeable names** across 7
  sectors (Financials 11, FMCG/IT/Auto 5, Pharma/Metals 4, Oil&Gas 3); Retail & Telecom (1 name)
  and the 2-name sectors are dropped. *(D1 — ruled ≥2 peers; excluded-name count logged as a diagnostic.)*

**Two arms (the sign-vs-magnitude test, parallel to candidate #1's A / A-Z):**
- **SR** — the raw sector-relative move.
- **SR-Z** — `SR ÷ ATR%` (the stock's ATR-20 in return units), the move in units of the stock's own
  normal volatility. Magnitude tested in the alpha logic, not the weights (murder-board #5).

2 signals × 3 windows = **6 arms** charged. *(D2 — ruled 2 arms.)*

**Sector-benchmark caveat (honest stamp).** The survivor cache holds the constituents, not the NSE
sector **indices**, so the sector benchmark here is the leave-one-out **equal-weight peer mean** — a
proxy for the sector index. A real point-in-time sector index is a Phase-4 refinement (like the
delisted-inclusive universe), not this smoke test.

## 3. Direction + mechanism (REVERSAL)

**REVERSAL** — LONG the **lowest** SR (stocks that underperformed their sector this morning, expected
to catch up), SHORT the **highest** (outperformed, expected to revert). A-priori mechanism:
**sector-spread mean-reversion / statistical arbitrage** — a stock that diverges *idiosyncratically*
from its sector in the morning tends to **converge** back to the sector over the session, and that
convergence accrues in the held entry→close window. This is why the **reversal** form is valid where
the momentum form is not: sector-relative momentum (persisting divergence) accrues overnight and is
useless to an intraday book — disqualified a-priori, not tested.

Reuses `build_book`'s REVERSAL leg-assignment (long lowest / short highest — the default, as
candidate #1); no new leg-direction code.

## 4. Window + point-in-time

Windows `{15, 30, 45}`. `SR` uses only bars ≤ entry (the morning return is prefix-invariant), and
the sector mean is a **same-day cross-sectional** average (all peers' morning returns known at
entry) — no look-ahead. Prefix-invariance teeth required (mirroring candidate #2).

## 5. Entry / exit / execution / cost / null / gate — INHERITED, unchanged

Entry at window close, hold to close; k=5; risk-parity sizing; Execution-Aware Dollar Neutrality;
⌈k/2⌉ sector cap; dual masks; circuit filter; gross floor ₹100,000. **Cost = fees + fixed 5/18 bps**
(the live standard, no CS). Global Null Panel (seed 20260711, N=1000, feasible capped disjoint,
null-health telemetry). Gate: beat-random ≥ 95th on the excess stream; DSR ≥ 0.95; CPCV median > 0;
positive-fraction > 0.5; PBO ≤ 0.20; **absolute-net > 0 per bound**.

> **One tension to flag (D3): the ⌈k/2⌉ sector cap vs a sector-relative signal.** The sector cap
> exists to stop the book becoming an accidental macro sector bet. A sector-relative signal is
> *already* sector-neutralised by construction (it ranks within-sector divergence), so the cap and
> the signal push the same way — but on the ~37-name / 7-sector universe, ⌈5/2⌉=3-per-sector may
> bind hard (Financials has 11 names). Surface: does the cap over-constrain a signal that is already
> sector-orthogonal? My read: keep the cap (it's cheap insurance and the null suffers it identically),
> but flag it for your ruling.

## 6. Cumulative ledger (Rule 4) + the return-blind-screen policy

Candidate #3's 6 arms charge on top of the durable ledger: candidate #1's **6** + candidate-2r
V_resid's **3** = **9 committed**, + candidate #3's 6 → cumulative effective-N over all
return-evaluated trials. Per the standing **return-blind-screen bright line** (PROGRESS.md): the
pre-run independence screen (§7) is return-blind → **not** charged; only the verdict run is.

## 7. Hard pre-run independence screen (blind — reuses the D8 machinery)

Before any verdict run, compute per window (Pearson + Spearman; gate on rank):

- **The DISTINCTNESS gate — corr(SR, candidate #1's gap) and corr(SR-Z, gap÷ATR). PINNED BLIND
  (2026-07-12), before the numbers:**
  - **rank-corr ≥ 0.8** → SR is substantially **the same reversal on a relabelled window** → fusion
    value ≈ nil; record as a **finding, not a feature**.
  - **rank-corr < 0.5** → **distinct** (an independent partner for the banked gap feature — which is
    exactly what the stable needs, not a second copy of gap).
  - **0.5 ≤ rank-corr < 0.8** → **STOP, escalate** to the operator.

  This is *the* gate that matters: candidate #1 (gap) is banked, so the stable needs an *independent*
  reversal partner, not a re-labelled duplicate that would collapse the effective-N.
- **corr(SR, raw morning return)** — **diagnostic, NOT a gate.** Candidate #3 openly *is* a
  morning-price signal (unlike candidate #2, whose V falsely *claimed* to be flow), so a high value is
  expected and not disqualifying; it is reported to quantify how much the sector-demeaning moves the
  ranking (if ≈ 1.0, the sector part is immaterial and candidate #3 collapses to raw intraday reversal
  — surface that).

## 8. Frozen parameter ledger (pin at sign-off)

| Parameter | Value | Swept? | Charged? |
|---|---|---|---|
| Signal arms | **SR** (raw), **SR-Z** (÷ATR%) | both | Yes (2) |
| Direction | **REVERSAL** (long lowest, short highest) | No | — |
| Window | `{15,30,45}` | Yes | Yes (6 arms) |
| Sector benchmark | leave-one-out equal-weight peer mean, **≥2 peers** | No | — |
| morning move | open→entry return | No | — |
| k / sizing / neutrality / caps / masks / floor | inherited | No | — |
| Cost corridor | fees + fixed 5 / 18 bps, impact 0 | both | — |
| Null / gate bars / seed / N | inherited (20260711 / 1000 / 95th, DSR .95, PBO .20, abs-net) | No | — |
| Ledger | cumulative: 9 committed + candidate #3's 6 | — | Yes |

## 9. Decisions — RULED (operator sign-off 2026-07-12)

| # | Decision | Ruling (accepted as recommended) |
|---|---|---|
| **D1** | Min sector peers | **≥2** (≥3-name sector, ~37 tradeable names) — a 1-peer benchmark is a noisy pair spread, not a sector. **Log the excluded-name count** as a diagnostic. |
| **D2** | Arm count | **2 arms (SR / SR-Z)** — sign-vs-magnitude belongs in the signal, and the precedent is direct: on candidate #1 the **normalized arm (A-Z) carried the edge while raw A did not** → the normalization axis matters. |
| **D3** | ⌈k/2⌉ sector cap | **Keep** — cheap insurance, and the null suffers it identically (symmetric comparison). On an already-sector-neutral signal it should **rarely bind**: **log its bind-rate** — a high bind-rate would signal the sector-demeaning isn't working as intended. |

**Diagnostics to log (per the rulings):** excluded-name count (D1), sector-cap bind-rate (D3), plus
the standard null-health / signal-day-drop / short-ban.

**FROZEN 2026-07-12. Next:** implement the SR/SR-Z feature + prefix-invariance teeth → run the
independence screen BLIND against the pinned distinctness band (§7) → bring the numbers → the single
verdict run follows **only if** the distinctness gate clears. `src/vendored/` pristine; recorded
verdicts untouched.
