"""The fixed set of tools the AI layer is allowed to call.

The agent never writes SQL and never produces a number itself. It chooses a
tool from this registry, and the tool returns both a human-readable summary
and the structured data behind it, so any claim in an answer can be traced
back to a calculation.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from altlens import analytics
from altlens.research import generate_research_brief
from altlens.schemas import ResearchBrief, SourceReferenceOut, ToolDescription


@dataclass
class ToolResult:
    """What a tool hands back to the agent."""

    summary: str
    data: Any = None
    brief: ResearchBrief | None = None
    sources: list[SourceReferenceOut] = field(default_factory=list)
    fund_ids: set[int] = field(default_factory=set)


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    run: Callable[..., ToolResult]

    def describe(self) -> ToolDescription:
        return ToolDescription(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )


class ToolExecutionError(RuntimeError):
    """Raised when a tool is called with arguments it cannot honour."""


def _percent(value: Decimal | None) -> str:
    if value is None:
        return "n/a"

    return f"{value * 100:.1f}%"


def _multiple(value: Decimal | None) -> str:
    if value is None:
        return "n/a"

    return f"{value:.2f}x"


def _describe_fund_metrics(item: analytics.FundWithMetrics) -> str:
    return (
        f"{item.fund.name} ({item.fund.vintage_year} vintage, "
        f"{item.fund.manager_name}): IRR {_percent(item.metrics.irr)}, "
        f"MOIC {_multiple(item.metrics.moic)}, DPI {_multiple(item.metrics.dpi)}, "
        f"RVPI {_multiple(item.metrics.rvpi)}"
    )


def tool_list_funds(
    vintage_year: int | None = None,
    strategy_contains: str | None = None,
    manager_name: str | None = None,
) -> ToolResult:
    funds = analytics.list_funds(
        vintage_year=vintage_year,
        strategy_contains=strategy_contains,
        manager_name=manager_name,
    )

    if not funds:
        return ToolResult(
            summary="No funds in the dataset match those filters.",
            data=[],
        )

    lines = [
        f"{fund.name} ({fund.vintage_year} vintage, {fund.strategy}, "
        f"{fund.geography})"
        for fund in funds
    ]

    return ToolResult(
        summary=f"{len(funds)} fund(s) matched:\n" + "\n".join(lines),
        data=[fund.model_dump(mode="json") for fund in funds],
        fund_ids={fund.id for fund in funds},
    )


def tool_get_fund_profile(fund_name: str) -> ToolResult:
    profile = analytics.get_fund_profile(fund_name)

    if profile is None:
        raise ToolExecutionError(
            f"No fund named '{fund_name}' is in the AltLens dataset."
        )

    fund = profile.fund

    summary = (
        f"{fund.name} is a {fund.vintage_year} vintage "
        f"{fund.asset_class.replace('_', ' ')} fund managed by "
        f"{fund.manager_name}. Strategy: {fund.strategy}. Geography: "
        f"{fund.geography}. Fund size: ${fund.fund_size_usd:,.0f}. "
        f"{_describe_fund_metrics(profile)}"
    )

    return ToolResult(
        summary=summary,
        data={
            "fund": fund.model_dump(mode="json"),
            "metrics": profile.metrics.model_dump(mode="json"),
        },
        sources=analytics.list_sources({fund.id}),
        fund_ids={fund.id},
    )


def tool_get_fund_metrics(fund_name: str) -> ToolResult:
    profile = analytics.get_fund_profile(fund_name)

    if profile is None:
        raise ToolExecutionError(
            f"No fund named '{fund_name}' is in the AltLens dataset."
        )

    metrics = profile.metrics

    summary = (
        f"{profile.fund.name}: IRR {_percent(metrics.irr)}, "
        f"MOIC {_multiple(metrics.moic)}, DPI {_multiple(metrics.dpi)}, "
        f"RVPI {_multiple(metrics.rvpi)}. Paid in "
        f"${metrics.paid_in_usd:,.0f}, distributed "
        f"${metrics.distributed_usd:,.0f}, residual NAV "
        f"${metrics.residual_value_usd or 0:,.0f}."
    )

    return ToolResult(
        summary=summary,
        data=metrics.model_dump(mode="json"),
        sources=analytics.list_sources({profile.fund.id}),
        fund_ids={profile.fund.id},
    )


def tool_compare_funds(fund_names: list[str]) -> ToolResult:
    if not fund_names:
        raise ToolExecutionError("compare_funds needs at least one fund name.")

    compared = analytics.compare_funds(fund_names)

    if not compared:
        raise ToolExecutionError(
            "None of those fund names are in the AltLens dataset: "
            + ", ".join(fund_names)
        )

    missing = [
        name for name in fund_names if analytics.find_fund(name) is None
    ]

    lines = [_describe_fund_metrics(item) for item in compared]

    if missing:
        lines.append(
            "Not found in the dataset (excluded): " + ", ".join(missing)
        )

    return ToolResult(
        summary="\n".join(lines),
        data=[
            {
                "fund": item.fund.model_dump(mode="json"),
                "metrics": item.metrics.model_dump(mode="json"),
            }
            for item in compared
        ],
        sources=analytics.list_sources({item.fund.id for item in compared}),
        fund_ids={item.fund.id for item in compared},
    )


def tool_get_top_performers(metric: str = "moic", limit: int = 5) -> ToolResult:
    try:
        performers = analytics.get_top_performers(metric=metric, limit=limit)
    except ValueError as error:
        raise ToolExecutionError(str(error)) from error

    if not performers:
        return ToolResult(summary="No funds available to rank.", data=[])

    lines = [
        f"{position}. {_describe_fund_metrics(item)}"
        for position, item in enumerate(performers, start=1)
    ]

    return ToolResult(
        summary=f"Top {len(performers)} fund(s) by {metric.upper()}:\n"
        + "\n".join(lines),
        data=[
            {
                "fund": item.fund.model_dump(mode="json"),
                "metrics": item.metrics.model_dump(mode="json"),
            }
            for item in performers
        ],
        sources=analytics.list_sources({item.fund.id for item in performers}),
        fund_ids={item.fund.id for item in performers},
    )


def tool_get_vintage_year_summary(vintage_year: int | None = None) -> ToolResult:
    summaries = analytics.get_vintage_year_summary(vintage_year=vintage_year)

    if not summaries:
        raise ToolExecutionError(
            f"No funds with vintage year {vintage_year} are in the dataset."
        )

    lines = [
        f"{summary.vintage_year}: {summary.fund_count} fund(s), median IRR "
        f"{_percent(summary.median_irr)}, median MOIC "
        f"{_multiple(summary.median_moic)} "
        f"({', '.join(summary.fund_names)})"
        for summary in summaries
    ]

    return ToolResult(
        summary="Vintage-year cohorts:\n" + "\n".join(lines),
        data=[summary.model_dump(mode="json") for summary in summaries],
    )


def tool_get_sector_exposure(fund_names: list[str] | None = None) -> ToolResult:
    exposures = analytics.get_sector_exposure(fund_names)

    if not exposures:
        raise ToolExecutionError(
            "No portfolio-company exposure is recorded for those funds."
        )

    scope = ", ".join(fund_names) if fund_names else "the full demo portfolio"

    lines = [
        f"{exposure.sector}: {_percent(exposure.share_of_value)} of value "
        f"(${exposure.current_value_usd:,.0f} across "
        f"{exposure.company_count} company(ies))"
        for exposure in exposures
    ]

    return ToolResult(
        summary=f"Sector exposure for {scope}:\n" + "\n".join(lines),
        data=[exposure.model_dump(mode="json") for exposure in exposures],
    )


def tool_generate_research_brief(
    question: str,
    fund_names: list[str] | None = None,
    vintage_year: int | None = None,
    limit: int = 5,
) -> ToolResult:
    brief = generate_research_brief(
        question=question,
        fund_names=fund_names,
        vintage_year=vintage_year,
        limit=limit,
    )

    return ToolResult(
        summary=brief.summary,
        data=brief.model_dump(mode="json"),
        brief=brief,
        sources=brief.sources,
        fund_ids={fund.id for fund in brief.funds},
    )


def tool_explain_metric_methodology(metric: str) -> ToolResult:
    note = analytics.explain_metric_methodology(metric)

    if note is None:
        raise ToolExecutionError(
            f"AltLens does not document a metric called '{metric}'. "
            "Documented metrics: "
            + ", ".join(sorted(analytics.METHODOLOGY_NOTES))
        )

    caveats = "\n".join(f"- {caveat}" for caveat in note.caveats)

    return ToolResult(
        summary=(
            f"{note.metric.upper()}: {note.definition}\n"
            f"Formula: {note.formula}\nCaveats:\n{caveats}"
        ),
        data=note.model_dump(mode="json"),
    )


def _string_array(description: str) -> dict[str, Any]:
    return {
        "type": "array",
        "items": {"type": "string"},
        "description": description,
    }


TOOLS: tuple[Tool, ...] = (
    Tool(
        name="list_funds",
        description=(
            "List the funds AltLens tracks, optionally filtered by vintage "
            "year, strategy keyword, or manager name."
        ),
        parameters={
            "type": "object",
            "properties": {
                "vintage_year": {
                    "type": "integer",
                    "description": "Only funds raised in this year.",
                },
                "strategy_contains": {
                    "type": "string",
                    "description": "Substring match on the fund strategy.",
                },
                "manager_name": {
                    "type": "string",
                    "description": "Substring match on the manager name.",
                },
            },
        },
        run=tool_list_funds,
    ),
    Tool(
        name="get_fund_profile",
        description=(
            "Get the full profile for one fund: manager, vintage, strategy, "
            "geography, size, and headline metrics."
        ),
        parameters={
            "type": "object",
            "properties": {
                "fund_name": {"type": "string", "description": "Name of the fund."}
            },
            "required": ["fund_name"],
        },
        run=tool_get_fund_profile,
    ),
    Tool(
        name="get_fund_metrics",
        description=(
            "Get IRR, MOIC, DPI, RVPI and the underlying paid-in, distributed "
            "and residual NAV figures for one fund."
        ),
        parameters={
            "type": "object",
            "properties": {
                "fund_name": {"type": "string", "description": "Name of the fund."}
            },
            "required": ["fund_name"],
        },
        run=tool_get_fund_metrics,
    ),
    Tool(
        name="compare_funds",
        description="Compare metrics across two or more named funds.",
        parameters={
            "type": "object",
            "properties": {
                "fund_names": _string_array("Names of the funds to compare."),
            },
            "required": ["fund_names"],
        },
        run=tool_compare_funds,
    ),
    Tool(
        name="get_top_performers",
        description=(
            "Rank funds by a performance metric. Valid metrics: irr, moic, "
            "tvpi, dpi, rvpi."
        ),
        parameters={
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": sorted(analytics.RANKABLE_METRICS),
                    "description": "Metric to rank by.",
                },
                "limit": {
                    "type": "integer",
                    "description": "How many funds to return.",
                },
            },
        },
        run=tool_get_top_performers,
    ),
    Tool(
        name="get_vintage_year_summary",
        description=(
            "Summarize fund cohorts by vintage year, including median IRR and "
            "median MOIC per year."
        ),
        parameters={
            "type": "object",
            "properties": {
                "vintage_year": {
                    "type": "integer",
                    "description": "Limit to a single vintage year.",
                },
            },
        },
        run=tool_get_vintage_year_summary,
    ),
    Tool(
        name="get_sector_exposure",
        description=(
            "Break down portfolio-company exposure by sector, for named funds "
            "or across the whole demo portfolio."
        ),
        parameters={
            "type": "object",
            "properties": {
                "fund_names": _string_array(
                    "Limit the breakdown to these funds. Omit for all funds."
                ),
            },
        },
        run=tool_get_sector_exposure,
    ),
    Tool(
        name="generate_research_brief",
        description=(
            "Build a full structured research brief with metrics, tables, "
            "charts, sources, assumptions and follow-up questions."
        ),
        parameters={
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The research question the brief answers.",
                },
                "fund_names": _string_array("Funds to include in the brief."),
                "vintage_year": {
                    "type": "integer",
                    "description": "Limit the brief to one vintage year.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of funds to include.",
                },
            },
            "required": ["question"],
        },
        run=tool_generate_research_brief,
    ),
    Tool(
        name="explain_metric_methodology",
        description=(
            "Explain how AltLens calculates a metric and what caveats apply. "
            "Documented metrics: irr, moic, tvpi, dpi, rvpi."
        ),
        parameters={
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": "Metric name, for example 'irr'.",
                },
            },
            "required": ["metric"],
        },
        run=tool_explain_metric_methodology,
    ),
)


TOOLS_BY_NAME: dict[str, Tool] = {tool.name: tool for tool in TOOLS}


def get_tool(name: str) -> Tool | None:
    return TOOLS_BY_NAME.get(name)


def describe_tools() -> list[ToolDescription]:
    return [tool.describe() for tool in TOOLS]


def run_tool(name: str, arguments: dict[str, Any]) -> ToolResult:
    tool = get_tool(name)

    if tool is None:
        raise ToolExecutionError(
            f"'{name}' is not an approved AltLens tool. Approved tools: "
            + ", ".join(TOOLS_BY_NAME)
        )

    try:
        return tool.run(**arguments)
    except ToolExecutionError:
        raise
    except TypeError as error:
        raise ToolExecutionError(
            f"Invalid arguments for tool '{name}': {error}"
        ) from error
