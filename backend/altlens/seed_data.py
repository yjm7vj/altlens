"""Load the illustrative demo dataset into a configured database.

Run with:

    python -m altlens.seed_data           # create tables, insert if empty
    python -m altlens.seed_data --reset   # drop and recreate first

The API does not need this: it serves the demo dataset from memory. This
script exists so the same data can be exercised against real Postgres before
verified private-market data is wired in.
"""

from __future__ import annotations

import argparse
import asyncio
from decimal import Decimal

from sqlalchemy import func, select

from altlens.database import create_all, dispose_engine, drop_all, session_scope
from altlens.demo_data import (
    get_demo_cash_flows,
    get_demo_funds,
    get_demo_positions,
    get_demo_snapshots,
    get_demo_sources,
)
from altlens.metrics import (
    calculate_dpi,
    calculate_irr,
    calculate_moic,
    calculate_tvpi,
    with_residual_value,
)
from altlens.models import (
    CashFlowEvent,
    Fund,
    FundMetrics,
    PerformanceSnapshot,
    PortfolioPosition,
    SourceReference,
)


async def seed(reset: bool = False) -> int:
    """Populate the database. Returns the number of funds written."""
    if reset:
        await drop_all()

    await create_all()

    async with session_scope() as session:
        existing = await session.scalar(select(func.count()).select_from(Fund))

        if existing:
            return 0

        for demo_fund in get_demo_funds():
            cash_flows = get_demo_cash_flows(demo_fund.id)
            snapshots = get_demo_snapshots(demo_fund.id)
            residual_value = (
                max(snapshots, key=lambda item: item.snapshot_date).nav_usd
                if snapshots
                else None
            )

            fund = Fund(
                id=demo_fund.id,
                name=demo_fund.name,
                manager_name=demo_fund.manager_name,
                asset_class=demo_fund.asset_class,
                vintage_year=demo_fund.vintage_year,
                fund_size_usd=demo_fund.fund_size_usd,
                strategy=demo_fund.strategy,
                geography=demo_fund.geography,
                description=demo_fund.description or None,
                data_quality=demo_fund.data_quality,
            )

            fund.cash_flows = [
                CashFlowEvent(
                    event_date=cash_flow.event_date,
                    amount_usd=cash_flow.amount_usd,
                    flow_type=cash_flow.flow_type,
                )
                for cash_flow in cash_flows
            ]

            fund.performance_snapshots = [
                PerformanceSnapshot(
                    snapshot_date=snapshot.snapshot_date,
                    nav_usd=snapshot.nav_usd,
                    cumulative_distributions_usd=(
                        snapshot.cumulative_distributions_usd
                    ),
                )
                for snapshot in snapshots
            ]

            fund.positions = [
                PortfolioPosition(
                    company_name=position.company_name,
                    sector=position.sector,
                    stage=position.stage,
                    invested_usd=position.invested_usd,
                    current_value_usd=position.current_value_usd,
                    status=position.status,
                )
                for position in get_demo_positions({demo_fund.id})
            ]

            fund.sources = [
                SourceReference(
                    source_name=source.source_name,
                    source_url=source.source_url,
                    field_name=source.field_name,
                    confidence=source.confidence,
                    data_status=source.data_status,
                    notes=source.notes,
                )
                for source in get_demo_sources({demo_fund.id})
            ]

            if cash_flows:
                irr_flows = with_residual_value(
                    cash_flows,
                    residual_value,
                    as_of=(
                        max(snapshot.snapshot_date for snapshot in snapshots)
                        if snapshots
                        else None
                    ),
                )
                fund.metrics = FundMetrics(
                    irr=_round(calculate_irr(irr_flows), 6),
                    moic=_round(calculate_moic(cash_flows, residual_value), 4),
                    tvpi=_round(calculate_tvpi(cash_flows, residual_value), 4),
                    dpi=_round(calculate_dpi(cash_flows), 4),
                )

            session.add(fund)

        return len(get_demo_funds())


def _round(value: float, places: int) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("1").scaleb(-places))


async def _main(reset: bool) -> None:
    try:
        written = await seed(reset=reset)
    finally:
        await dispose_engine()

    if written:
        print(f"Seeded {written} illustrative funds.")
    else:
        print("Database already contains funds; nothing was written.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the AltLens demo dataset.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate all tables before seeding.",
    )
    arguments = parser.parse_args()

    asyncio.run(_main(reset=arguments.reset))


if __name__ == "__main__":
    main()
