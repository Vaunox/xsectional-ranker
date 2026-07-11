"""HarnessAdapter — the single, stable surface onto the frozen vendored harness.

This is the ONLY module in ``xsranker`` that imports ``lab.*`` (the byte-identical
predecessor code vendored at commit ``0c5c592`` under ``src/vendored``; see
``src/vendored/VENDORED_FROM.md``). The freeze-boundary check
(``scripts/check_freeze_boundary.py``) fails CI if any other ``xsranker`` module
reaches into the vendored tree.

**Late binding is deliberate.** Every method calls its vendored entry point
*module-qualified* (``_metrics.deflated_sharpe_ratio(...)``, not a name imported
at module load). That is what lets the machinery-removal falsification
(Deep Dive 03, Check 3) stub a vendored function and observe the adapter-driven
certifying test go red — proving the surface routes to real machinery, not a
stub.

**What is deliberately NOT surfaced.** The vendored single-name event/vectorized
backtester (``lab.research.validation.backtester.run_backtest``,
``robustness.vectorized_backtest``, ``robustness.two_engines_agree``) is frozen
and verified (Check 1) but not exposed here: this program does not drive the
single-name engine. The cross-sectional book and its own two-engine reconciliation
are new Phase-2 code (carry-forward note, ``VENDORED_FROM.md``).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np

# Vendored modules — imported module-qualified (never `from … import <name>`),
# so calls stay late-bound for Check 3. This is the whole point of the boundary.
from lab.data.features import indicators as _indicators
from lab.data.features import ohlcv as _vendored_ohlcv
from lab.research.trials import ledger as _ledger
from lab.research.validation import costs as _costs
from lab.research.validation import cpcv as _cpcv
from lab.research.validation import metrics as _metrics
from lab.research.validation import pbo as _pbo
from lab.research.validation import robustness as _robustness
from lab.research.validation import sharpe as _sharpe
from xsranker.core.config import Settings
from xsranker.core.types import OHLCV, FloatArray

# Re-export the vendored result/value types so callers need not import lab.*.
CPCVResult = _cpcv.CPCVResult
CPCVDistribution = _cpcv.CPCVDistribution
PBOResult = _pbo.PBOResult
CostModel = _costs.CostModel
TrialLedger = _ledger.TrialLedger

_IST = ZoneInfo("Asia/Kolkata")


class HarnessAdapter:
    """Thin, stable facade over the frozen statistical harness (Layer 0).

    Bound to a :class:`~xsranker.core.config.Settings` so it can resolve the
    pinned cost config and the master determinism seed without any caller reaching
    into the vendored tree.
    """

    def __init__(self, settings: Settings) -> None:
        """Bind the adapter to resolved settings (config dir + seed)."""
        self._settings = settings

    @property
    def settings(self) -> Settings:
        """The bound settings (config dir, seed, logging)."""
        return self._settings

    # -- Sharpe --------------------------------------------------------------- #
    def per_period_sharpe(self, returns: Sequence[float]) -> float:
        """Per-period Sharpe of a return stream."""
        return _sharpe.per_period_sharpe(returns)

    def annualized_sharpe(self, returns: Sequence[float], periods_per_year: float) -> float:
        """Annualized Sharpe at a given realized observation frequency."""
        return _sharpe.annualized_sharpe(returns, periods_per_year)

    # -- Deflated / probabilistic Sharpe -------------------------------------- #
    def probabilistic_sharpe_ratio(
        self, observed_sharpe: float, benchmark_sharpe: float, n: int, skew: float, kurtosis: float
    ) -> float:
        """PSR: P(true Sharpe > benchmark) given the sample moments."""
        return _metrics.probabilistic_sharpe_ratio(
            observed_sharpe, benchmark_sharpe, n, skew, kurtosis
        )

    def expected_max_sharpe(self, n_trials: float, trial_sharpe_std: float) -> float:
        """Expected maximum Sharpe under a null of ``n_trials`` independent trials."""
        return _metrics.expected_max_sharpe(n_trials, trial_sharpe_std)

    def deflated_sharpe_ratio(
        self,
        observed_sharpe: float,
        n: int,
        skew: float,
        kurtosis: float,
        *,
        effective_trials: float,
        trial_sharpe_std: float,
    ) -> float:
        """Deflated Sharpe Ratio, deflated by the EFFECTIVE (cluster-adjusted) trials."""
        return _metrics.deflated_sharpe_ratio(
            observed_sharpe,
            n,
            skew,
            kurtosis,
            effective_trials=effective_trials,
            trial_sharpe_std=trial_sharpe_std,
        )

    # -- CPCV ----------------------------------------------------------------- #
    def combinatorial_purged_cv(
        self,
        returns: Sequence[float],
        entry_times: Sequence[datetime],
        exit_times: Sequence[datetime],
        *,
        n_groups: int,
        k_test_groups: int,
        periods_per_year: float,
        embargo: timedelta | None = None,
    ) -> _cpcv.CPCVResult:
        """Run purged, embargoed CPCV; return the path-Sharpe distribution."""
        if embargo is None:
            return _cpcv.combinatorial_purged_cv(
                returns,
                entry_times,
                exit_times,
                n_groups=n_groups,
                k_test_groups=k_test_groups,
                periods_per_year=periods_per_year,
            )
        return _cpcv.combinatorial_purged_cv(
            returns,
            entry_times,
            exit_times,
            n_groups=n_groups,
            k_test_groups=k_test_groups,
            periods_per_year=periods_per_year,
            embargo=embargo,
        )

    def cpcv_distribution_summary(self, path_sharpes: Sequence[float]) -> _cpcv.CPCVDistribution:
        """Summarize a CPCV path-Sharpe distribution over its finite paths."""
        return _cpcv.cpcv_distribution_summary(path_sharpes)

    # -- PBO / CSCV ----------------------------------------------------------- #
    def probability_of_backtest_overfitting(
        self,
        performance_matrix: Any,
        entry_times: Sequence[datetime],
        exit_times: Sequence[datetime],
        *,
        n_splits: int = _pbo.DEFAULT_N_SPLITS,
        embargo: timedelta | None = None,
    ) -> _pbo.PBOResult:
        """Estimate PBO from a (periods x configs) performance matrix via CSCV."""
        if embargo is None:
            return _pbo.probability_of_backtest_overfitting(
                performance_matrix, entry_times, exit_times, n_splits=n_splits
            )
        return _pbo.probability_of_backtest_overfitting(
            performance_matrix, entry_times, exit_times, n_splits=n_splits, embargo=embargo
        )

    # -- Effective-N trial ledger --------------------------------------------- #
    def trial_ledger(self, storage_dir: Path) -> _ledger.TrialLedger:
        """Open (or create) the append-only effective-N trial ledger."""
        return _ledger.TrialLedger(storage_dir)

    # -- Indian cost primitives ----------------------------------------------- #
    def load_cost_model(self) -> _costs.CostModel:
        """Load the frozen Indian intraday cost model from the pinned config dir."""
        return _costs.load_cost_model(self._settings.config_dir)

    def trade_cost_fraction(
        self,
        cost_model: _costs.CostModel,
        notional: float,
        entry_price: float,
        entry_volume: float,
        *,
        stressed: bool = False,
    ) -> float:
        """Per-trade round-trip cost fraction, liquidity-aware via the entry bar."""
        return _costs.trade_cost_fraction(
            cost_model, notional, entry_price, entry_volume, stressed=stressed
        )

    # -- Robustness battery --------------------------------------------------- #
    def monte_carlo_sign_flip(
        self, returns: Sequence[float], *, n_shuffles: int = 1000, seed: int | None = None
    ) -> float:
        """Fraction of sign-flipped nulls the real per-period Sharpe beats.

        Uses the master config seed unless one is passed explicitly (Check 4).
        """
        return _robustness.monte_carlo_sign_flip(
            returns, n_shuffles=n_shuffles, seed=self._settings.seed if seed is None else seed
        )

    def inject_ohlc_noise(
        self, candles: Sequence[Any], *, relative_scale: float = 0.0005, seed: int | None = None
    ) -> list[Any]:
        """Return candles with each bar's price level multiplicatively perturbed."""
        return _robustness.inject_ohlc_noise(
            candles,
            relative_scale=relative_scale,
            seed=self._settings.seed if seed is None else seed,
        )

    def fraction_positive(self, values: Sequence[float]) -> float:
        """Fraction of finite values that are strictly positive."""
        return _robustness.fraction_positive(values)

    # -- Feature primitives (Phase 2) + the OHLCV bridge ---------------------- #
    def _to_vendored_ohlcv(self, series: OHLCV) -> _vendored_ohlcv.OHLCV:
        """Bridge ``xsranker`` OHLCV -> the vendored OHLCV the frozen primitives expect.

        Load-bearing seam (tested as a gate-zero-class check): timestamps become
        **IST-localized** python datetimes so the vendored ``gap``'s ``.date()``
        day-grouping falls on the correct IST calendar boundary; O/H/L/C pass through
        as float64; and int volume becomes float64 (the vendored type's dtype). A
        timezone slip or wrong day-open bar here silently corrupts the signal.
        """
        naive_utc = series.timestamp.astype("datetime64[us]").astype(object)
        stamps = tuple(d.replace(tzinfo=UTC).astimezone(_IST) for d in naive_utc)
        return _vendored_ohlcv.OHLCV(
            timestamps=stamps,
            open=series.open.astype(np.float64),
            high=series.high.astype(np.float64),
            low=series.low.astype(np.float64),
            close=series.close.astype(np.float64),
            volume=series.volume.astype(np.float64),
        )

    def gap(self, series: OHLCV) -> FloatArray:
        """Per-bar overnight gap ``(day_open - prior_close)/prior_close`` (frozen `gap`)."""
        result: FloatArray = _indicators.gap(self._to_vendored_ohlcv(series))
        return result

    def atr(self, series: OHLCV, period: int) -> FloatArray:
        """ATR over ``period`` bars via the frozen `atr` (talib.ATR)."""
        result: FloatArray = _indicators.atr(self._to_vendored_ohlcv(series), period)
        return result

    def cross_sectional_rank(
        self, values_by_symbol: dict[str, FloatArray]
    ) -> dict[str, FloatArray]:
        """Point-in-time cross-sectional rank in [0,1] per timestamp (frozen primitive)."""
        result: dict[str, FloatArray] = _indicators.cross_sectional_rank(values_by_symbol)
        return result
