"""
REST endpoints for querying sensor data with time-windowing,
aggregation, and downsampling.
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db

# Allowed interval pattern: digits + unit (prevents SQL injection in bucket literal)
_BUCKET_RE = re.compile(r"^\d+\s+(seconds?|minutes?|hours?|days?|weeks?|months?)$", re.IGNORECASE)

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/devices")
async def list_devices(db: AsyncSession = Depends(get_db)):
    """Return all known device IDs."""
    result = await db.execute(text("SELECT DISTINCT device_id FROM sensor_data ORDER BY device_id"))
    return [row[0] for row in result.fetchall()]


@router.get("/metrics")
async def list_metrics(db: AsyncSession = Depends(get_db)):
    """Return all known metric names."""
    result = await db.execute(text("SELECT DISTINCT metric FROM sensor_data ORDER BY metric"))
    return [row[0] for row in result.fetchall()]


@router.get("/raw")
async def get_raw_data(
    device_id: str,
    metric: str,
    start: Optional[datetime] = Query(None, description="ISO 8601 start time"),
    end: Optional[datetime] = Query(None, description="ISO 8601 end time"),
    limit: int = Query(1000, le=10000),
    db: AsyncSession = Depends(get_db),
):
    """Return raw sensor readings for a device+metric within a time range."""
    now = datetime.now(timezone.utc)
    if end is None:
        end = now
    if start is None:
        start = end - timedelta(hours=1)

    result = await db.execute(
        text("""
            SELECT time, value
            FROM sensor_data
            WHERE device_id = :device_id AND metric = :metric
              AND time >= :start AND time <= :end
            ORDER BY time DESC
            LIMIT :limit
        """),
        {"device_id": device_id, "metric": metric, "start": start, "end": end, "limit": limit},
    )
    rows = result.fetchall()
    return [{"time": r[0].isoformat(), "value": r[1]} for r in rows]


@router.get("/aggregate")
async def get_aggregate(
    device_id: str,
    metric: str,
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    bucket: str = Query("1 hour", description="Time bucket size, e.g. '5 minutes', '1 hour', '1 day'"),
    db: AsyncSession = Depends(get_db),
):
    """
    Return downsampled/aggregated data using TimescaleDB time_bucket.
    Returns avg, min, max, stddev, count per bucket.
    """
    if not _BUCKET_RE.match(bucket):
        raise HTTPException(status_code=400, detail=f"Invalid bucket interval: {bucket}")

    now = datetime.now(timezone.utc)
    if end is None:
        end = now
    if start is None:
        start = end - timedelta(hours=24)

    result = await db.execute(
        text(f"""
            SELECT
                time_bucket(INTERVAL '{bucket}', time) AS bucket,
                AVG(value)    AS avg_value,
                MIN(value)    AS min_value,
                MAX(value)    AS max_value,
                STDDEV(value) AS stddev_value,
                COUNT(*)      AS sample_count
            FROM sensor_data
            WHERE device_id = :device_id AND metric = :metric
              AND time >= :start AND time <= :end
            GROUP BY bucket
            ORDER BY bucket DESC
        """),
        {"device_id": device_id, "metric": metric, "start": start, "end": end},
    )
    rows = result.fetchall()
    return [
        {
            "time": r[0].isoformat(),
            "avg": r[1],
            "min": r[2],
            "max": r[3],
            "stddev": r[4],
            "count": r[5],
        }
        for r in rows
    ]


@router.get("/latest")
async def get_latest(
    device_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Return the most recent reading for each device+metric pair."""
    query = """
        SELECT DISTINCT ON (device_id, metric)
            device_id, metric, value, time
        FROM sensor_data
    """
    params = {}
    if device_id:
        query += " WHERE device_id = :device_id"
        params["device_id"] = device_id

    query += " ORDER BY device_id, metric, time DESC"

    result = await db.execute(text(query), params)
    rows = result.fetchall()
    return [
        {"device_id": r[0], "metric": r[1], "value": r[2], "time": r[3].isoformat()}
        for r in rows
    ]
