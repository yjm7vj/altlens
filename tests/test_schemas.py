from decimal import Decimal

from altlens.schemas import (
    FundMetricSummary,
    FundSummary,
    ResearchBrief,
    ResearchBriefSection,
    SourceReferenceOut,
)


def test_research_brief_groups_metrics_sources_and_assumptions():
    brief = ResearchBrief(
        question="Compare 2018 VC funds",
        summary="Illustrative comparison of available fund data.",
        funds=[
            FundSummary(
                id=1,
                name="Example Ventures I",
                manager_name="Example Capital",
                vintage_year=2018,
                fund_size_usd=Decimal("250000000"),
            )
        ],
        metrics={1: FundMetricSummary(irr=Decimal("0.153"), moic=Decimal("2.0"))},
        sections=[
            ResearchBriefSection(
                title="Performance",
                body="Example Ventures I shows stronger MOIC than the peer set.",
            )
        ],
        sources=[
            SourceReferenceOut(
                source_name="Demo seed data",
                field_name="moic",
                confidence="low",
                data_status="illustrative",
            )
        ],
        assumptions=["Demo figures are illustrative until verified source data is added."],
        data_quality_notes=["Do not present illustrative figures as audited returns."],
    )

    assert brief.metrics[1].moic == Decimal("2.0")
    assert brief.sources[0].data_status == "illustrative"
    assert "illustrative" in brief.assumptions[0]
