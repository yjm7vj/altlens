from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Fund(Base):
    __tablename__ = "funds"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    manager_name: Mapped[str | None] = mapped_column(String(255))
    asset_class: Mapped[str] = mapped_column(
        String(50), nullable=False, default="venture_capital"
    )
    vintage_year: Mapped[int | None]
    fund_size_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    strategy: Mapped[str | None] = mapped_column(String(255))
    geography: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    data_quality: Mapped[str] = mapped_column(
        String(50), nullable=False, default="illustrative"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    cash_flows: Mapped[list[CashFlowEvent]] = relationship(
        back_populates="fund", cascade="all, delete-orphan"
    )
    performance_snapshots: Mapped[list[PerformanceSnapshot]] = relationship(
        back_populates="fund", cascade="all, delete-orphan"
    )
    metrics: Mapped[FundMetrics | None] = relationship(
        back_populates="fund", cascade="all, delete-orphan"
    )
    sources: Mapped[list[SourceReference]] = relationship(
        back_populates="fund", cascade="all, delete-orphan"
    )
    positions: Mapped[list[PortfolioPosition]] = relationship(
        back_populates="fund", cascade="all, delete-orphan"
    )


class CashFlowEvent(Base):
    __tablename__ = "cash_flows"

    id: Mapped[int] = mapped_column(primary_key=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id", ondelete="CASCADE"))
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    flow_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    fund: Mapped[Fund] = relationship(back_populates="cash_flows")


class PerformanceSnapshot(Base):
    __tablename__ = "performance_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id", ondelete="CASCADE"))
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    nav_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    cumulative_distributions_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    fund: Mapped[Fund] = relationship(back_populates="performance_snapshots")


class FundMetrics(Base):
    __tablename__ = "fund_metrics"

    fund_id: Mapped[int] = mapped_column(
        ForeignKey("funds.id", ondelete="CASCADE"), primary_key=True
    )
    irr: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    moic: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    tvpi: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    dpi: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    last_calculated: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    fund: Mapped[Fund] = relationship(back_populates="metrics")


class PortfolioPosition(Base):
    """A portfolio company held by a fund, used for sector-exposure analysis."""

    __tablename__ = "portfolio_positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id", ondelete="CASCADE"))
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(100))
    stage: Mapped[str | None] = mapped_column(String(50))
    invested_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    current_value_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    fund: Mapped[Fund] = relationship(back_populates="positions")


class SourceReference(Base):
    __tablename__ = "source_references"

    id: Mapped[int] = mapped_column(primary_key=True)
    fund_id: Mapped[int | None] = mapped_column(
        ForeignKey("funds.id", ondelete="CASCADE")
    )
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    field_name: Mapped[str | None] = mapped_column(String(100))
    confidence: Mapped[str] = mapped_column(String(50), nullable=False, default="low")
    data_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="illustrative"
    )
    notes: Mapped[str | None] = mapped_column(Text)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    fund: Mapped[Fund | None] = relationship(back_populates="sources")
