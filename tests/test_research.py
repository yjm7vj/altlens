from altlens.research import generate_demo_research_brief


def test_generate_demo_research_brief_includes_metrics_and_sources():
    brief = generate_demo_research_brief("Compare the demo VC funds")

    assert brief.question == "Compare the demo VC funds"
    assert len(brief.funds) == 3
    assert set(brief.metrics) == {1, 2, 3}
    assert all(metric.moic is not None for metric in brief.metrics.values())
    assert brief.sources


def test_generate_demo_research_brief_marks_data_quality_limits():
    brief = generate_demo_research_brief("Which fund is strongest?")

    assert all(fund.data_quality == "illustrative" for fund in brief.funds)
    assert any("synthetic" in assumption for assumption in brief.assumptions)
    assert any("investment advice" in note for note in brief.data_quality_notes)


def test_generate_demo_research_brief_handles_empty_selection():
    brief = generate_demo_research_brief("Compare nothing", limit=0)

    assert brief.funds == []
    assert brief.metrics == {}
    assert "No demo funds" in brief.summary
