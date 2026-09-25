"""The constrained research agent.

Flow: the provider picks tools, AltLens runs them, the provider narrates the
result. The agent is the only place those three steps meet, and it enforces
the guardrails — a bounded number of tool calls, approved tools only, and a
refusal when no tool can answer the question.
"""

from __future__ import annotations

import re
from statistics import mean

from altlens import ai_tools
from altlens.ai_tools import ToolExecutionError, ToolResult
from altlens.config import Settings
from altlens.providers import (
    OUT_OF_SCOPE_ANSWER,
    ModelProvider,
    ProviderError,
    build_rule_based_provider,
    get_provider,
)
from altlens.schemas import (
    AIQueryResponse,
    ResearchBrief,
    SourceReferenceOut,
    ToolCallRecord,
)

MAX_TOOL_CALLS = 3

DEMO_DATA_NOTE = (
    "AltLens is running on illustrative demo data, not verified fund reporting."
)


def answer_question(
    question: str,
    provider_name: str | None = None,
    model: str | None = None,
    settings: Settings | None = None,
) -> AIQueryResponse:
    """Answer a research question using only approved backend tools."""
    provider = get_provider(provider_name, model=model, settings=settings)
    notes: list[str] = [DEMO_DATA_NOTE]

    decision, provider, notes = _plan_with_fallback(provider, question, notes)

    if not decision.tool_calls:
        return AIQueryResponse(
            question=question,
            answer=decision.message or OUT_OF_SCOPE_ANSWER,
            provider=provider.name,
            model=provider.default_model(),
            data_quality_notes=notes,
        )

    records: list[ToolCallRecord] = []
    outputs: list[tuple[str, str]] = []
    sources: dict[tuple[str, str | None], SourceReferenceOut] = {}
    brief: ResearchBrief | None = None

    for invocation in decision.tool_calls[:MAX_TOOL_CALLS]:
        try:
            result = ai_tools.run_tool(invocation.name, invocation.arguments)
        except ToolExecutionError as error:
            records.append(
                ToolCallRecord(
                    tool_name=invocation.name,
                    arguments=dict(invocation.arguments),
                    summary=f"Tool could not run: {error}",
                )
            )
            outputs.append((invocation.name, str(error)))
            continue

        records.append(
            ToolCallRecord(
                tool_name=invocation.name,
                arguments=dict(invocation.arguments),
                summary=result.summary,
            )
        )
        outputs.append((invocation.name, result.summary))

        for source in result.sources:
            sources[(source.source_name, source.field_name)] = source

        if result.brief is not None and brief is None:
            brief = result.brief

        aggregate = _aggregate_note(question, result)

        if aggregate:
            outputs.append(("aggregate", aggregate))

    answer, notes = _narrate_with_fallback(provider, question, outputs, notes)

    if brief is not None:
        notes.extend(
            note for note in brief.data_quality_notes if note not in notes
        )

    return AIQueryResponse(
        question=question,
        answer=answer,
        provider=provider.name,
        model=provider.default_model(),
        tool_calls=records,
        brief=brief,
        sources=list(sources.values()),
        data_quality_notes=notes,
    )


def _plan_with_fallback(
    provider: ModelProvider, question: str, notes: list[str]
):
    try:
        decision = provider.plan(question, _tool_payload())
    except ProviderError as error:
        fallback = build_rule_based_provider()
        notes = [
            *notes,
            f"{provider.name} provider unavailable ({error}); answered with "
            "deterministic rule-based routing.",
        ]
        return fallback.plan(question, _tool_payload()), fallback, notes

    if not decision.tool_calls and provider.name != "rule_based":
        fallback = build_rule_based_provider()
        fallback_decision = fallback.plan(question, _tool_payload())

        if fallback_decision.tool_calls:
            notes = [
                *notes,
                f"{provider.name} did not select a tool; fell back to "
                "deterministic rule-based routing so the answer stays "
                "backed by calculated data.",
            ]
            return fallback_decision, fallback, notes

    return decision, provider, notes


def _narrate_with_fallback(
    provider: ModelProvider,
    question: str,
    outputs: list[tuple[str, str]],
    notes: list[str],
) -> tuple[str, list[str]]:
    try:
        return provider.narrate(question, outputs), notes
    except ProviderError as error:
        fallback = build_rule_based_provider()
        return (
            fallback.narrate(question, outputs),
            [
                *notes,
                f"{provider.name} could not phrase the answer ({error}); the "
                "tool output is shown directly.",
            ],
        )


def _tool_payload() -> list[dict[str, object]]:
    return [
        {
            "name": description.name,
            "description": description.description,
            "parameters": description.parameters,
        }
        for description in ai_tools.describe_tools()
    ]


_AGGREGATE_PATTERN = re.compile(r"\b(average|mean)\b", re.IGNORECASE)


def _aggregate_note(question: str, result: ToolResult) -> str | None:
    """Compute a mean across a tool's own results when the question asks for one.

    This stays in the agent rather than the model so the figure is calculated,
    not generated.
    """
    if not _AGGREGATE_PATTERN.search(question):
        return None

    if not isinstance(result.data, list):
        return None

    metric = _requested_metric(question) or "moic"
    values = [
        entry["metrics"][metric]
        for entry in result.data
        if isinstance(entry, dict)
        and isinstance(entry.get("metrics"), dict)
        and entry["metrics"].get(metric) is not None
    ]

    if not values:
        return None

    average = mean(float(value) for value in values)

    if metric == "irr":
        rendered = f"{average * 100:.1f}%"
    else:
        rendered = f"{average:.2f}x"

    return (
        f"Average {metric.upper()} across the {len(values)} fund(s) returned "
        f"above: {rendered}."
    )


def _requested_metric(question: str) -> str | None:
    text = question.casefold()

    for metric in ("irr", "moic", "tvpi", "dpi", "rvpi"):
        if re.search(rf"\b{metric}\b", text):
            return metric

    return None
