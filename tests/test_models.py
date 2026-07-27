from sqlalchemy import ForeignKeyConstraint

from altlens.models import Base, Fund, SourceReference


def test_core_private_market_tables_are_registered():
    assert set(Base.metadata.tables) >= {
        "funds",
        "cash_flows",
        "performance_snapshots",
        "fund_metrics",
        "source_references",
    }


def test_fund_model_tracks_private_market_context_and_data_quality():
    fund_columns = Fund.__table__.columns

    assert "manager_name" in fund_columns
    assert "vintage_year" in fund_columns
    assert "strategy" in fund_columns
    assert "geography" in fund_columns
    assert "data_quality" in fund_columns


def test_source_references_can_attach_to_funds_for_auditability():
    constraints = [
        constraint
        for constraint in SourceReference.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]

    assert any(
        "funds.id" in str(element.target_fullname)
        for constraint in constraints
        for element in constraint.elements
    )
