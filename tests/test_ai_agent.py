"""The agent's guardrails, exercised without any model provider.

These run against the deterministic rule-based provider, so they assert what
must hold for every provider: approved tools only, bounded tool calls, and a
refusal rather than a guess when nothing fits.
"""

import pytest

from altlens.ai_agent import MAX_TOOL_CALLS, answer_question
from altlens.ai_tools import (
    TOOLS_BY_NAME,
    ToolExecutionError,
    describe_tools,
    run_tool,
)
from altlens.providers import (
    OUT_OF_SCOPE_ANSWER,
    ModelDecision,
    ProviderError,
    RuleBasedProvider,
    ToolInvocation,
    get_provider,
    list_providers,
)


class StubProvider(RuleBasedProvider):
    """A provider that returns a fixed decision, standing in for a model."""

    name = "stub"

    def __init__(self, decision: ModelDecision, fail_narration: bool = False):
        super().__init__(fund_names=[], manager_names=[])
        self._decision = decision
        self._fail_narration = fail_narration

    def plan(self, question, tools):
        return self._decision

    def narrate(self, question, tool_outputs):
        if self._fail_narration:
            raise ProviderError("stub narration failed")

        return super().narrate(question, tool_outputs)


def test_every_tool_is_described_with_a_json_schema():
    described = describe_tools()

    assert {tool.name for tool in described} == set(TOOLS_BY_NAME)
    assert all(tool.description for tool in described)
    assert all(tool.parameters.get("type") == "object" for tool in described)


def test_running_an_unapproved_tool_is_refused():
    with pytest.raises(ToolExecutionError, match="not an approved AltLens tool"):
        run_tool("drop_table", {})


def test_tool_rejects_arguments_it_does_not_accept():
    with pytest.raises(ToolExecutionError, match="Invalid arguments"):
        run_tool("get_fund_metrics", {"ticker": "AAPL"})


def test_tool_reports_an_unknown_fund_rather_than_inventing_one():
    with pytest.raises(ToolExecutionError, match="No fund named"):
        run_tool("get_fund_profile", {"fund_name": "Sequoia Capital XX"})


def test_metric_question_routes_to_fund_metrics():
    response = answer_question("What's the IRR for Frontier Seed Partners II?")

    assert [call.tool_name for call in response.tool_calls] == ["get_fund_metrics"]
    assert "21." in response.answer
    assert response.sources


def test_ranking_question_routes_to_top_performers():
    response = answer_question("Which fund had the best performance?")

    assert [call.tool_name for call in response.tool_calls] == ["get_top_performers"]


def test_comparison_question_routes_to_compare_funds():
    response = answer_question(
        "Compare AltLens Ventures I and Summit Growth VC III"
    )

    assert [call.tool_name for call in response.tool_calls] == ["compare_funds"]
    assert "AltLens Ventures I" in response.answer
    assert "Summit Growth VC III" in response.answer


def test_brief_question_returns_a_structured_brief():
    response = answer_question("Create a research brief on 2018 vintage funds")

    assert response.brief is not None
    assert response.brief.tables
    assert response.brief.follow_up_questions
    assert response.brief.assumptions


def test_average_question_reports_a_calculated_mean():
    response = answer_question("What is the average MOIC across all funds?")

    assert "Average MOIC" in response.answer


def test_out_of_scope_question_is_refused_without_tool_calls():
    response = answer_question("How did hedge funds perform last year?")

    assert response.tool_calls == []
    assert response.answer == OUT_OF_SCOPE_ANSWER
    assert response.brief is None


def test_methodology_question_explains_rather_than_ranking():
    response = answer_question("How is IRR calculated?")

    assert [call.tool_name for call in response.tool_calls] == [
        "explain_metric_methodology"
    ]
    assert "net present value" in response.answer


def test_every_answer_carries_a_demo_data_note():
    response = answer_question("Which fund had the best performance?")

    assert any("illustrative" in note for note in response.data_quality_notes)


def test_agent_stops_after_the_tool_call_limit():
    decision = ModelDecision(
        tool_calls=[ToolInvocation("list_funds", {})] * (MAX_TOOL_CALLS + 3)
    )
    provider = StubProvider(decision)

    response = _answer_with(provider, "List every fund")

    assert len(response.tool_calls) == MAX_TOOL_CALLS


def test_agent_records_a_failed_tool_instead_of_inventing_an_answer():
    decision = ModelDecision(
        tool_calls=[ToolInvocation("get_fund_profile", {"fund_name": "Nope"})]
    )

    response = _answer_with(StubProvider(decision), "Tell me about Nope")

    assert response.tool_calls[0].summary.startswith("Tool could not run")
    assert "No fund named" in response.answer


def test_agent_falls_back_when_narration_fails():
    decision = ModelDecision(tool_calls=[ToolInvocation("list_funds", {})])

    response = _answer_with(
        StubProvider(decision, fail_narration=True), "List the funds"
    )

    assert "AltLens Ventures I" in response.answer
    assert any("could not phrase" in note for note in response.data_quality_notes)


def _answer_with(provider, question):
    """Run the agent against a specific provider instance."""
    import altlens.ai_agent as agent_module

    original = agent_module.get_provider
    agent_module.get_provider = lambda *args, **kwargs: provider

    try:
        return answer_question(question)
    finally:
        agent_module.get_provider = original


def test_provider_registry_always_offers_a_working_default():
    providers = {info.name: info for info in list_providers()}

    assert providers["rule_based"].available is True
    assert "openai" in providers
    assert "ollama" in providers


def test_unknown_provider_name_is_rejected():
    with pytest.raises(ProviderError, match="Unknown model provider"):
        get_provider("gpt-5-turbo-ultra")
