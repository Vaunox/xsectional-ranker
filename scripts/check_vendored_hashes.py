"""Vendored-hash tripwire (Deep Dive 03) — fail if any frozen file drifts.

Recomputes the SHA-256 of every file under ``src/vendored/lab`` and compares it to
the recorded manifest ``src/vendored/vendored_hashes.txt``. Any drift — a silent
local edit to frozen code, a missing file, or an unrecorded addition — fails. Run
by pre-commit, by CI, and by ``tests/test_vendored_freeze.py``.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

VENDORED_DIR = Path(__file__).resolve().parents[1] / "src" / "vendored"
MANIFEST = VENDORED_DIR / "vendored_hashes.txt"


def parse_manifest(manifest: Path) -> dict[str, str]:
    """Parse a ``sha256sum``-format manifest into ``{relpath: sha256}``."""
    entries: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, path = line.split(None, 1)
        entries[path.lstrip("*")] = digest
    return entries


def check(vendored_dir: Path = VENDORED_DIR, manifest: Path = MANIFEST) -> list[str]:
    """Return drift descriptions (empty list == every frozen file matches)."""
    recorded = parse_manifest(manifest)
    present = {
        p.relative_to(vendored_dir).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(vendored_dir.rglob("*.py"))
    }
    problems: list[str] = []
    for rel, digest in recorded.items():
        if rel not in present:
            problems.append(f"missing frozen file: {rel}")
        elif present[rel] != digest:
            problems.append(
                f"HASH DRIFT: {rel} (recorded {digest[:12]}…, found {present[rel][:12]}…)"
            )
    for rel in present:
        if rel not in recorded:
            problems.append(f"unrecorded vendored file (add to manifest or remove): {rel}")
    return problems


def main() -> int:
    """CLI entry: print status and exit nonzero on any drift."""
    problems = check()
    if problems:
        print("VENDORED FREEZE VIOLATION (src/vendored is frozen; Deep Dive 03):")
        for p in problems:
            print("  -", p)
        return 1
    print(f"vendored freeze intact: {len(parse_manifest(MANIFEST))} files match recorded hashes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
