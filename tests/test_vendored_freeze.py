"""Check 4 (determinism lock) + freeze-integrity (hash tripwire, boundary grep).

The tripwire and boundary checks are asserted intact AND proven to have teeth
(they catch an injected drift / an injected ``lab.*`` import). The determinism
lock pins the exact numeric stack the goldens were birthed against and proves the
seeded RNG path is reproducible and wired from config (Deep Dive 03).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import numpy as np
import scipy

from scripts.check_freeze_boundary import check as boundary_check
from scripts.check_vendored_hashes import MANIFEST, VENDORED_DIR
from scripts.check_vendored_hashes import check as hash_check
from xsranker.core.config import load_settings
from xsranker.harness.adapter import HarnessAdapter

# The EXACT pins the golden masters were birthed against (VENDORED_FROM.md, Check 4).
PINNED_PYTHON = (3, 11)
PINNED_NUMPY = "2.4.6"
PINNED_SCIPY = "1.17.1"


# --- freeze integrity -------------------------------------------------------- #
def test_vendored_hashes_intact() -> None:
    assert hash_check() == []


def test_freeze_boundary_intact() -> None:
    assert boundary_check() == []


def test_hash_tripwire_has_teeth(tmp_path: Path) -> None:
    """A one-byte edit to a frozen file must be caught by the tripwire."""
    shutil.copytree(VENDORED_DIR / "lab", tmp_path / "lab")
    shutil.copy(MANIFEST, tmp_path / "vendored_hashes.txt")
    victim = tmp_path / "lab" / "research" / "validation" / "sharpe.py"
    victim.write_bytes(victim.read_bytes() + b"\n# tampered\n")
    problems = hash_check(vendored_dir=tmp_path, manifest=tmp_path / "vendored_hashes.txt")
    assert any("HASH DRIFT" in p and "sharpe.py" in p for p in problems)


def test_freeze_boundary_has_teeth(tmp_path: Path) -> None:
    """A new module importing lab.* outside the adapter must be caught."""
    pkg = tmp_path / "xsranker"
    pkg.mkdir()
    (pkg / "rogue.py").write_text("from lab.research.validation import metrics\n", encoding="utf-8")
    problems = boundary_check(src_dir=pkg, adapter=pkg / "harness" / "adapter.py")
    assert any("rogue.py" in p for p in problems)


# --- determinism lock (Check 4) ---------------------------------------------- #
def test_numeric_stack_matches_the_pin() -> None:
    """Golden-master equality is only meaningful against the locked numeric stack."""
    assert (
        sys.version_info[:2] == PINNED_PYTHON
    ), f"python {sys.version_info[:2]} != {PINNED_PYTHON}"
    assert np.__version__ == PINNED_NUMPY, f"numpy {np.__version__} != {PINNED_NUMPY}"
    assert scipy.__version__ == PINNED_SCIPY, f"scipy {scipy.__version__} != {PINNED_SCIPY}"


def test_seeded_path_is_reproducible() -> None:
    """Two runs on the same seed produce identical output."""
    adapter = HarnessAdapter(load_settings())
    returns = [0.01, -0.02, 0.03, -0.01, 0.02, 0.0] * 12
    first = adapter.monte_carlo_sign_flip(returns, n_shuffles=400, seed=7)
    second = adapter.monte_carlo_sign_flip(returns, n_shuffles=400, seed=7)
    assert first == second


def test_master_seed_is_threaded_from_config() -> None:
    """The adapter's default seed is the config seed — not a hidden literal."""
    import lab.research.validation.robustness as rob  # test may reach vendored directly

    settings = load_settings()
    adapter = HarnessAdapter(settings)
    returns = [0.005, -0.01, 0.02, -0.003, 0.008, 0.0] * 12
    assert adapter.monte_carlo_sign_flip(returns, n_shuffles=400) == rob.monte_carlo_sign_flip(
        returns, n_shuffles=400, seed=settings.seed
    )
