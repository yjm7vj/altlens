import pytest
from fastapi.testclient import TestClient

from altlens.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_reports_the_demo_data_source(client):
    body = client.get("/api/health").json()

    assert body["status"] == "ok"
    assert body["data_source"] == "illustrative_demo"
    assert body["fund_count"] > 0
    assert "investment advice" in body["disclaimer"]


def test_list_funds_and_filter_by_vintage(client):
    everything = client.get("/api/funds").json()
    filtered = client.get("/api/funds", params={"vintage_year": 2018}).json()

    assert len(everything) > len(filtered)
    assert all(fund["vintage_year"] == 2018 for fund in filtered)


def test_funds_with_metrics_joins_calculated_figures(client):
    rows = client.get("/api/funds/with-metrics").json()

    assert rows
    assert all(row["metrics"]["moic"] is not None for row in rows)


def test_fund_detail_and_missing_fund(client):
    response = client.get("/api/funds/1")
    assert response.status_code == 200

    detail = response.json()
    assert detail["fund"]["name"] == "AltLens Ventures I"
    assert detail["cash_flows"]
    assert detail["positions"]

    assert client.get("/api/funds/9999").status_code == 404


def test_performance_and_metrics_endpoints(client):
    performance = client.get("/api/funds/1/performance").json()
    assert performance["points"]

    metrics = client.get("/api/funds/1/metrics").json()
    assert metrics["irr"] is not None

    assert client.get("/api/funds/9999/metrics").status_code == 404


def test_top_performers_validates_the_metric(client):
    ok = client.get("/api/metrics/top", params={"metric": "irr", "limit": 3})
    assert ok.status_code == 200
    assert len(ok.json()) == 3

    bad = client.get("/api/metrics/top", params={"metric": "sharpe_ratio"})
    assert bad.status_code == 400


def test_vintage_sector_and_timeline_endpoints(client):
    assert client.get("/api/metrics/vintages").json()
    assert client.get("/api/metrics/sectors").json()

    timeline = client.get("/api/metrics/capital-timeline").json()
    assert timeline["points"]
    assert timeline["break_even_date"]


def test_methodology_endpoint(client):
    assert client.get("/api/metrics/methodology/irr").status_code == 200
    assert client.get("/api/metrics/methodology/alpha").status_code == 404


def test_research_brief_endpoint_returns_structured_output(client):
    brief = client.post(
        "/api/research/brief",
        params={"question": "Compare 2018 funds", "vintage_year": 2018},
    ).json()

    assert brief["funds"]
    assert brief["tables"]
    assert brief["assumptions"]
    assert brief["data_quality_notes"]


def test_ai_query_endpoint_records_its_tool_calls(client):
    body = client.post(
        "/api/ai/query", json={"question": "Which fund had the best performance?"}
    ).json()

    assert body["provider"] == "rule_based"
    assert [call["tool_name"] for call in body["tool_calls"]] == [
        "get_top_performers"
    ]


def test_ai_query_rejects_an_empty_question(client):
    assert client.post("/api/ai/query", json={"question": ""}).status_code == 422


def test_ai_tool_catalog_is_exposed_for_inspection(client):
    tools = client.get("/api/ai/tools").json()

    assert {"get_fund_metrics", "compare_funds", "generate_research_brief"} <= {
        tool["name"] for tool in tools
    }


def test_sources_endpoint_labels_everything_illustrative(client):
    sources = client.get("/api/sources").json()

    assert sources
    assert all(source["data_status"] == "illustrative" for source in sources)
