"""Deterministic research-brief assembly.

Briefs are built from the approved analytics functions, not from a model.
The AI layer's job is to choose which brief to build and how to narrate it;
every number in the output comes from this module.
"""

from __future__ import annotations

from decimal import Decimal

from altlens.analytics import (
    calculate_fund_metrics,
    find_fund,
    get_sector_exposure,
    get_vintage_year_summary,
    list_sources,
)
from altlens.demo_data import DemoFund, get_demo_funds
from altlens.schemas import (
    BriefChart,
    BriefTable,
    FundMetricSummary,
    FundSummary,
    ResearchBrief,
    ResearchBriefSection,
)

STANDARD_ASSUMPTIONS: tuple[str, ...] = (
    "Demo fund profiles and cash flows are synthetic.",
    "Metrics are calculated from seed cash flows using the backend metric layer.",
    "Unrealized NAV is treated as a terminal distribution when solving IRR.",
    "Illustrative data must be replaced with verified sources before external use.",
)

STANDARD_DATA_QUALITY_NOTES: tuple[str, ...] = (
    "Every current seed source is low-confidence and illustrative.",
    "NAV marks are unaudited and drive both MOIC and IRR.",
    "Do not present generated demo briefs as investment advice.",
)


def generate_research_brief(
    question: str,
    fund_names: list[str] | None = None,
    vintage_year: int | None = None,
    limit: int = 5,
) -> ResearchBrief:
    """Build a structured brief for a question over a selected fund set."""
    funds = _select_funds(fund_names=fund_names, vintage_year=vintage_year, limit=limit)

    if not funds:
        return ResearchBrief(
            question=question,
            summary="No demo funds were selected for this brief.",
            assumptions=list(STANDARD_ASSUMPTIONS),
            data_quality_notes=[
                "No metrics were calculated because no funds were selected.",
                *STANDARD_DATA_QUALITY_NOTES,
            ],
            follow_up_questions=[
                "Which vintage years should this brief cover?",
                "Should the comparison be limited to a single strategy?",
            ],
        )

    metrics = {fund.id: calculate_fund_metrics(fund.id) for fund in funds}
    ranked_funds = sorted(
        funds,
        key=lambda fund: metrics[fund.id].moic or Decimal("0"),
        reverse=True,
    )
    top_fund = ranked_funds[0]
    weakest_fund = ranked_funds[-1]

    return ResearchBrief(
        question=question,
        summary=_build_summary(top_fund, weakest_fund, metrics, len(funds)),
        funds=[_to_fund_summary(fund) for fund in funds],
        metrics=metrics,
        sections=_build_sections(ranked_funds, metrics),
        tables=[_build_metric_table(ranked_funds, metrics)],
        charts=_build_charts(ranked_funds, metrics),
        sources=list_sources({fund.id for fund in funds}),
        assumptions=list(STANDARD_ASSUMPTIONS),
        data_quality_notes=list(STANDARD_DATA_QUALITY_NOTES),
        follow_up_questions=_build_follow_ups(ranked_funds),
    )


def generate_demo_research_brief(question: str, limit: int = 3) -> ResearchBrief:
    """Backwards-compatible entry point over the first funds in the dataset."""
    return generate_research_brief(question, limit=limit)


def _select_funds(
    fund_names: list[str] | None,
    vintage_year: int | None,
    limit: int,
) -> list[DemoFund]:
    if limit < 1:
        return []

    if fund_names:
        resolved: list[DemoFund] = []
        seen: set[int] = set()

        for name in fund_names:
            fund = find_fund(name)

            if fund is not None and fund.id not in seen:
                seen.add(fund.id)
                resolved.append(fund)

        return resolved[:limit]

    funds = list(get_demo_funds())

    if vintage_year is not None:
        funds = [fund for fund in funds if fund.vintage_year == vintage_year]

    return funds[:limit]


def _build_summary(
    top_fund: DemoFund,
    weakest_fund: DemoFund,
    metrics: dict[int, FundMetricSummary],
    fund_count: int,
) -> str:
    top_metrics = metrics[top_fund.id]

    if fund_count == 1:
        return (
            f"{top_fund.name} ({top_fund.vintage_year} vintage) shows "
            f"{top_metrics.moic:.2f}x MOIC and {_as_percent(top_metrics.irr)} IRR on "
            "illustrative seed cash flows. Treat this as workflow validation, "
            "not an audited performance conclusion."
        )

    return (
        f"Across {fund_count} illustrative funds, {top_fund.name} screens "
        f"strongest by MOIC at {top_metrics.moic:.2f}x "
        f"({_as_percent(top_metrics.irr)} IRR), while {weakest_fund.name} "
        f"trails at {metrics[weakest_fund.id].moic:.2f}x. Treat this as workflow "
        "validation, not an audited performance conclusion."
    )


def _build_sections(
    ranked_funds: list[DemoFund], metrics: dict[int, FundMetricSummary]
) -> list[ResearchBriefSection]:
    vintage_years = sorted({fund.vintage_year for fund in ranked_funds})
    vintage_summaries = [
        summary
        for summary in get_vintage_year_summary()
        if summary.vintage_year in vintage_years
    ]

    sections = [
        ResearchBriefSection(
            title="Performance Snapshot",
            body=_build_performance_snapshot(ranked_funds, metrics),
        ),
        ResearchBriefSection(
            title="Realized vs Unrealized",
            body=_build_realization_body(ranked_funds, metrics),
        ),
    ]

    if vintage_summaries:
        sections.append(
            ResearchBriefSection(
                title="Vintage Context",
                body=" | ".join(
                    f"{summary.vintage_year}: {summary.fund_count} fund(s), "
                    f"median MOIC {summary.median_moic:.2f}x, median IRR "
                    f"{_as_percent(summary.median_irr)}"
                    for summary in vintage_summaries
                ),
            )
        )

    exposures = get_sector_exposure([fund.name for fund in ranked_funds])

    if exposures:
        sections.append(
            ResearchBriefSection(
                title="Sector Exposure",
                body=" | ".join(
                    f"{exposure.sector}: "
                    f"{_as_percent(exposure.share_of_value)} of portfolio value "
                    f"across {exposure.company_count} company(ies)"
                    for exposure in exposures[:5]
                ),
            )
        )

    sections.append(
        ResearchBriefSection(
            title="Data Quality",
            body=(
                "All included fund records are marked illustrative so the "
                "brief can test the product flow without overstating data "
                "confidence. IRR figures incorporate unaudited NAV marks."
            ),
        )
    )

    return sections


def _build_performance_snapshot(
    funds: list[DemoFund], metrics: dict[int, FundMetricSummary]
) -> str:
    rows = []

    for fund in funds:
        metric = metrics[fund.id]
        rows.append(
            f"{fund.name}: {metric.moic:.2f}x MOIC, "
            f"{_as_percent(metric.irr)} IRR"
        )

    return " | ".join(rows)


def _build_realization_body(
    funds: list[DemoFund], metrics: dict[int, FundMetricSummary]
) -> str:
    rows = []

    for fund in funds:
        metric = metrics[fund.id]
        rows.append(
            f"{fund.name}: {metric.dpi:.2f}x realized (DPI), "
            f"{metric.rvpi:.2f}x still held at NAV (RVPI)"
        )

    return " | ".join(rows)


def _build_metric_table(
    funds: list[DemoFund], metrics: dict[int, FundMetricSummary]
) -> BriefTable:
    return BriefTable(
        title="Fund metrics",
        columns=["Fund", "Vintage", "IRR", "MOIC", "DPI", "RVPI"],
        rows=[
            [
                fund.name,
                str(fund.vintage_year),
                _as_percent(metrics[fund.id].irr),
                f"{metrics[fund.id].moic:.2f}x",
                f"{metrics[fund.id].dpi:.2f}x",
                f"{metrics[fund.id].rvpi:.2f}x",
            ]
            for fund in funds
        ],
    )


def _build_charts(
    funds: list[DemoFund], metrics: dict[int, FundMetricSummary]
) -> list[BriefChart]:
    charts = [
        BriefChart(
            title="IRR and MOIC by fund",
            chart_type="bar",
            x_key="label",
            series=["irr_pct", "moic"],
            data=[
                {
                    "label": fund.name,
                    "irr_pct": float((metrics[fund.id].irr or Decimal("0")) * 100),
                    "moic": float(metrics[fund.id].moic or Decimal("0")),
                }
                for fund in funds
            ],
        ),
        BriefChart(
            title="Realized vs unrealized value",
            chart_type="stacked_bar",
            x_key="label",
            series=["dpi", "rvpi"],
            data=[
                {
                    "label": fund.name,
                    "dpi": float(metrics[fund.id].dpi or Decimal("0")),
                    "rvpi": float(metrics[fund.id].rvpi or Decimal("0")),
                }
                for fund in funds
            ],
        ),
    ]

    exposures = get_sector_exposure([fund.name for fund in funds])

    if exposures:
        charts.append(
            BriefChart(
                title="Sector exposure by current value",
                chart_type="pie",
                x_key="label",
                series=["value"],
                data=[
                    {
                        "label": exposure.sector,
                        "value": float(exposure.current_value_usd),
                    }
                    for exposure in exposures
                ],
            )
        )

    return charts


def _build_follow_ups(funds: list[DemoFund]) -> list[str]:
    top = funds[0]

    follow_ups = [
        f"What drives {top.name}'s MOIC at the portfolio-company level?",
        "Which of these funds has the weakest DPI relative to its MOIC?",
        "How do these funds compare against their own vintage-year cohort?",
    ]

    if len(funds) > 1:
        follow_ups.append(
            f"Compare {funds[0].name} and {funds[-1].name} on sector exposure."
        )

    return follow_ups


def _to_fund_summary(fund: DemoFund) -> FundSummary:
    return FundSummary(
        id=fund.id,
        name=fund.name,
        manager_name=fund.manager_name,
        asset_class=fund.asset_class,
        vintage_year=fund.vintage_year,
        fund_size_usd=fund.fund_size_usd,
        strategy=fund.strategy,
        geography=fund.geography,
        description=fund.description or None,
        data_quality=fund.data_quality,
    )


def _as_percent(value: Decimal | None) -> str:
    if value is None:
        return "n/a"

    return f"{value * 100:.1f}%"
