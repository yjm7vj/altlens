import pytest

from altlens.analytics import (
    calculate_fund_metrics,
    compare_funds,
    explain_metric_methodology,
    find_fund,
    get_capital_timeline,
    get_fund_detail,
    get_fund_performance,
    get_fund_profile,
    get_sector_exposure,
    get_top_performers,
    get_vintage_year_summary,
    list_funds,
)


def test_list_funds_filters_by_vintage_year():
    funds = list_funds(vintage_year=2019)

    assert {fund.name for fund in funds} == {
        "Frontier Seed Partners II",
        "Northwind Deep Tech I",
    }


def test_list_funds_filters_by_strategy_and_manager():
    assert [fund.name for fund in list_funds(strategy_contains="climate")] == [
        "Atlas Climate Fund I"
    ]
    assert [fund.name for fund in list_funds(manager_name="pinnacle")] == [
        "Pinnacle Enterprise Fund IV"
    ]


def test_get_fund_profile_is_case_insensitive_and_includes_metrics():
    profile = get_fund_profile("altlens ventures i")

    assert profile is not None
    assert profile.fund.name == "AltLens Ventures I"
    assert profile.metrics.moic is not None


def test_find_fund_resolves_unambiguous_partial_names():
    assert find_fund("Frontier").name == "Frontier Seed Partners II"


def test_find_fund_rejects_ambiguous_partial_names():
    # Several funds contain "ventures", so a partial match must not guess.
    assert find_fund("ventures") is None


def test_get_top_performers_sorts_by_requested_metric():
    performers = get_top_performers(metric="moic", limit=2)

    assert len(performers) == 2
    assert performers[0].metrics.moic >= performers[1].metrics.moic


def test_get_top_performers_supports_realization_metrics():
    performers = get_top_performers(metric="dpi", limit=3)

    assert performers[0].metrics.dpi >= performers[-1].metrics.dpi


def test_get_top_performers_rejects_unknown_metric():
    with pytest.raises(ValueError, match="metric must be one of"):
        get_top_performers(metric="sharpe_ratio")


def test_compare_funds_returns_only_requested_funds():
    comparison = compare_funds(["AltLens Ventures I", "Summit Growth VC III"])

    assert {item.fund.name for item in comparison} == {
        "AltLens Ventures I",
        "Summit Growth VC III",
    }


def test_compare_funds_skips_unknown_names_without_failing():
    comparison = compare_funds(["AltLens Ventures I", "Nonexistent Fund"])

    assert [item.fund.name for item in comparison] == ["AltLens Ventures I"]


def test_fund_metrics_separate_realized_from_unrealized_value():
    metrics = calculate_fund_metrics(1)

    assert metrics.dpi is not None
    assert metrics.rvpi is not None
    # MOIC is total value, so it must account for both components.
    assert metrics.moic == pytest.approx(metrics.dpi + metrics.rvpi, abs=1e-4)


def test_young_fund_with_no_distributions_still_has_irr_from_nav():
    # Lattice Early Stage II has called capital but made no distributions.
    metrics = calculate_fund_metrics(10)

    assert metrics.dpi == 0
    assert metrics.rvpi > 0
    assert metrics.irr is not None and metrics.irr > 0


def test_get_fund_performance_returns_sorted_snapshots():
    series = get_fund_performance(1)

    dates = [point.snapshot_date for point in series.points]
    assert dates == sorted(dates)
    assert series.fund_name == "AltLens Ventures I"


def test_get_fund_detail_bundles_cash_flows_positions_and_sources():
    detail = get_fund_detail(2)

    assert detail is not None
    assert detail.cash_flows
    assert detail.positions
    assert detail.sources
    assert all(source.data_status == "illustrative" for source in detail.sources)


def test_get_fund_detail_returns_none_for_unknown_fund():
    assert get_fund_detail(9999) is None


def test_vintage_summary_groups_funds_by_year():
    summaries = get_vintage_year_summary()
    years = [summary.vintage_year for summary in summaries]

    assert years == sorted(years)
    assert sum(summary.fund_count for summary in summaries) == len(list_funds())


def test_vintage_summary_can_target_a_single_year():
    summaries = get_vintage_year_summary(vintage_year=2018)

    assert len(summaries) == 1
    assert summaries[0].fund_count == 2


def test_sector_exposure_shares_sum_to_one():
    exposures = get_sector_exposure()

    assert exposures
    total_share = sum(float(exposure.share_of_value) for exposure in exposures)
    assert total_share == pytest.approx(1.0, abs=0.001)


def test_sector_exposure_can_be_scoped_to_named_funds():
    exposures = get_sector_exposure(["Frontier Seed Partners II"])

    assert {exposure.sector for exposure in exposures} == {
        "AI Infrastructure",
        "Developer Tools",
    }


def test_capital_timeline_tracks_cumulative_flows_and_break_even():
    timeline = get_capital_timeline()

    assert timeline.points
    called = [point.cumulative_called_usd for point in timeline.points]
    distributed = [point.cumulative_distributed_usd for point in timeline.points]

    assert called == sorted(called)
    assert distributed == sorted(distributed)
    assert timeline.break_even_date is not None


def test_capital_timeline_for_a_single_fund_is_labelled_by_name():
    timeline = get_capital_timeline(["AltLens Ventures I"])

    assert timeline.label == "AltLens Ventures I"
    assert timeline.fund_count == 1


def test_methodology_notes_exist_for_every_rankable_metric():
    for metric in ("irr", "moic", "tvpi", "dpi", "rvpi"):
        note = explain_metric_methodology(metric)

        assert note is not None
        assert note.caveats


def test_methodology_lookup_returns_none_for_unknown_metric():
    assert explain_metric_methodology("sharpe_ratio") is None
