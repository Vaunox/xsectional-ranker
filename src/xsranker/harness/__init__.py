"""The adapter boundary onto the frozen vendored statistical harness.

:class:`xsranker.harness.adapter.HarnessAdapter` is the ONLY module in the
program permitted to import ``lab.*`` (the vendored predecessor code under
``src/vendored``). Everything else composes the harness through this stable
surface, so the freeze is enforceable and a future harness version bump is a
single, golden-master-reverified change (Deep Dive 03).
"""

from __future__ import annotations
