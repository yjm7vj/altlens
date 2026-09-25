from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from scipy.optimize import brentq

CAPITAL_CALL = "capital_call"
DISTRIBUTION = "distribution"


@dataclass(frozen=True)
class CashFlow:
    event_date: date
    amount_usd: Decimal
    flow_type: str


def total_paid_in(cash_flows: Iterable[CashFlow]) -> Decimal:
    """Total capital called by the fund, expressed as a positive number."""
    return sum(
        (
            abs(cash_flow.amount_usd)
            for cash_flow in cash_flows
            if cash_flow.flow_type == CAPITAL_CALL
        ),
        Decimal("0"),
    )


def total_distributions(cash_flows: Iterable[CashFlow]) -> Decimal:
    """Total capital returned to limited partners."""
    return sum(
        (
            cash_flow.amount_usd
            for cash_flow in cash_flows
            if cash_flow.flow_type == DISTRIBUTION
        ),
        Decimal("0"),
    )


def calculate_moic(
    cash_flows: Iterable[CashFlow],
    residual_value_usd: Decimal | None = None,
) -> float:
    """Multiple on invested capital.

    Distributions plus any remaining residual value (NAV), divided by paid-in
    capital. With no residual value supplied this is realized MOIC, which is
    the same figure as DPI.
    """
    cash_flows = list(cash_flows)
    invested = total_paid_in(cash_flows)

    if invested == 0:
        return 0.0

    returned = total_distributions(cash_flows) + (residual_value_usd or Decimal("0"))

    return float(returned / invested)


def calculate_dpi(cash_flows: Iterable[CashFlow]) -> float:
    """Distributions to paid-in: realized cash returned per dollar called."""
    cash_flows = list(cash_flows)
    invested = total_paid_in(cash_flows)

    if invested == 0:
        return 0.0

    return float(total_distributions(cash_flows) / invested)


def calculate_rvpi(
    cash_flows: Iterable[CashFlow], residual_value_usd: Decimal | None
) -> float:
    """Residual value to paid-in: unrealized NAV per dollar called."""
    invested = total_paid_in(cash_flows)

    if invested == 0 or residual_value_usd is None:
        return 0.0

    return float(residual_value_usd / invested)


def calculate_tvpi(
    cash_flows: Iterable[CashFlow], residual_value_usd: Decimal | None
) -> float:
    """Total value to paid-in: realized distributions plus unrealized NAV."""
    return calculate_moic(cash_flows, residual_value_usd)


def with_residual_value(
    cash_flows: Sequence[CashFlow],
    residual_value_usd: Decimal | None,
    as_of: date | None = None,
) -> list[CashFlow]:
    """Append unrealized NAV as a terminal inflow.

    IRR for a fund that is still holding positions is only meaningful when the
    remaining NAV is treated as though it were distributed on the valuation
    date. Without this, a young fund with no exits yet has no solvable IRR.
    """
    flows = list(cash_flows)

    if not residual_value_usd or residual_value_usd <= 0:
        return flows

    terminal_date = as_of or (
        max(flow.event_date for flow in flows) if flows else date.today()
    )

    return [
        *flows,
        CashFlow(terminal_date, residual_value_usd, DISTRIBUTION),
    ]


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
