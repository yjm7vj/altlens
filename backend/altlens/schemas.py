from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FundSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    manager_name: str | None = None
    asset_class: str = "venture_capital"
    vintage_year: int | None = None
    fund_size_usd: Decimal | None = None
    strategy: str | None = None
    geography: str | None = None
    description: str | None = None
    data_quality: str = "illustrative"


class FundMetricSummary(BaseModel):
    irr: Decimal | None = None
    moic: Decimal | None = None
    tvpi: Decimal | None = None
    dpi: Decimal | None = None
    rvpi: Decimal | None = None
    paid_in_usd: Decimal | None = None
    distributed_usd: Decimal | None = None
    residual_value_usd: Decimal | None = None


class SourceReferenceOut(BaseModel):
    source_name: str
    source_url: str | None = None
    field_name: str | None = None
    confidence: str = "low"
    data_status: str = "illustrative"
    notes: str | None = None


class FundWithMetricsOut(BaseModel):
    fund: FundSummary
    metrics: FundMetricSummary


class PerformancePoint(BaseModel):
    snapshot_date: date
    nav_usd: Decimal | None = None
    cumulative_distributions_usd: Decimal | None = None
    total_value_usd: Decimal | None = None


class FundPerformanceSeries(BaseModel):
    fund_id: int
    fund_name: str
    points: list[PerformancePoint] = Field(default_factory=list)


class CapitalTimelinePoint(BaseModel):
    """One step of the J-curve: capital called vs returned, plus NAV."""

    period_date: date
    cumulative_called_usd: Decimal
    cumulative_distributed_usd: Decimal
    nav_usd: Decimal | None = None
    total_value_usd: Decimal | None = None


class CapitalTimeline(BaseModel):
    label: str
    fund_count: int = 0
    break_even_date: date | None = None
    points: list[CapitalTimelinePoint] = Field(default_factory=list)


class CashFlowOut(BaseModel):
    event_date: date
    amount_usd: Decimal
    flow_type: str


class PortfolioPositionOut(BaseModel):
    fund_id: int
    company_name: str
    sector: str
    stage: str
    invested_usd: Decimal
    current_value_usd: Decimal
    status: str = "active"


class SectorExposure(BaseModel):
    sector: str
    invested_usd: Decimal
    current_value_usd: Decimal
    share_of_value: Decimal
    company_count: int


class VintageYearSummary(BaseModel):
    vintage_year: int
    fund_count: int
    median_irr: Decimal | None = None
    median_moic: Decimal | None = None
    total_fund_size_usd: Decimal | None = None
    fund_names: list[str] = Field(default_factory=list)


class FundDetail(BaseModel):
    fund: FundSummary
    metrics: FundMetricSummary
    performance: FundPerformanceSeries
    cash_flows: list[CashFlowOut] = Field(default_factory=list)
    positions: list[PortfolioPositionOut] = Field(default_factory=list)
    sources: list[SourceReferenceOut] = Field(default_factory=list)


class MethodologyNote(BaseModel):
    metric: str
    definition: str
    formula: str
    caveats: list[str] = Field(default_factory=list)


class BriefTable(BaseModel):
    title: str
    columns: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)


class BriefChart(BaseModel):
    title: str
    chart_type: str = "bar"
    x_key: str = "label"
    series: list[str] = Field(default_factory=list)
    data: list[dict[str, float | str | None]] = Field(default_factory=list)


class ResearchBriefSection(BaseModel):
    title: str
    body: str


class ResearchBrief(BaseModel):
    question: str
    summary: str
    funds: list[FundSummary] = Field(default_factory=list)
    metrics: dict[int, FundMetricSummary] = Field(default_factory=dict)
    sections: list[ResearchBriefSection] = Field(default_factory=list)
    tables: list[BriefTable] = Field(default_factory=list)
    charts: list[BriefChart] = Field(default_factory=list)
    sources: list[SourceReferenceOut] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    data_quality_notes: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)


class ToolCallRecord(BaseModel):
    """One approved backend tool the agent ran while answering."""

    tool_name: str
    arguments: dict[str, object] = Field(default_factory=dict)
    summary: str


class AIQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    provider: str | None = None
    model: str | None = None


class AIQueryResponse(BaseModel):
    question: str
    answer: str
    provider: str
    model: str | None = None
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    brief: ResearchBrief | None = None
    sources: list[SourceReferenceOut] = Field(default_factory=list)
    data_quality_notes: list[str] = Field(default_factory=list)


class ToolDescription(BaseModel):
    name: str
    description: str
    parameters: dict[str, object] = Field(default_factory=dict)


class ProviderInfo(BaseModel):
    name: str
    available: bool
    default_model: str | None = None
    notes: str | None = None
