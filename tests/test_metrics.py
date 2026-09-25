from datetime import date
from decimal import Decimal

import pytest

from altlens.metrics import (
    CashFlow,
    calculate_dpi,
    calculate_irr,
    calculate_moic,
    calculate_rvpi,
    calculate_tvpi,
    total_distributions,
    total_paid_in,
    with_residual_value,
)


def test_calculate_moic_returns_distributions_over_paid_in_capital():
    cash_flows = [
        CashFlow(date(2020, 1, 1), Decimal("-100"), "capital_call"),
        CashFlow(date(2021, 1, 1), Decimal("-50"), "capital_call"),
        CashFlow(date(2024, 1, 1), Decimal("300"), "distribution"),
    ]

    assert calculate_moic(cash_flows) == pytest.approx(2.0)


def test_calculate_moic_includes_residual_nav_when_supplied():
    cash_flows = [
        CashFlow(date(2020, 1, 1), Decimal("-100"), "capital_call"),
        CashFlow(date(2024, 1, 1), Decimal("150"), "distribution"),
    ]

    assert calculate_moic(cash_flows, Decimal("50")) == pytest.approx(2.0)


def test_paid_in_and_distribution_totals():
    cash_flows = [
        CashFlow(date(2020, 1, 1), Decimal("-100"), "capital_call"),
        CashFlow(date(2021, 1, 1), Decimal("-50"), "capital_call"),
        CashFlow(date(2024, 1, 1), Decimal("180"), "distribution"),
    ]

    assert total_paid_in(cash_flows) == Decimal("150")
    assert total_distributions(cash_flows) == Decimal("180")


def test_dpi_rvpi_and_tvpi_split_realized_from_unrealized_value():
    cash_flows = [
        CashFlow(date(2020, 1, 1), Decimal("-100"), "capital_call"),
        CashFlow(date(2024, 1, 1), Decimal("120"), "distribution"),
    ]
    nav = Decimal("60")

    assert calculate_dpi(cash_flows) == pytest.approx(1.2)
    assert calculate_rvpi(cash_flows, nav) == pytest.approx(0.6)
    assert calculate_tvpi(cash_flows, nav) == pytest.approx(1.8)


def test_metrics_with_no_paid_in_capital_return_zero_rather_than_dividing():
    assert calculate_moic([]) == 0.0
    assert calculate_dpi([]) == 0.0
    assert calculate_rvpi([], Decimal("100")) == 0.0


def test_calculate_irr_for_simple_five_year_double():
    cash_flows = [
        CashFlow(date(2020, 1, 1), Decimal("-100"), "capital_call"),
        CashFlow(date(2025, 1, 1), Decimal("200"), "distribution"),
    ]

    assert calculate_irr(cash_flows) == pytest.approx(0.1485, abs=0.001)


def test_calculate_irr_with_multiple_capital_calls():
    cash_flows = [
        CashFlow(date(2020, 1, 1), Decimal("-100"), "capital_call"),
        CashFlow(date(2021, 1, 1), Decimal("-50"), "capital_call"),
        CashFlow(date(2023, 1, 1), Decimal("220"), "distribution"),
    ]

    assert calculate_irr(cash_flows) == pytest.approx(0.153, abs=0.005)


def test_calculate_irr_for_losing_fund_is_negative():
    cash_flows = [
        CashFlow(date(2020, 1, 1), Decimal("-100"), "capital_call"),
        CashFlow(date(2023, 1, 1), Decimal("75"), "distribution"),
    ]

    assert calculate_irr(cash_flows) == pytest.approx(-0.091, abs=0.005)


def test_calculate_irr_without_mixed_cash_flow_signs_returns_zero():
    cash_flows = [
        CashFlow(date(2020, 1, 1), Decimal("-100"), "capital_call"),
        CashFlow(date(2021, 1, 1), Decimal("-50"), "capital_call"),
    ]

    assert calculate_irr(cash_flows) == 0.0


def test_residual_value_makes_an_unrealized_fund_solvable():
    cash_flows = [
        CashFlow(date(2020, 1, 1), Decimal("-100"), "capital_call"),
        CashFlow(date(2021, 1, 1), Decimal("-50"), "capital_call"),
    ]

    assert calculate_irr(cash_flows) == 0.0

    with_nav = with_residual_value(
        cash_flows, Decimal("225"), as_of=date(2025, 1, 1)
    )

    # Checked independently: -100 at t=0, -50 at t=1, +225 at t=5 solves
    # to roughly 9.0%. IRR intuition is unreliable here, so the expected
    # value comes from the cash-flow arithmetic, not a guess.
    assert calculate_irr(with_nav) == pytest.approx(0.090, abs=0.005)


def test_residual_value_is_ignored_when_there_is_none():
    cash_flows = [CashFlow(date(2020, 1, 1), Decimal("-100"), "capital_call")]

    assert with_residual_value(cash_flows, None) == cash_flows
    assert with_residual_value(cash_flows, Decimal("0")) == cash_flows
