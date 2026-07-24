from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from scipy.optimize import brentq


@dataclass(frozen=True)
class CashFlow:
    event_date: date
    amount_usd: Decimal
    flow_type: str


def calculate_moic(cash_flows: Iterable[CashFlow]) -> float:
    invested = Decimal("0")
    returned = Decimal("0")

    for cash_flow in cash_flows:
        if cash_flow.flow_type == "capital_call":
            invested += abs(cash_flow.amount_usd)
        elif cash_flow.flow_type == "distribution":
            returned += cash_flow.amount_usd

    if invested == 0:
        return 0.0

    return float(returned / invested)


def calculate_irr(cash_flows: Iterable[CashFlow]) -> float:
    sorted_flows = sorted(cash_flows, key=lambda cash_flow: cash_flow.event_date)

    if len(sorted_flows) < 2:
        return 0.0

    amounts = [float(cash_flow.amount_usd) for cash_flow in sorted_flows]

    if not _has_positive_and_negative_amounts(amounts):
        return 0.0

    base_date = sorted_flows[0].event_date
    years = [
        (cash_flow.event_date - base_date).days / 365.0
        for cash_flow in sorted_flows
    ]

    def net_present_value(rate: float) -> float:
        return sum(
            amount / ((1 + rate) ** year)
            for amount, year in zip(amounts, years, strict=True)
        )

    try:
        return float(brentq(net_present_value, -0.99, 10.0))
    except ValueError:
        return 0.0


def _has_positive_and_negative_amounts(amounts: Iterable[float]) -> bool:
    has_positive = False
    has_negative = False

    for amount in amounts:
        has_positive = has_positive or amount > 0
        has_negative = has_negative or amount < 0

    return has_positive and has_negative
