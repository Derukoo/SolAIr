"""
REST endpoints for alert management.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(
    device_id: Optional[str] = None,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List alerts with optional filters."""
    conditions = []
    params = {"limit": limit}

    if device_id is not None:
        conditions.append("device_id = :device_id")
        params["device_id"] = device_id
    if severity is not None:
        conditions.append("severity = :severity")
        params["severity"] = severity
    if acknowledged is not None:
        conditions.append("acknowledged = :acknowledged")
        params["acknowledged"] = acknowledged

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    query = f"SELECT id, created_at, device_id, metric, severity, alert_type, message, value, threshold, acknowledged, acknowledged_at FROM alerts{where} ORDER BY created_at DESC LIMIT :limit"

    result = await db.execute(text(query), params)
    rows = result.fetchall()
    return [
        {
            "id": r[0],
            "created_at": r[1].isoformat(),
            "device_id": r[2],
            "metric": r[3],
            "severity": r[4],
            "alert_type": r[5],
            "message": r[6],
            "value": r[7],
            "threshold": r[8],
            "acknowledged": r[9],
            "acknowledged_at": r[10].isoformat() if r[10] else None,
        }
        for r in rows
    ]


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    """Mark an alert as acknowledged."""
    now = datetime.now(timezone.utc)
    await db.execute(
        text("UPDATE alerts SET acknowledged = true, acknowledged_at = :now WHERE id = :id"),
        {"id": alert_id, "now": now},
    )
    await db.commit()
    return {"status": "ok", "alert_id": alert_id}


@router.get("/summary")
async def alert_summary(db: AsyncSession = Depends(get_db)):
    """Count of active (unacknowledged) alerts grouped by severity."""
    result = await db.execute(
        text("""
            SELECT severity, COUNT(*) FROM alerts
            WHERE acknowledged = false
            GROUP BY severity
        """)
    )
    rows = result.fetchall()
    return {r[0]: r[1] for r in rows}
