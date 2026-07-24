from datetime import date
from decimal import Decimal

import pytest

from altlens.metrics import CashFlow, calculate_irr, calculate_moic


def test_calculate_moic_returns_distributions_over_paid_in_capital():
    cash_flows = [
        CashFlow(date(2020, 1, 1), Decimal("-100"), "capital_call"),
        CashFlow(date(2021, 1, 1), Decimal("-50"), "capital_call"),
        CashFlow(date(2024, 1, 1), Decimal("300"), "distribution"),
    ]

    assert calculate_moic(cash_flows) == pytest.approx(2.0)


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
