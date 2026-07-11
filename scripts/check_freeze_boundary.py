"""Freeze boundary — only the HarnessAdapter may import ``lab.*`` (Deep Dive 03).

Scans new-program source under ``src/xsranker`` and fails if any module other than
``src/xsranker/harness/adapter.py`` imports the vendored ``lab`` package. This is
what makes the freeze enforceable: all composition of the frozen harness routes
through one stable, golden-master-reverified surface. Tests are intentionally out
of scope — the verification harness must reach vendored internals directly.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "xsranker"
ADAPTER = (SRC / "harness" / "adapter.py").resolve()

# `import lab`, `import lab.x [as y]`, `from lab import …`, `from lab.x import …`
_LAB_IMPORT = re.compile(
    r"^\s*(?:import\s+lab(?:\.|\s|$)|from\s+lab(?:\.|\s+import))", re.MULTILINE
)


def check(src_dir: Path = SRC, adapter: Path = ADAPTER) -> list[str]:
    """Return boundary violations (empty == only the adapter imports ``lab.*``)."""
    problems: list[str] = []
    for path in sorted(src_dir.rglob("*.py")):
        if path.resolve() == adapter.resolve():
            continue
        if _LAB_IMPORT.search(path.read_text(encoding="utf-8")):
            problems.append(f"{path.as_posix()} imports lab.* outside the adapter")
    return problems


def main() -> int:
    """CLI entry: print status and exit nonzero on any violation."""
    problems = check()
    if problems:
        print("FREEZE BOUNDARY VIOLATION (only src/xsranker/harness/adapter.py may import lab.*):")
        for p in problems:
            print("  -", p)
        return 1
    print("freeze boundary intact: no lab.* import outside the adapter")
    return 0


if __name__ == "__main__":
    sys.exit(main())
