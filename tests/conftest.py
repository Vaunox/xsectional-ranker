"""Shared pytest configuration for the verification gate.

Pin BLAS/OpenMP threading to a single thread BEFORE numpy/scipy import anywhere,
so golden-master reductions are order-deterministic and bit-for-bit reconciliation
does not trip on a ~1e-13 thread-reduction difference (Deep Dive 03, Check 4).
Best-effort at import time; CI also sets OMP_NUM_THREADS=1 in the job env.
"""

from __future__ import annotations

import os

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_var, "1")
