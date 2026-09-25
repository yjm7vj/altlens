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
    description: str = ""
    asset_class: str = "venture_capital"
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


@dataclass(frozen=True)
class DemoSnapshot:
    fund_id: int
    snapshot_date: date
    nav_usd: Decimal
    cumulative_distributions_usd: Decimal


@dataclass(frozen=True)
class DemoPosition:
    """Illustrative portfolio-company exposure held by a demo fund."""

    fund_id: int
    company_name: str
    sector: str
    stage: str
    invested_usd: Decimal
    current_value_usd: Decimal
    status: str = "active"


DEMO_FUNDS: tuple[DemoFund, ...] = (
    DemoFund(
        id=1,
        name="AltLens Ventures I",
        manager_name="AltLens Capital",
        vintage_year=2018,
        fund_size_usd=Decimal("250000000"),
        strategy="Early-stage enterprise software",
        geography="North America",
        description=(
            "Early-stage enterprise software fund with a concentrated "
            "seed-through-Series-B portfolio."
        ),
    ),
    DemoFund(
        id=2,
        name="Frontier Seed Partners II",
        manager_name="Frontier Seed Partners",
        vintage_year=2019,
        fund_size_usd=Decimal("175000000"),
        strategy="Seed-stage AI infrastructure",
        geography="North America",
        description=(
            "Seed specialist concentrated in AI infrastructure and developer "
            "tooling companies."
        ),
    ),
    DemoFund(
        id=3,
        name="Summit Growth VC III",
        manager_name="Summit Growth",
        vintage_year=2020,
        fund_size_usd=Decimal("425000000"),
        strategy="Late-stage growth equity",
        geography="US and Europe",
        description=(
            "Late-stage growth vehicle backing pre-IPO software and fintech "
            "businesses."
        ),
    ),
    DemoFund(
        id=4,
        name="Harbor Point Ventures II",
        manager_name="Harbor Point",
        vintage_year=2018,
        fund_size_usd=Decimal("310000000"),
        strategy="Multi-stage fintech",
        geography="North America",
        description=(
            "Multi-stage fintech fund with meaningful payments and lending "
            "infrastructure exposure."
        ),
    ),
    DemoFund(
        id=5,
        name="Northwind Deep Tech I",
        manager_name="Northwind Capital",
        vintage_year=2019,
        fund_size_usd=Decimal("140000000"),
        strategy="Deep tech and semiconductors",
        geography="North America",
        description=(
            "First-time deep tech manager investing in semiconductors, "
            "robotics, and advanced manufacturing."
        ),
    ),
    DemoFund(
        id=6,
        name="Meridian Health Ventures III",
        manager_name="Meridian Partners",
        vintage_year=2020,
        fund_size_usd=Decimal("265000000"),
        strategy="Healthcare and biotech venture",
        geography="North America",
        description=(
            "Healthcare venture fund split between digital health and "
            "therapeutics platforms."
        ),
    ),
    DemoFund(
        id=7,
        name="Atlas Climate Fund I",
        manager_name="Atlas Climate",
        vintage_year=2021,
        fund_size_usd=Decimal("190000000"),
        strategy="Climate and energy transition",
        geography="Europe",
        description=(
            "Climate-focused venture fund investing across energy transition "
            "and industrial decarbonization."
        ),
    ),
    DemoFund(
        id=8,
        name="Cobalt Consumer Partners II",
        manager_name="Cobalt Partners",
        vintage_year=2021,
        fund_size_usd=Decimal("120000000"),
        strategy="Consumer internet and marketplaces",
        geography="North America",
        description=(
            "Consumer internet fund concentrated in marketplaces and "
            "subscription commerce."
        ),
    ),
    DemoFund(
        id=9,
        name="Pinnacle Enterprise Fund IV",
        manager_name="Pinnacle Ventures",
        vintage_year=2017,
        fund_size_usd=Decimal("500000000"),
        strategy="Enterprise infrastructure",
        geography="Global",
        description=(
            "Mature enterprise infrastructure fund with several realized "
            "exits and a substantial distribution history."
        ),
    ),
    DemoFund(
        id=10,
        name="Lattice Early Stage II",
        manager_name="Lattice Ventures",
        vintage_year=2022,
        fund_size_usd=Decimal("95000000"),
        strategy="Pre-seed and seed generalist",
        geography="North America",
        description=(
            "Young generalist pre-seed fund still inside its investment "
            "period with no realizations yet."
        ),
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
    4: (
        CashFlow(date(2018, 10, 1), Decimal("-110000000"), "capital_call"),
        CashFlow(date(2020, 1, 15), Decimal("-85000000"), "capital_call"),
        CashFlow(date(2023, 3, 31), Decimal("120000000"), "distribution"),
        CashFlow(date(2025, 6, 30), Decimal("165000000"), "distribution"),
    ),
    5: (
        CashFlow(date(2019, 9, 1), Decimal("-55000000"), "capital_call"),
        CashFlow(date(2021, 3, 1), Decimal("-50000000"), "capital_call"),
        CashFlow(date(2024, 6, 30), Decimal("70000000"), "distribution"),
        CashFlow(date(2026, 3, 31), Decimal("60000000"), "distribution"),
    ),
    6: (
        CashFlow(date(2020, 6, 1), Decimal("-95000000"), "capital_call"),
        CashFlow(date(2021, 12, 1), Decimal("-80000000"), "capital_call"),
        CashFlow(date(2024, 12, 31), Decimal("105000000"), "distribution"),
        CashFlow(date(2026, 6, 30), Decimal("115000000"), "distribution"),
    ),
    7: (
        CashFlow(date(2021, 5, 1), Decimal("-70000000"), "capital_call"),
        CashFlow(date(2022, 11, 1), Decimal("-55000000"), "capital_call"),
        CashFlow(date(2025, 9, 30), Decimal("95000000"), "distribution"),
    ),
    8: (
        CashFlow(date(2021, 8, 1), Decimal("-45000000"), "capital_call"),
        CashFlow(date(2022, 8, 1), Decimal("-40000000"), "capital_call"),
        CashFlow(date(2025, 6, 30), Decimal("52000000"), "distribution"),
    ),
    9: (
        CashFlow(date(2017, 4, 1), Decimal("-180000000"), "capital_call"),
        CashFlow(date(2018, 10, 1), Decimal("-150000000"), "capital_call"),
        CashFlow(date(2021, 6, 30), Decimal("240000000"), "distribution"),
        CashFlow(date(2023, 12, 31), Decimal("300000000"), "distribution"),
        CashFlow(date(2025, 12, 31), Decimal("210000000"), "distribution"),
    ),
    10: (
        CashFlow(date(2022, 6, 1), Decimal("-30000000"), "capital_call"),
        CashFlow(date(2023, 9, 1), Decimal("-25000000"), "capital_call"),
    ),
}


DEMO_SNAPSHOTS: tuple[DemoSnapshot, ...] = (
    DemoSnapshot(1, date(2020, 12, 31), Decimal("165000000"), Decimal("0")),
    DemoSnapshot(1, date(2022, 12, 31), Decimal("210000000"), Decimal("90000000")),
    DemoSnapshot(1, date(2024, 12, 31), Decimal("120000000"), Decimal("280000000")),
    DemoSnapshot(1, date(2026, 6, 30), Decimal("95000000"), Decimal("280000000")),
    DemoSnapshot(2, date(2021, 12, 31), Decimal("135000000"), Decimal("0")),
    DemoSnapshot(2, date(2023, 12, 31), Decimal("190000000"), Decimal("60000000")),
    DemoSnapshot(2, date(2025, 12, 31), Decimal("125000000"), Decimal("210000000")),
    DemoSnapshot(2, date(2026, 6, 30), Decimal("118000000"), Decimal("210000000")),
    DemoSnapshot(3, date(2022, 12, 31), Decimal("330000000"), Decimal("0")),
    DemoSnapshot(3, date(2024, 12, 31), Decimal("260000000"), Decimal("180000000")),
    DemoSnapshot(3, date(2026, 6, 30), Decimal("245000000"), Decimal("180000000")),
    DemoSnapshot(4, date(2021, 12, 31), Decimal("235000000"), Decimal("0")),
    DemoSnapshot(4, date(2023, 12, 31), Decimal("215000000"), Decimal("120000000")),
    DemoSnapshot(4, date(2026, 6, 30), Decimal("140000000"), Decimal("285000000")),
    DemoSnapshot(5, date(2021, 12, 31), Decimal("115000000"), Decimal("0")),
    DemoSnapshot(5, date(2024, 12, 31), Decimal("105000000"), Decimal("70000000")),
    DemoSnapshot(5, date(2026, 6, 30), Decimal("60000000"), Decimal("130000000")),
    DemoSnapshot(6, date(2022, 12, 31), Decimal("205000000"), Decimal("0")),
    DemoSnapshot(6, date(2024, 12, 31), Decimal("190000000"), Decimal("105000000")),
    DemoSnapshot(6, date(2026, 6, 30), Decimal("115000000"), Decimal("220000000")),
    DemoSnapshot(7, date(2023, 12, 31), Decimal("140000000"), Decimal("0")),
    DemoSnapshot(7, date(2025, 12, 31), Decimal("120000000"), Decimal("95000000")),
    DemoSnapshot(7, date(2026, 6, 30), Decimal("118000000"), Decimal("95000000")),
    DemoSnapshot(8, date(2023, 12, 31), Decimal("95000000"), Decimal("0")),
    DemoSnapshot(8, date(2025, 12, 31), Decimal("72000000"), Decimal("52000000")),
    DemoSnapshot(8, date(2026, 6, 30), Decimal("68000000"), Decimal("52000000")),
    DemoSnapshot(9, date(2019, 12, 31), Decimal("395000000"), Decimal("0")),
    DemoSnapshot(9, date(2021, 12, 31), Decimal("460000000"), Decimal("240000000")),
    DemoSnapshot(9, date(2023, 12, 31), Decimal("300000000"), Decimal("540000000")),
    DemoSnapshot(9, date(2026, 6, 30), Decimal("150000000"), Decimal("750000000")),
    DemoSnapshot(10, date(2023, 12, 31), Decimal("52000000"), Decimal("0")),
    DemoSnapshot(10, date(2025, 12, 31), Decimal("68000000"), Decimal("0")),
    DemoSnapshot(10, date(2026, 6, 30), Decimal("71000000"), Decimal("0")),
)


DEMO_POSITIONS: tuple[DemoPosition, ...] = (
    DemoPosition(
        1, "Northstar Data", "Enterprise SaaS", "series_b",
        Decimal("22000000"), Decimal("64000000"),
    ),
    DemoPosition(
        1, "Relay Workflow", "Enterprise SaaS", "series_a",
        Decimal("15000000"), Decimal("41000000"),
    ),
    DemoPosition(
        1, "Ledgerline", "Fintech", "series_b",
        Decimal("18000000"), Decimal("12000000"), "written_down",
    ),
    DemoPosition(
        2, "Tensor Fabric", "AI Infrastructure", "seed",
        Decimal("9000000"), Decimal("78000000"),
    ),
    DemoPosition(
        2, "Vectorlake", "AI Infrastructure", "series_a",
        Decimal("12000000"), Decimal("34000000"),
    ),
    DemoPosition(
        2, "Promptworks", "Developer Tools", "seed",
        Decimal("6000000"), Decimal("9000000"),
    ),
    DemoPosition(
        3, "Cascade Payments", "Fintech", "series_d",
        Decimal("55000000"), Decimal("92000000"),
    ),
    DemoPosition(
        3, "Orbital Logistics", "Logistics", "series_c",
        Decimal("48000000"), Decimal("61000000"),
    ),
    DemoPosition(
        3, "Halcyon Security", "Cybersecurity", "series_c",
        Decimal("40000000"), Decimal("55000000"),
    ),
    DemoPosition(
        4, "Beacon Lending", "Fintech", "series_c",
        Decimal("35000000"), Decimal("58000000"),
    ),
    DemoPosition(
        4, "Payrail", "Fintech", "series_b",
        Decimal("24000000"), Decimal("47000000"),
    ),
    DemoPosition(
        4, "Quill Insurance", "Insurtech", "series_a",
        Decimal("16000000"), Decimal("11000000"), "written_down",
    ),
    DemoPosition(
        5, "Silicon Ridge", "Semiconductors", "series_b",
        Decimal("26000000"), Decimal("44000000"),
    ),
    DemoPosition(
        5, "Axiom Robotics", "Robotics", "series_a",
        Decimal("14000000"), Decimal("19000000"),
    ),
    DemoPosition(
        6, "Helix Diagnostics", "Healthcare", "series_b",
        Decimal("30000000"), Decimal("58000000"),
    ),
    DemoPosition(
        6, "Caremesh", "Digital Health", "series_a",
        Decimal("18000000"), Decimal("23000000"),
    ),
    DemoPosition(
        6, "Protean Bio", "Biotech", "series_c",
        Decimal("34000000"), Decimal("40000000"),
    ),
    DemoPosition(
        7, "Gridwise Energy", "Energy Transition", "series_b",
        Decimal("28000000"), Decimal("46000000"),
    ),
    DemoPosition(
        7, "Carbonform", "Industrial Decarbonization", "series_a",
        Decimal("17000000"), Decimal("21000000"),
    ),
    DemoPosition(
        8, "Marketmint", "Consumer Marketplace", "series_b",
        Decimal("21000000"), Decimal("18000000"),
    ),
    DemoPosition(
        8, "Everyday Goods", "Consumer Commerce", "series_a",
        Decimal("12000000"), Decimal("9000000"), "written_down",
    ),
    DemoPosition(
        9, "Cirrus Cloud", "Enterprise Infrastructure", "series_d",
        Decimal("70000000"), Decimal("260000000"), "realized",
    ),
    DemoPosition(
        9, "Keystone Data", "Enterprise Infrastructure", "series_c",
        Decimal("52000000"), Decimal("140000000"), "realized",
    ),
    DemoPosition(
        9, "Sentry Networks", "Cybersecurity", "series_c",
        Decimal("45000000"), Decimal("88000000"),
    ),
    DemoPosition(
        10, "Foundry Labs", "AI Infrastructure", "pre_seed",
        Decimal("4000000"), Decimal("11000000"),
    ),
    DemoPosition(
        10, "Tidepool Analytics", "Enterprise SaaS", "seed",
        Decimal("5000000"), Decimal("7000000"),
    ),
)


SEED_SOURCE_NAME = "AltLens demo seed dataset"


def _build_demo_sources() -> tuple[DemoSource, ...]:
    sources: list[DemoSource] = []

    for fund in DEMO_FUNDS:
        sources.append(
            DemoSource(
                fund_id=fund.id,
                source_name=SEED_SOURCE_NAME,
                field_name="cash_flows",
                confidence="low",
                data_status="illustrative",
                notes=(
                    f"Synthetic cash flows for {fund.name}, used to exercise "
                    "metric calculations without licensed data."
                ),
            )
        )
        sources.append(
            DemoSource(
                fund_id=fund.id,
                source_name=SEED_SOURCE_NAME,
                field_name="strategy",
                confidence="low",
                data_status="illustrative",
                notes=(
                    f"Strategy and geography labels for {fund.name} are "
                    "illustrative placeholders pending verified sources."
                ),
            )
        )

    return tuple(sources)


DEMO_SOURCES: tuple[DemoSource, ...] = _build_demo_sources()


def get_demo_funds() -> tuple[DemoFund, ...]:
    return DEMO_FUNDS


def get_demo_fund(fund_id: int) -> DemoFund | None:
    for fund in DEMO_FUNDS:
        if fund.id == fund_id:
            return fund

    return None


def get_demo_cash_flows(fund_id: int) -> tuple[CashFlow, ...]:
    return DEMO_CASH_FLOWS.get(fund_id, ())


def get_demo_snapshots(fund_id: int) -> tuple[DemoSnapshot, ...]:
    return tuple(
        snapshot for snapshot in DEMO_SNAPSHOTS if snapshot.fund_id == fund_id
    )


def get_demo_positions(fund_ids: set[int] | None = None) -> tuple[DemoPosition, ...]:
    if fund_ids is None:
        return DEMO_POSITIONS

    return tuple(
        position for position in DEMO_POSITIONS if position.fund_id in fund_ids
    )


def get_demo_sources(fund_ids: set[int] | None = None) -> tuple[DemoSource, ...]:
    if fund_ids is None:
        return DEMO_SOURCES

    return tuple(source for source in DEMO_SOURCES if source.fund_id in fund_ids)
