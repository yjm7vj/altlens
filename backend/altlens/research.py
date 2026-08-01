from __future__ import annotations

from decimal import Decimal

from altlens.analytics import calculate_fund_metrics
from altlens.demo_data import (
    DemoFund,
    get_demo_funds,
    get_demo_sources,
)
from altlens.schemas import (
    FundMetricSummary,
    FundSummary,
    ResearchBrief,
    ResearchBriefSection,
    SourceReferenceOut,
)


def generate_demo_research_brief(question: str, limit: int = 3) -> ResearchBrief:
    funds = list(get_demo_funds())[:limit]

    if not funds:
        return ResearchBrief(
            question=question,
            summary="No demo funds were selected for this brief.",
            data_quality_notes=["No metrics were calculated because no funds were selected."],
        )

    metrics = {fund.id: calculate_fund_metrics(fund.id) for fund in funds}
    ranked_funds = sorted(
        funds,
        key=lambda fund: metrics[fund.id].moic or Decimal("0"),
        reverse=True,
    )
    top_fund = ranked_funds[0]

    return ResearchBrief(
        question=question,
        summary=(
            f"{top_fund.name} currently screens strongest in the illustrative "
            "demo set by MOIC. Treat this as workflow validation, not an "
            "audited performance conclusion."
        ),
        funds=[_to_fund_summary(fund) for fund in funds],
        metrics=metrics,
        sections=[
            ResearchBriefSection(
                title="Performance Snapshot",
                body=_build_performance_snapshot(ranked_funds, metrics),
            ),
            ResearchBriefSection(
                title="Data Quality",
                body=(
                    "All included fund records are marked illustrative so the "
                    "brief can test the product flow without overstating data "
                    "confidence."
                ),
            ),
        ],
        sources=[
            SourceReferenceOut(
                source_name=source.source_name,
                source_url=source.source_url,
                field_name=source.field_name,
                confidence=source.confidence,
                data_status=source.data_status,
                notes=source.notes,
            )
            for source in get_demo_sources({fund.id for fund in funds})
        ],
        assumptions=[
            "Demo fund profiles and cash flows are synthetic.",
            "Metrics are calculated from seed cash flows using the backend metric layer.",
            "Illustrative data must be replaced with verified sources before external use.",
        ],
        data_quality_notes=[
            "Every current seed source is low-confidence and illustrative.",
            "Do not present generated demo briefs as investment advice.",
        ],
    )


def _to_fund_summary(fund: DemoFund) -> FundSummary:
    return FundSummary(
        id=fund.id,
        name=fund.name,
        manager_name=fund.manager_name,
        vintage_year=fund.vintage_year,
        fund_size_usd=fund.fund_size_usd,
        strategy=fund.strategy,
        geography=fund.geography,
        data_quality=fund.data_quality,
    )


def _build_performance_snapshot(
    funds: list[DemoFund], metrics: dict[int, FundMetricSummary]
) -> str:
    rows = []

    for fund in funds:
        metric = metrics[fund.id]
        rows.append(f"{fund.name}: {metric.moic}x MOIC, {metric.irr} IRR")

    return " | ".join(rows)
