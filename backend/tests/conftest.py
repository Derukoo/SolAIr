"""
Shared fixtures for backend tests.

Runs against the real TimescaleDB instance to exercise PostgreSQL-specific
features (DISTINCT ON, time_bucket, etc.). Tests use a transaction that
is rolled back after each test to avoid polluting the database.
"""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import get_db
from app.main import app


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(settings.database_url, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Session wrapped in a transaction that rolls back after the test."""
    conn = await db_engine.connect()
    trans = await conn.begin()
    session = AsyncSession(bind=conn)
    yield session
    await session.close()
    await trans.rollback()
    await conn.close()


@pytest_asyncio.fixture
async def client(db_engine):
    """AsyncClient with a rolled-back transaction — starts with empty tables."""
    conn = await db_engine.connect()
    trans = await conn.begin()

    async def _override_get_db():
        session = AsyncSession(bind=conn)
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await trans.rollback()
    await conn.close()


@pytest_asyncio.fixture
async def seeded_client(db_engine):
    """Client with pre-seeded sensor data and alerts, rolled back after test."""
    conn = await db_engine.connect()
    trans = await conn.begin()

    # Use a nested savepoint for seeding
    now = datetime.now(timezone.utc)

    # Sensor readings — spread across a few seconds so ordering is deterministic
    for i in range(5):
        t = now - timedelta(seconds=10 - i)
        await conn.execute(
            text("INSERT INTO sensor_data (time, device_id, metric, value) VALUES (:t, :d, :m, :v)"),
            {"t": t, "d": "unit-0", "m": "temperature", "v": 22.0 + i},
        )
    await conn.execute(
        text("INSERT INTO sensor_data (time, device_id, metric, value) VALUES (:t, :d, :m, :v)"),
        {"t": now, "d": "unit-0", "m": "humidity", "v": 55.0},
    )
    await conn.execute(
        text("INSERT INTO sensor_data (time, device_id, metric, value) VALUES (:t, :d, :m, :v)"),
        {"t": now, "d": "unit-1", "m": "temperature", "v": 30.0},
    )

    # Alerts
    await conn.execute(
        text("""INSERT INTO alerts (device_id, metric, severity, alert_type, message, value, threshold)
                VALUES (:d, :m, :s, :at, :msg, :v, :th)"""),
        {"d": "unit-0", "m": "temperature", "s": "warning", "at": "threshold",
         "msg": "Temperature high", "v": 41.0, "th": 40.0},
    )
    await conn.execute(
        text("""INSERT INTO alerts (device_id, metric, severity, alert_type, message, value, threshold)
                VALUES (:d, :m, :s, :at, :msg, :v, :th)"""),
        {"d": "unit-0", "m": "voltage", "s": "critical", "at": "threshold",
         "msg": "Voltage too high", "v": 17.0, "th": 16.5},
    )

    async def _override_get_db():
        session = AsyncSession(bind=conn)
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await trans.rollback()
    await conn.close()
