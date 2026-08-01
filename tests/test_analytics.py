import pytest

from altlens.analytics import (
    compare_funds,
    get_fund_profile,
    get_top_performers,
    list_funds,
)


def test_list_funds_filters_by_vintage_year():
    funds = list_funds(vintage_year=2019)

    assert len(funds) == 1
    assert funds[0].name == "Frontier Seed Partners II"


def test_get_fund_profile_is_case_insensitive_and_includes_metrics():
    profile = get_fund_profile("altlens ventures i")

    assert profile is not None
    assert profile.fund.name == "AltLens Ventures I"
    assert profile.metrics.moic is not None


def test_get_top_performers_sorts_by_requested_metric():
    performers = get_top_performers(metric="moic", limit=2)

    assert len(performers) == 2
    assert performers[0].metrics.moic >= performers[1].metrics.moic


def test_get_top_performers_rejects_unknown_metric():
    with pytest.raises(ValueError, match="metric must be"):
        get_top_performers(metric="dpi")


def test_compare_funds_returns_only_requested_funds():
    comparison = compare_funds(["AltLens Ventures I", "Summit Growth VC III"])

    assert {item.fund.name for item in comparison} == {
        "AltLens Ventures I",
        "Summit Growth VC III",
    }
