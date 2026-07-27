from __future__ import annotations

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
    data_quality: str = "illustrative"


class FundMetricSummary(BaseModel):
    irr: Decimal | None = None
    moic: Decimal | None = None
    tvpi: Decimal | None = None
    dpi: Decimal | None = None


class SourceReferenceOut(BaseModel):
    source_name: str
    source_url: str | None = None
    field_name: str | None = None
    confidence: str = "low"
    data_status: str = "illustrative"
    notes: str | None = None


class ResearchBriefSection(BaseModel):
    title: str
    body: str


class ResearchBrief(BaseModel):
    question: str
    summary: str
    funds: list[FundSummary] = Field(default_factory=list)
    metrics: dict[int, FundMetricSummary] = Field(default_factory=dict)
    sections: list[ResearchBriefSection] = Field(default_factory=list)
    sources: list[SourceReferenceOut] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    data_quality_notes: list[str] = Field(default_factory=list)
