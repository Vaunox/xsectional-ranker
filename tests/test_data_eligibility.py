"""Tests for the dual eligibility masks — the asymmetric short-ban logic (teeth)."""

from __future__ import annotations

from xsranker.data.universe.eligibility import (
    SecurityStatus,
    Series,
    long_eligible,
    short_eligible,
)


def _status(**kw: object) -> SecurityStatus:
    base: dict[str, object] = {
        "symbol": "X",
        "series": Series.EQ,
        "asm": False,
        "gsm": False,
        "shortable": True,
    }
    base.update(kw)
    return SecurityStatus(**base)  # type: ignore[arg-type]


def test_clean_eq_passes_both() -> None:
    s = _status()
    assert long_eligible(s) and short_eligible(s)


def test_t2t_series_blocks_both() -> None:
    for series in (Series.BE, Series.BZ):
        s = _status(series=series)
        assert not long_eligible(s)  # T2T cannot be squared intraday
        assert not short_eligible(s)


def test_asm_blocks_short_not_long() -> None:
    # THE asymmetry: an ASM name is un-shortable but a valid 100%-cash long
    s = _status(asm=True)
    assert long_eligible(s)
    assert not short_eligible(s)


def test_gsm_blocks_short_not_long() -> None:
    s = _status(gsm=True)
    assert long_eligible(s)
    assert not short_eligible(s)


def test_margin_proxy_blocks_short_not_long() -> None:
    # 100% margin / 1x leverage proxy => not shortable, still long-eligible
    s = _status(shortable=False)
    assert long_eligible(s)
    assert not short_eligible(s)
