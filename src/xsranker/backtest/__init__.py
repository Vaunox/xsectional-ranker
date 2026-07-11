"""The run harness (Phase 3, Step 3a) — P&L engine + orchestration.

Turns real (or synthetic) OHLCV into the per-day NET RETURN streams the gate consumes.
Built and teeth-tested on synthetic / known-answer inputs BEFORE it touches the real
signal — the same discipline the gate followed (Step 1). A P&L bug here would produce a
confident wrong verdict (cf. the Phase-1 ``daily_open_close`` bug), so every layer has
teeth: the hold return is no-lookahead; the book -> net-return engine is hand-worked
(short-leg sign, per-position cost at both corridor bounds, neutral book -> ~0); the
orchestration is exercised end-to-end on a tiny universe with a closed-form answer.

Nothing here writes to ``src/vendored`` or freezes anything; the pre-registration
(``pre-registration-frozen``) stands untouched. The real cache is read-only, reached via
the config path / ``XSR_DATA_CACHE_PATH``, never a literal.
"""

from __future__ import annotations
