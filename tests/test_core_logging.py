"""Tests for structured logging: IST timestamps, correlation IDs, redaction."""

from __future__ import annotations

import io
import json

from xsranker.core.logging import (
    REDACTION_MASK,
    bind_correlation_id,
    clear_context,
    configure_logging,
    correlation_context,
    get_logger,
)


def _emit_json() -> dict[str, object]:
    stream = io.StringIO()
    configure_logging(level="INFO", renderer="json", stream=stream)
    with correlation_context("cid-123"):
        get_logger("test").info("event", api_key="super-secret", value=42)
    clear_context()
    record: dict[str, object] = json.loads(stream.getvalue().strip().splitlines()[-1])
    return record


def test_redacts_sensitive_keys() -> None:
    record = _emit_json()
    assert record["api_key"] == REDACTION_MASK
    assert record["value"] == 42  # non-sensitive fields untouched


def test_stamps_ist_timestamp() -> None:
    record = _emit_json()
    ts = str(record["timestamp"])
    # IST is UTC+05:30, so the ISO offset is present and positive.
    assert ts.endswith("+05:30")


def test_binds_correlation_id() -> None:
    record = _emit_json()
    assert record["correlation_id"] == "cid-123"


def test_bind_correlation_id_returns_generated_id() -> None:
    cid = bind_correlation_id()
    assert cid  # a non-empty generated id
    clear_context()
