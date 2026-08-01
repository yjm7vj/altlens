from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from altlens.demo_data import DemoFund, get_demo_cash_flows, get_demo_funds
from altlens.metrics import calculate_irr, calculate_moic
from altlens.schemas import FundMetricSummary, FundSummary


@dataclass(frozen=True)
class FundWithMetrics:
    fund: FundSummary
    metrics: FundMetricSummary


def list_funds(
    asset_class: str | None = None,
    vintage_year: int | None = None,
) -> list[FundSummary]:
    funds = get_demo_funds()

    if asset_class is not None:
        funds = tuple(fund for fund in funds if asset_class == "venture_capital")

    if vintage_year is not None:
        funds = tuple(fund for fund in funds if fund.vintage_year == vintage_year)

    return [_to_fund_summary(fund) for fund in funds]


def get_fund_profile(fund_name: str) -> FundWithMetrics | None:
    normalized_name = fund_name.casefold()

    for fund in get_demo_funds():
        if fund.name.casefold() == normalized_name:
            return FundWithMetrics(
                fund=_to_fund_summary(fund),
                metrics=calculate_fund_metrics(fund.id),
            )

    return None


def get_top_performers(metric: str = "moic", limit: int = 5) -> list[FundWithMetrics]:
    if metric not in {"irr", "moic"}:
        raise ValueError("metric must be either 'irr' or 'moic'")

    funds_with_metrics = [
        _to_fund_with_metrics(fund)
        for fund in get_demo_funds()
    ]

    return sorted(
        funds_with_metrics,
        key=lambda item: getattr(item.metrics, metric) or Decimal("0"),
        reverse=True,
    )[:limit]


def compare_funds(fund_names: list[str]) -> list[FundWithMetrics]:
    requested_names = {name.casefold() for name in fund_names}

    return [
        _to_fund_with_metrics(fund)
        for fund in get_demo_funds()
        if fund.name.casefold() in requested_names
    ]


def calculate_fund_metrics(fund_id: int) -> FundMetricSummary:
    cash_flows = get_demo_cash_flows(fund_id)

    return FundMetricSummary(
        irr=_to_decimal(calculate_irr(cash_flows), places=6),
        moic=_to_decimal(calculate_moic(cash_flows), places=4),
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


def _to_fund_with_metrics(fund: DemoFund) -> FundWithMetrics:
    return FundWithMetrics(
        fund=_to_fund_summary(fund),
        metrics=calculate_fund_metrics(fund.id),
    )


def _to_decimal(value: float, places: int) -> Decimal:
    quantizer = Decimal("1").scaleb(-places)
    return Decimal(str(value)).quantize(quantizer)
