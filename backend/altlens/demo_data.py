from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from altlens.metrics import CashFlow


@dataclass(frozen=True)
class DemoFund:
    id: int
    name: str
    manager_name: str
    vintage_year: int
    fund_size_usd: Decimal
    strategy: str
    geography: str
    data_quality: str = "illustrative"


@dataclass(frozen=True)
class DemoSource:
    fund_id: int
    source_name: str
    field_name: str
    confidence: str
    data_status: str
    notes: str
    source_url: str | None = None


DEMO_FUNDS: tuple[DemoFund, ...] = (
    DemoFund(
        id=1,
        name="AltLens Ventures I",
        manager_name="AltLens Capital",
        vintage_year=2018,
        fund_size_usd=Decimal("250000000"),
        strategy="Early-stage enterprise software",
        geography="North America",
    ),
    DemoFund(
        id=2,
        name="Frontier Seed Partners II",
        manager_name="Frontier Seed Partners",
        vintage_year=2019,
        fund_size_usd=Decimal("175000000"),
        strategy="Seed-stage AI infrastructure",
        geography="North America",
    ),
    DemoFund(
        id=3,
        name="Summit Growth VC III",
        manager_name="Summit Growth",
        vintage_year=2020,
        fund_size_usd=Decimal("425000000"),
        strategy="Late-stage growth equity",
        geography="US and Europe",
    ),
)


DEMO_CASH_FLOWS: dict[int, tuple[CashFlow, ...]] = {
    1: (
        CashFlow(date(2018, 7, 1), Decimal("-80000000"), "capital_call"),
        CashFlow(date(2019, 7, 1), Decimal("-60000000"), "capital_call"),
        CashFlow(date(2022, 9, 30), Decimal("90000000"), "distribution"),
        CashFlow(date(2024, 12, 31), Decimal("190000000"), "distribution"),
    ),
    2: (
        CashFlow(date(2019, 4, 1), Decimal("-65000000"), "capital_call"),
        CashFlow(date(2020, 4, 1), Decimal("-45000000"), "capital_call"),
        CashFlow(date(2023, 6, 30), Decimal("60000000"), "distribution"),
        CashFlow(date(2025, 3, 31), Decimal("150000000"), "distribution"),
    ),
    3: (
        CashFlow(date(2020, 10, 1), Decimal("-160000000"), "capital_call"),
        CashFlow(date(2021, 10, 1), Decimal("-140000000"), "capital_call"),
        CashFlow(date(2024, 9, 30), Decimal("180000000"), "distribution"),
    ),
}


DEMO_SOURCES: tuple[DemoSource, ...] = (
    DemoSource(
        fund_id=1,
        source_name="AltLens demo seed dataset",
        field_name="cash_flows",
        confidence="low",
        data_status="illustrative",
        notes="Synthetic cash flows for product development and demo wiring.",
    ),
    DemoSource(
        fund_id=2,
        source_name="AltLens demo seed dataset",
        field_name="strategy",
        confidence="low",
        data_status="illustrative",
        notes="Illustrative strategy label used to exercise research brief output.",
    ),
    DemoSource(
        fund_id=3,
        source_name="AltLens demo seed dataset",
        field_name="cash_flows",
        confidence="low",
        data_status="illustrative",
        notes="Synthetic fund profile used until verified private-market data exists.",
    ),
)


def get_demo_funds() -> tuple[DemoFund, ...]:
    return DEMO_FUNDS


def get_demo_cash_flows(fund_id: int) -> tuple[CashFlow, ...]:
    return DEMO_CASH_FLOWS.get(fund_id, ())


def get_demo_sources(fund_ids: set[int] | None = None) -> tuple[DemoSource, ...]:
    if fund_ids is None:
        return DEMO_SOURCES

    return tuple(source for source in DEMO_SOURCES if source.fund_id in fund_ids)
