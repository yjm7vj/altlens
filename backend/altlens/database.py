"""Async database access.

The API currently serves the illustrative demo dataset from memory, so the
demo runs with no database at all. This module is what the ingestion path and
the seed script use, and it is where the API will read from once verified
private-market data exists.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from altlens.config import Settings, settings as default_settings
from altlens.models import Base

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


class DatabaseNotConfiguredError(RuntimeError):
    """Raised when database access is attempted with no database URL set."""


def normalize_database_url(url: str) -> str:
    """Point plain `postgresql://` URLs at the async driver.

    Hosting providers hand out `postgres://` or `postgresql://` URLs, which
    SQLAlchemy's async engine cannot use directly.
    """
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]

    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]

    return url


def is_configured(settings: Settings | None = None) -> bool:
    settings = settings or default_settings
    return bool(settings.database_url)


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    global _engine

    settings = settings or default_settings

    if not settings.database_url:
        raise DatabaseNotConfiguredError(
            "No database URL configured. Set ALTLENS_DATABASE_URL (or "
            "DATABASE_URL) to use the database-backed data path."
        )

    if _engine is None:
        _engine = create_async_engine(
            normalize_database_url(settings.database_url),
            pool_pre_ping=True,
        )

    return _engine


def get_session_factory(
    settings: Settings | None = None,
) -> async_sessionmaker[AsyncSession]:
    global _session_factory

    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(settings),
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _session_factory


@asynccontextmanager
async def session_scope(
    settings: Settings | None = None,
) -> AsyncIterator[AsyncSession]:
    """Transactional session scope: commit on success, roll back on failure."""
    factory = get_session_factory(settings)
    session = factory()

    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_session(
    settings: Settings | None = None,
) -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a session."""
    async with session_scope(settings) as session:
        yield session


async def create_all(settings: Settings | None = None) -> None:
    engine = get_engine(settings)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def drop_all(settings: Settings | None = None) -> None:
    engine = get_engine(settings)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


async def dispose_engine() -> None:
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()

    _engine = None
    _session_factory = None
