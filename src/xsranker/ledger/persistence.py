"""Durable, fail-closed effective-N trial ledger (R2 fix — Inviolable Rule 4).

The vendored :class:`TrialLedger` persists per-trial return streams to a directory, but
the candidate-#1 smoke run wrote them to an **ephemeral** dir that was never committed — so
the streams were lost and only a number (effective-N ≈ 5.98) survived, as prose in
``RESEARCH_FINDINGS.md``. That silently broke Rule 4's cross-session guarantee: every future
candidate would deflate its DSR against an unreconstructable, under-counted trial history.
Found and fixed 2026-07-12, the **same class of defect as the null-construction bug** — a
silent hole that would quietly rot the DSR bar across candidates.

This layer is NEW ``xsranker`` code wrapping the FROZEN vendored ``TrialLedger`` (never
editing it). It adds:

* a **durable, in-repo, committed** ledger directory (config ``ledger.dir``);
* a **manifest** declaring which prior candidates' trial streams MUST be present;
* a **fail-closed** integrity check — the gate raises :class:`LedgerIntegrityError` if any
  required stream is missing or empty, so effective-N is never silently undercounted.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml

from xsranker.harness.adapter import TrialLedger


class LedgerIntegrityError(RuntimeError):
    """A required prior-candidate trial stream is missing/empty — refuse to gate.

    Raised by :func:`verify_ledger_integrity` rather than letting the gate proceed on an
    under-counted trial history and silently deflate a future candidate's DSR against a hole.
    """


@dataclass(frozen=True, slots=True)
class LedgerManifest:
    """Which prior candidates' trial-ids MUST be present in the durable ledger."""

    #: candidate name -> the trial-ids that candidate contributed (all required present).
    candidates: Mapping[str, tuple[str, ...]]

    @property
    def required_trial_ids(self) -> tuple[str, ...]:
        """Every trial-id that must be present, across all declared candidates."""
        return tuple(tid for ids in self.candidates.values() for tid in ids)


def load_manifest(path: Path) -> LedgerManifest:
    """Load the ledger manifest (a missing or empty file → an empty manifest).

    Raises:
        ValueError: if the file exists but ``candidates`` is not a mapping.
    """
    if not path.exists():
        return LedgerManifest(candidates={})
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cands = data.get("candidates") or {}
    if not isinstance(cands, Mapping):
        raise ValueError(f"{path}: 'candidates' must be a mapping of name -> [trial_ids]")
    return LedgerManifest(
        candidates={str(k): tuple(str(t) for t in (v or ())) for k, v in cands.items()}
    )


def write_manifest(path: Path, manifest: LedgerManifest) -> None:
    """Persist ``manifest`` to ``path`` as YAML (used by the regeneration script)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"candidates": {k: list(v) for k, v in sorted(manifest.candidates.items())}}
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")


def verify_ledger_integrity(ledger: TrialLedger, manifest: LedgerManifest) -> None:
    """Raise if any manifest-required trial stream is absent or empty (FAIL CLOSED).

    This is the guard that keeps effective-N honest across candidates: it refuses to let the
    gate proceed on an under-counted trial history rather than silently deflating a future
    candidate's DSR against a hole. An **empty** stream is treated as missing because the
    correlation-participation-ratio drops zero-length streams — so a present-but-empty trial
    would also silently undercount.

    Raises:
        LedgerIntegrityError: if a required trial-id is missing, or present but empty.
    """
    by_id = {r.trial_id: r for r in ledger.trials()}
    missing = [t for t in manifest.required_trial_ids if t not in by_id]
    empty = [t for t in manifest.required_trial_ids if t in by_id and len(by_id[t].returns) == 0]
    if missing or empty:
        detail = f"{len(missing)} MISSING {missing[:8]}"
        if empty:
            detail += f"; {len(empty)} EMPTY {empty[:8]}"
        raise LedgerIntegrityError(
            f"durable ledger fails closed: required prior-candidate stream(s) {detail} "
            f"(ledger dir has {len(by_id)} trial(s)) — refusing to gate; effective-N would "
            f"be silently undercounted (Inviolable Rule 4). Run scripts/regenerate_ledger.py."
        )


def open_persistent_ledger(dir_: Path, manifest_path: Path) -> tuple[TrialLedger, LedgerManifest]:
    """Open the durable ledger and its manifest (does NOT verify — call the guard first)."""
    return TrialLedger(dir_), load_manifest(manifest_path)


def arm_trial_id(candidate: str, arm: str, window: int, *, cost: str | None = None) -> str:
    """Deterministic, filesystem-safe trial-id so the manifest can name a persisted stream.

    ``cand1__A-Z__30`` for a base arm; ``cand1__A-Z__30__fees+ar`` for a cost-realism re-run.
    Uses ``__`` (not ``:``) as the separator because the vendored ledger writes each stream
    to ``<trial_id>.json`` and ``:`` is an invalid filename character on Windows.
    """
    base = f"{candidate}__{arm}__{window}"
    return f"{base}__{cost}" if cost else base
