"""Approved analytics functions over the AltLens demo dataset.

Every function here is safe to expose to the AI layer: the inputs are
validated, the outputs are structured, and nothing generates SQL or free-form
calculations. The agent picks a function; it never invents a number.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from statistics import median

from altlens.demo_data import (
    DemoFund,
    DemoPosition,
    get_demo_cash_flows,
    get_demo_fund,
    get_demo_funds,
    get_demo_positions,
    get_demo_snapshots,
    get_demo_sources,
)
from altlens.metrics import (
    calculate_dpi,
    calculate_irr,
    calculate_moic,
    calculate_rvpi,
    calculate_tvpi,
    total_distributions,
    total_paid_in,
    with_residual_value,
)
from altlens.schemas import (
    CapitalTimeline,
    CapitalTimelinePoint,
    CashFlowOut,
    FundDetail,
    FundMetricSummary,
    FundPerformanceSeries,
    FundSummary,
    MethodologyNote,
    PerformancePoint,
    PortfolioPositionOut,
    SectorExposure,
    SourceReferenceOut,
    VintageYearSummary,
)

RANKABLE_METRICS: frozenset[str] = frozenset({"irr", "moic", "tvpi", "dpi", "rvpi"})

SUPPORTED_ASSET_CLASSES: frozenset[str] = frozenset({"venture_capital"})


@dataclass(frozen=True)
class FundWithMetrics:
    fund: FundSummary
    metrics: FundMetricSummary


class UnknownFundError(LookupError):
    """Raised when a requested fund is not in the dataset."""


def list_funds(
    asset_class: str | None = None,
    vintage_year: int | None = None,
    strategy_contains: str | None = None,
    manager_name: str | None = None,
) -> list[FundSummary]:
    funds = get_demo_funds()

    if asset_class is not None:
        normalized = asset_class.casefold()
        funds = tuple(
            fund for fund in funds if fund.asset_class.casefold() == normalized
        )

    if vintage_year is not None:
        funds = tuple(fund for fund in funds if fund.vintage_year == vintage_year)

    if strategy_contains is not None:
        needle = strategy_contains.casefold()
        funds = tuple(fund for fund in funds if needle in fund.strategy.casefold())

    if manager_name is not None:
        needle = manager_name.casefold()
        funds = tuple(fund for fund in funds if needle in fund.manager_name.casefold())

    return [_to_fund_summary(fund) for fund in funds]


def find_fund(fund_name: str) -> DemoFund | None:
    """Resolve a fund by exact name first, then by unambiguous substring."""
    needle = fund_name.strip().casefold()

    if not needle:
        return None

    for fund in get_demo_funds():
        if fund.name.casefold() == needle:
            return fund

    partial = [fund for fund in get_demo_funds() if needle in fund.name.casefold()]

    if len(partial) == 1:
        return partial[0]

    return None


def get_fund_profile(fund_name: str) -> FundWithMetrics | None:
    fund = find_fund(fund_name)

    if fund is None:
        return None

    return _to_fund_with_metrics(fund)


def get_fund_detail(fund_id: int) -> FundDetail | None:
    fund = get_demo_fund(fund_id)

    if fund is None:
        return None

    return FundDetail(
        fund=_to_fund_summary(fund),
        metrics=calculate_fund_metrics(fund.id),
        performance=get_fund_performance(fund.id) or FundPerformanceSeries(
            fund_id=fund.id, fund_name=fund.name
        ),
        cash_flows=[
            CashFlowOut(
                event_date=cash_flow.event_date,
                amount_usd=cash_flow.amount_usd,
                flow_type=cash_flow.flow_type,
            )
            for cash_flow in get_demo_cash_flows(fund.id)
        ],
        positions=[
            _to_position_out(position)
            for position in get_demo_positions({fund.id})
        ],
        sources=list_sources({fund.id}),
    )


def fund_exists(fund_id: int) -> bool:
    return get_demo_fund(fund_id) is not None


def get_fund_performance(fund_id: int) -> FundPerformanceSeries | None:
    fund = get_demo_fund(fund_id)

    if fund is None:
        return None

    points = [
        PerformancePoint(
            snapshot_date=snapshot.snapshot_date,
            nav_usd=snapshot.nav_usd,
            cumulative_distributions_usd=snapshot.cumulative_distributions_usd,
            total_value_usd=(
                snapshot.nav_usd + snapshot.cumulative_distributions_usd
            ),
        )
        for snapshot in sorted(
            get_demo_snapshots(fund_id), key=lambda item: item.snapshot_date
        )
    ]

    return FundPerformanceSeries(fund_id=fund.id, fund_name=fund.name, points=points)


def get_capital_timeline(fund_names: list[str] | None = None) -> CapitalTimeline:
    """Build the J-curve: capital called versus capital returned over time.

    This is the shape that separates private markets from public ones — money
    goes out for years before any comes back — so it is the one series worth
    plotting across the whole portfolio.
    """
    funds = [find_fund(name) for name in fund_names] if fund_names else None
    selected = (
        [fund for fund in funds if fund is not None]
        if funds is not None
        else list(get_demo_funds())
    )

    if not selected:
        return CapitalTimeline(label="No funds selected", fund_count=0)

    label = (
        selected[0].name
        if len(selected) == 1
        else f"{len(selected)} funds, aggregate"
    )

    events: dict[date, tuple[Decimal, Decimal]] = {}

    for fund in selected:
        for cash_flow in get_demo_cash_flows(fund.id):
            called, distributed = events.get(
                cash_flow.event_date, (Decimal("0"), Decimal("0"))
            )

            if cash_flow.flow_type == "capital_call":
                called += abs(cash_flow.amount_usd)
            else:
                distributed += cash_flow.amount_usd

            events[cash_flow.event_date] = (called, distributed)

    if not events:
        return CapitalTimeline(label=label, fund_count=len(selected))

    nav_by_date = _aggregate_nav_by_date(selected)
    all_dates = sorted(set(events) | set(nav_by_date))

    points: list[CapitalTimelinePoint] = []
    break_even: date | None = None
    running_called = Decimal("0")
    running_distributed = Decimal("0")

    for period_date in all_dates:
        called, distributed = events.get(period_date, (Decimal("0"), Decimal("0")))
        running_called += called
        running_distributed += distributed
        nav = _nav_as_of(nav_by_date, period_date)

        if break_even is None and running_distributed >= running_called:
            break_even = period_date

        points.append(
            CapitalTimelinePoint(
                period_date=period_date,
                cumulative_called_usd=running_called,
                cumulative_distributed_usd=running_distributed,
                nav_usd=nav,
                total_value_usd=(
                    running_distributed + nav if nav is not None else None
                ),
            )
        )

    return CapitalTimeline(
        label=label,
        fund_count=len(selected),
        break_even_date=break_even,
        points=points,
    )


def _aggregate_nav_by_date(funds: list[DemoFund]) -> dict[date, dict[int, Decimal]]:
    """NAV per fund keyed by snapshot date, so gaps can be carried forward."""
    by_date: dict[date, dict[int, Decimal]] = {}

    for fund in funds:
        for snapshot in get_demo_snapshots(fund.id):
            by_date.setdefault(snapshot.snapshot_date, {})[fund.id] = (
                snapshot.nav_usd
            )

    return by_date


def _nav_as_of(
    nav_by_date: dict[date, dict[int, Decimal]], period_date: date
) -> Decimal | None:
    """Sum each fund's most recent NAV mark on or before this date."""
    latest: dict[int, Decimal] = {}

    for snapshot_date in sorted(nav_by_date):
        if snapshot_date > period_date:
            break

        latest.update(nav_by_date[snapshot_date])

    if not latest:
        return None

    return sum(latest.values(), Decimal("0"))


def get_top_performers(metric: str = "moic", limit: int = 5) -> list[FundWithMetrics]:
    normalized_metric = metric.casefold()

    if normalized_metric not in RANKABLE_METRICS:
        raise ValueError(
            "metric must be one of " + ", ".join(sorted(RANKABLE_METRICS))
        )

    if limit < 1:
        return []

    funds_with_metrics = [_to_fund_with_metrics(fund) for fund in get_demo_funds()]

    return sorted(
        funds_with_metrics,
        key=lambda item: getattr(item.metrics, normalized_metric) or Decimal("0"),
        reverse=True,
    )[:limit]


def compare_funds(fund_names: list[str]) -> list[FundWithMetrics]:
    compared: list[FundWithMetrics] = []
    seen: set[int] = set()

    for name in fund_names:
        fund = find_fund(name)

        if fund is None or fund.id in seen:
            continue

        seen.add(fund.id)
        compared.append(_to_fund_with_metrics(fund))

    return compared


def get_vintage_year_summary(
    vintage_year: int | None = None,
) -> list[VintageYearSummary]:
    grouped: dict[int, list[DemoFund]] = {}

    for fund in get_demo_funds():
        if vintage_year is not None and fund.vintage_year != vintage_year:
            continue

        grouped.setdefault(fund.vintage_year, []).append(fund)

    summaries: list[VintageYearSummary] = []

    for year in sorted(grouped):
        funds = grouped[year]
        metrics = [calculate_fund_metrics(fund.id) for fund in funds]

        summaries.append(
            VintageYearSummary(
                vintage_year=year,
                fund_count=len(funds),
                median_irr=_median_metric(metrics, "irr"),
                median_moic=_median_metric(metrics, "moic"),
                total_fund_size_usd=sum(
                    (fund.fund_size_usd for fund in funds), Decimal("0")
                ),
                fund_names=[fund.name for fund in funds],
            )
        )

    return summaries


def get_sector_exposure(fund_names: list[str] | None = None) -> list[SectorExposure]:
    fund_ids: set[int] | None = None

    if fund_names:
        resolved = [find_fund(name) for name in fund_names]
        fund_ids = {fund.id for fund in resolved if fund is not None}

        if not fund_ids:
            return []

    positions = get_demo_positions(fund_ids)

    if not positions:
        return []

    total_value = sum(
        (position.current_value_usd for position in positions), Decimal("0")
    )

    grouped: dict[str, list[DemoPosition]] = {}

    for position in positions:
        grouped.setdefault(position.sector, []).append(position)

    exposures = [
        SectorExposure(
            sector=sector,
            invested_usd=sum(
                (item.invested_usd for item in sector_positions), Decimal("0")
            ),
            current_value_usd=sum(
                (item.current_value_usd for item in sector_positions), Decimal("0")
            ),
            share_of_value=_share_of(
                sum(
                    (item.current_value_usd for item in sector_positions),
                    Decimal("0"),
                ),
                total_value,
            ),
            company_count=len(sector_positions),
        )
        for sector, sector_positions in grouped.items()
    ]

    return sorted(exposures, key=lambda item: item.current_value_usd, reverse=True)


def calculate_fund_metrics(fund_id: int) -> FundMetricSummary:
    cash_flows = get_demo_cash_flows(fund_id)
    residual_value = latest_nav(fund_id)

    if not cash_flows:
        return FundMetricSummary()

    irr_flows = with_residual_value(
        cash_flows, residual_value, as_of=latest_snapshot_date(fund_id)
    )

    return FundMetricSummary(
        irr=_to_decimal(calculate_irr(irr_flows), places=6),
        moic=_to_decimal(calculate_moic(cash_flows, residual_value), places=4),
        tvpi=_to_decimal(calculate_tvpi(cash_flows, residual_value), places=4),
        dpi=_to_decimal(calculate_dpi(cash_flows), places=4),
        rvpi=_to_decimal(calculate_rvpi(cash_flows, residual_value), places=4),
        paid_in_usd=total_paid_in(cash_flows),
        distributed_usd=total_distributions(cash_flows),
        residual_value_usd=residual_value,
    )


def latest_nav(fund_id: int) -> Decimal | None:
    snapshots = get_demo_snapshots(fund_id)

    if not snapshots:
        return None

    return max(snapshots, key=lambda snapshot: snapshot.snapshot_date).nav_usd


def latest_snapshot_date(fund_id: int):
    snapshots = get_demo_snapshots(fund_id)

    if not snapshots:
        return None

    return max(snapshot.snapshot_date for snapshot in snapshots)


def list_sources(fund_ids: set[int] | None = None) -> list[SourceReferenceOut]:
    return [
        SourceReferenceOut(
            source_name=source.source_name,
            source_url=source.source_url,
            field_name=source.field_name,
            confidence=source.confidence,
            data_status=source.data_status,
            notes=source.notes,
        )
        for source in get_demo_sources(fund_ids)
    ]


METHODOLOGY_NOTES: dict[str, MethodologyNote] = {
    "irr": MethodologyNote(
        metric="irr",
        definition=(
            "Internal rate of return: the annualized discount rate at which "
            "the net present value of all fund cash flows equals zero."
        ),
        formula="solve for r where sum(cash_flow / (1 + r) ** years) == 0",
        caveats=[
            "Calculated XIRR-style from actual cash-flow dates, not even periods.",
            "Remaining NAV is treated as a distribution on the latest valuation "
            "date so unrealized funds still produce a figure.",
            "IRR is highly sensitive to cash-flow timing and to the NAV mark.",
        ],
    ),
    "moic": MethodologyNote(
        metric="moic",
        definition=(
            "Multiple on invested capital: total value (distributions plus "
            "remaining NAV) divided by capital paid in."
        ),
        formula="(distributions + residual_nav) / paid_in_capital",
        caveats=[
            "MOIC ignores timing, so a 2.0x over three years and over ten "
            "years look identical.",
            "Includes unrealized NAV, which is a mark rather than cash.",
        ],
    ),
    "dpi": MethodologyNote(
        metric="dpi",
        definition=(
            "Distributions to paid-in: realized cash returned to limited "
            "partners per dollar of capital called."
        ),
        formula="distributions / paid_in_capital",
        caveats=[
            "DPI excludes unrealized value, so young funds sit near zero.",
        ],
    ),
    "tvpi": MethodologyNote(
        metric="tvpi",
        definition=(
            "Total value to paid-in: realized distributions plus remaining "
            "NAV, over paid-in capital."
        ),
        formula="(distributions + residual_nav) / paid_in_capital",
        caveats=[
            "Equal to MOIC as AltLens defines it.",
            "Depends on the manager's NAV mark, which is not independently "
            "verified in the demo dataset.",
        ],
    ),
    "rvpi": MethodologyNote(
        metric="rvpi",
        definition=(
            "Residual value to paid-in: unrealized NAV per dollar of capital "
            "called."
        ),
        formula="residual_nav / paid_in_capital",
        caveats=[
            "Entirely dependent on valuation marks.",
        ],
    ),
}


def explain_metric_methodology(metric: str) -> MethodologyNote | None:
    return METHODOLOGY_NOTES.get(metric.casefold())


def _median_metric(
    metrics: list[FundMetricSummary], attribute: str
) -> Decimal | None:
    values = [
        getattr(metric, attribute)
        for metric in metrics
        if getattr(metric, attribute) is not None
    ]

    if not values:
        return None

    return Decimal(str(median(float(value) for value in values))).quantize(
        Decimal("0.0001")
    )


def _share_of(value: Decimal, total: Decimal) -> Decimal:
    if total == 0:
        return Decimal("0.0000")

    return (value / total).quantize(Decimal("0.0001"))


def _to_fund_summary(fund: DemoFund) -> FundSummary:
    return FundSummary(
        id=fund.id,
        name=fund.name,
        manager_name=fund.manager_name,
        asset_class=fund.asset_class,
        vintage_year=fund.vintage_year,
        fund_size_usd=fund.fund_size_usd,
        strategy=fund.strategy,
        geography=fund.geography,
        description=fund.description or None,
        data_quality=fund.data_quality,
    )


def _to_position_out(position: DemoPosition) -> PortfolioPositionOut:
    return PortfolioPositionOut(
        fund_id=position.fund_id,
        company_name=position.company_name,
        sector=position.sector,
        stage=position.stage,
        invested_usd=position.invested_usd,
        current_value_usd=position.current_value_usd,
        status=position.status,
    )


def _to_fund_with_metrics(fund: DemoFund) -> FundWithMetrics:
    return FundWithMetrics(
        fund=_to_fund_summary(fund),
        metrics=calculate_fund_metrics(fund.id),
    )


def _to_decimal(value: float, places: int) -> Decimal:
    quantizer = Decimal("1").scaleb(-places)
    return Decimal(str(value)).quantize(quantizer)
