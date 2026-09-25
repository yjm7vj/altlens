"""AltLens REST API.

Serves the illustrative demo dataset and the constrained research agent.
Nothing here requires a database or a model API key, so the whole product
runs locally with `uvicorn altlens.main:app --reload`.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from altlens import ai_tools, analytics, database
from altlens.ai_agent import answer_question
from altlens.config import settings
from altlens.providers import ProviderError, list_providers
from altlens.research import generate_research_brief
from altlens.schemas import (
    AIQueryRequest,
    AIQueryResponse,
    CapitalTimeline,
    FundDetail,
    FundMetricSummary,
    FundPerformanceSeries,
    FundSummary,
    FundWithMetricsOut,
    MethodologyNote,
    ProviderInfo,
    ResearchBrief,
    SectorExposure,
    SourceReferenceOut,
    ToolDescription,
    VintageYearSummary,
)

DATA_DISCLAIMER = (
    "AltLens is seeded with illustrative demo data based on the shape of "
    "public private-market reporting. Figures are not verified fund "
    "performance and must not be used as investment advice."
)

app = FastAPI(
    title="AltLens API",
    version="1.0.0",
    description=(
        "Alternative-investment research API for AIA. Fund profiles, "
        "cash-flow based metrics, and a constrained research agent. "
        + DATA_DISCLAIMER
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _to_out(item: analytics.FundWithMetrics) -> FundWithMetricsOut:
    return FundWithMetricsOut(fund=item.fund, metrics=item.metrics)


@app.get("/api/health", tags=["meta"])
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "fund_count": len(analytics.list_funds()),
        "data_source": "illustrative_demo",
        "database_configured": database.is_configured(),
        "disclaimer": DATA_DISCLAIMER,
    }


@app.get("/api/funds", response_model=list[FundSummary], tags=["funds"])
def list_funds(
    asset_class: str | None = None,
    vintage_year: int | None = None,
    strategy_contains: str | None = None,
    manager_name: str | None = None,
) -> list[FundSummary]:
    return analytics.list_funds(
        asset_class=asset_class,
        vintage_year=vintage_year,
        strategy_contains=strategy_contains,
        manager_name=manager_name,
    )


@app.get(
    "/api/funds/with-metrics",
    response_model=list[FundWithMetricsOut],
    tags=["funds"],
)
def list_funds_with_metrics(
    vintage_year: int | None = None,
) -> list[FundWithMetricsOut]:
    """Fund list joined with computed metrics — what the dashboard table uses."""
    funds = analytics.list_funds(vintage_year=vintage_year)

    return [
        FundWithMetricsOut(
            fund=fund, metrics=analytics.calculate_fund_metrics(fund.id)
        )
        for fund in funds
    ]


@app.get("/api/funds/{fund_id}", response_model=FundDetail, tags=["funds"])
def get_fund(fund_id: int) -> FundDetail:
    detail = analytics.get_fund_detail(fund_id)

    if detail is None:
        raise HTTPException(status_code=404, detail=f"Fund {fund_id} not found")

    return detail


@app.get(
    "/api/funds/{fund_id}/performance",
    response_model=FundPerformanceSeries,
    tags=["funds"],
)
def get_fund_performance(fund_id: int) -> FundPerformanceSeries:
    series = analytics.get_fund_performance(fund_id)

    if series is None:
        raise HTTPException(status_code=404, detail=f"Fund {fund_id} not found")

    return series


@app.get(
    "/api/funds/{fund_id}/metrics",
    response_model=FundMetricSummary,
    tags=["metrics"],
)
def get_fund_metrics(fund_id: int) -> FundMetricSummary:
    if not analytics.fund_exists(fund_id):
        raise HTTPException(status_code=404, detail=f"Fund {fund_id} not found")

    return analytics.calculate_fund_metrics(fund_id)


@app.get(
    "/api/funds/{fund_id}/sources",
    response_model=list[SourceReferenceOut],
    tags=["funds"],
)
def get_fund_sources(fund_id: int) -> list[SourceReferenceOut]:
    if not analytics.fund_exists(fund_id):
        raise HTTPException(status_code=404, detail=f"Fund {fund_id} not found")

    return analytics.list_sources({fund_id})


@app.get(
    "/api/metrics/top",
    response_model=list[FundWithMetricsOut],
    tags=["metrics"],
)
def top_performers(
    metric: str = Query(default="moic"),
    limit: int = Query(default=5, ge=1, le=50),
) -> list[FundWithMetricsOut]:
    try:
        performers = analytics.get_top_performers(metric=metric, limit=limit)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return [_to_out(item) for item in performers]


@app.get(
    "/api/metrics/capital-timeline",
    response_model=CapitalTimeline,
    tags=["metrics"],
)
def capital_timeline(
    fund_names: list[str] | None = Query(default=None),
) -> CapitalTimeline:
    """Cumulative capital called versus returned — the J-curve."""
    return analytics.get_capital_timeline(fund_names)


@app.get(
    "/api/metrics/vintages",
    response_model=list[VintageYearSummary],
    tags=["metrics"],
)
def vintage_summary(vintage_year: int | None = None) -> list[VintageYearSummary]:
    return analytics.get_vintage_year_summary(vintage_year=vintage_year)


@app.get(
    "/api/metrics/sectors",
    response_model=list[SectorExposure],
    tags=["metrics"],
)
def sector_exposure(
    fund_names: list[str] | None = Query(default=None),
) -> list[SectorExposure]:
    return analytics.get_sector_exposure(fund_names)


@app.get(
    "/api/metrics/methodology/{metric}",
    response_model=MethodologyNote,
    tags=["metrics"],
)
def metric_methodology(metric: str) -> MethodologyNote:
    note = analytics.explain_metric_methodology(metric)

    if note is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No methodology note for '{metric}'. Documented metrics: "
                + ", ".join(sorted(analytics.METHODOLOGY_NOTES))
            ),
        )

    return note


@app.get("/api/sources", response_model=list[SourceReferenceOut], tags=["sources"])
def all_sources() -> list[SourceReferenceOut]:
    return analytics.list_sources()


@app.post("/api/research/brief", response_model=ResearchBrief, tags=["research"])
def research_brief(
    question: str = Query(min_length=1, max_length=1000),
    fund_names: list[str] | None = Query(default=None),
    vintage_year: int | None = None,
    limit: int = Query(default=5, ge=0, le=25),
) -> ResearchBrief:
    return generate_research_brief(
        question=question,
        fund_names=fund_names,
        vintage_year=vintage_year,
        limit=limit,
    )


@app.post("/api/ai/query", response_model=AIQueryResponse, tags=["ai"])
def ai_query(request: AIQueryRequest) -> AIQueryResponse:
    try:
        return answer_question(
            question=request.question,
            provider_name=request.provider,
            model=request.model,
        )
    except ProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/api/ai/tools", response_model=list[ToolDescription], tags=["ai"])
def ai_tool_catalog() -> list[ToolDescription]:
    """The complete set of tools the agent may call. Nothing else is reachable."""
    return ai_tools.describe_tools()


@app.get("/api/ai/providers", response_model=list[ProviderInfo], tags=["ai"])
def ai_providers() -> list[ProviderInfo]:
    return list_providers()
