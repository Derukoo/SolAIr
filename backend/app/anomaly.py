"""
Anomaly detection engine.

Runs periodically and checks recent sensor data for:
1. Static threshold violations
2. Z-score deviations from rolling baseline
3. Long-term drift (baseline shift over weeks)
"""

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import create_engine, text

from .config import settings

logger = logging.getLogger("solair.anomaly")

# Static thresholds: metric -> (min, max, severity)
THRESHOLDS = {
    "temperature": (None, 40.0, "critical"),
    "humidity": (None, 85.0, "warning"),
    "voltage": (None, 16.5, "critical"),
    "current": (None, 5.0, "critical"),
}

# Z-score config
ZSCORE_WINDOW_HOURS = 24
ZSCORE_THRESHOLD = 3.0

# Drift config: compare last 7 days vs prior 30 days
DRIFT_RECENT_DAYS = 7
DRIFT_BASELINE_DAYS = 30
DRIFT_STDDEV_MULTIPLIER = 2.0


def _get_engine():
    return create_engine(settings.database_url_sync, pool_pre_ping=True)


def _insert_alert(conn, device_id, metric, severity, alert_type, message, value, threshold):
    conn.execute(
        text("""
            INSERT INTO alerts (device_id, metric, severity, alert_type, message, value, threshold)
            VALUES (:device_id, :metric, :severity, :alert_type, :message, :value, :threshold)
        """),
        {
            "device_id": device_id,
            "metric": metric,
            "severity": severity,
            "alert_type": alert_type,
            "message": message,
            "value": value,
            "threshold": threshold,
        },
    )


def _has_recent_alert(conn, device_id, metric, alert_type, minutes=30):
    """Prevent alert spam: check if a similar alert was raised recently."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    result = conn.execute(
        text("""
            SELECT COUNT(*) FROM alerts
            WHERE device_id = :d AND metric = :m AND alert_type = :t AND created_at > :c
        """),
        {"d": device_id, "m": metric, "t": alert_type, "c": cutoff},
    )
    return result.scalar() > 0


def check_thresholds():
    """Check latest readings against static thresholds."""
    engine = _get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT DISTINCT ON (device_id, metric)
                    device_id, metric, value
                FROM sensor_data
                WHERE time > NOW() - INTERVAL '5 minutes'
                ORDER BY device_id, metric, time DESC
            """)
        )

        for device_id, metric, value in result.fetchall():
            if metric not in THRESHOLDS:
                continue

            low, high, severity = THRESHOLDS[metric]

            if high is not None and value > high:
                if not _has_recent_alert(conn, device_id, metric, "threshold"):
                    _insert_alert(
                        conn, device_id, metric, severity, "threshold",
                        f"{metric} = {value:.2f} exceeds max threshold {high}",
                        value, high,
                    )
            if low is not None and value < low:
                if not _has_recent_alert(conn, device_id, metric, "threshold"):
                    _insert_alert(
                        conn, device_id, metric, severity, "threshold",
                        f"{metric} = {value:.2f} below min threshold {low}",
                        value, low,
                    )

        conn.commit()


def check_zscore():
    """Detect readings that deviate significantly from the rolling baseline."""
    engine = _get_engine()
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=ZSCORE_WINDOW_HOURS)

    with engine.connect() as conn:
        # Get baseline stats per device+metric over the window
        stats = conn.execute(
            text("""
                SELECT device_id, metric, AVG(value), STDDEV(value)
                FROM sensor_data
                WHERE time >= :start
                GROUP BY device_id, metric
                HAVING STDDEV(value) > 0 AND COUNT(*) >= 30
            """),
            {"start": window_start},
        ).fetchall()

        for device_id, metric, avg, stddev in stats:
            # Check most recent reading
            latest = conn.execute(
                text("""
                    SELECT value FROM sensor_data
                    WHERE device_id = :d AND metric = :m
                    ORDER BY time DESC LIMIT 1
                """),
                {"d": device_id, "m": metric},
            ).fetchone()

            if latest is None:
                continue

            zscore = abs(latest[0] - avg) / stddev
            if zscore >= ZSCORE_THRESHOLD:
                if not _has_recent_alert(conn, device_id, metric, "zscore"):
                    _insert_alert(
                        conn, device_id, metric, "warning", "zscore",
                        f"{metric} Z-score = {zscore:.1f} (value={latest[0]:.2f}, "
                        f"baseline avg={avg:.2f}, stddev={stddev:.2f})",
                        latest[0], ZSCORE_THRESHOLD,
                    )

        conn.commit()


def check_drift():
    """Detect gradual baseline shifts by comparing recent vs historical averages."""
    engine = _get_engine()
    now = datetime.now(timezone.utc)

    with engine.connect() as conn:
        # Get historical baseline (30-day avg and stddev, excluding last 7 days)
        baseline_start = now - timedelta(days=DRIFT_BASELINE_DAYS + DRIFT_RECENT_DAYS)
        baseline_end = now - timedelta(days=DRIFT_RECENT_DAYS)

        baselines = conn.execute(
            text("""
                SELECT device_id, metric, AVG(value), STDDEV(value)
                FROM sensor_data
                WHERE time >= :start AND time < :end
                GROUP BY device_id, metric
                HAVING STDDEV(value) > 0 AND COUNT(*) >= 100
            """),
            {"start": baseline_start, "end": baseline_end},
        ).fetchall()

        for device_id, metric, hist_avg, hist_stddev in baselines:
            # Get recent average (last 7 days)
            recent = conn.execute(
                text("""
                    SELECT AVG(value) FROM sensor_data
                    WHERE device_id = :d AND metric = :m
                      AND time >= :start
                    HAVING COUNT(*) >= 30
                """),
                {"d": device_id, "m": metric, "start": baseline_end},
            ).fetchone()

            if recent is None or recent[0] is None:
                continue

            drift = abs(recent[0] - hist_avg)
            if drift > DRIFT_STDDEV_MULTIPLIER * hist_stddev:
                if not _has_recent_alert(conn, device_id, metric, "drift", minutes=1440):
                    _insert_alert(
                        conn, device_id, metric, "info", "drift",
                        f"{metric} baseline drift: recent avg={recent[0]:.2f} vs "
                        f"historical avg={hist_avg:.2f} (shift={drift:.2f}, "
                        f"threshold={DRIFT_STDDEV_MULTIPLIER * hist_stddev:.2f})",
                        recent[0], hist_avg,
                    )

        conn.commit()


def _run_all_checks():
    try:
        check_thresholds()
        check_zscore()
        check_drift()
    except Exception:
        logger.exception("Anomaly detection cycle failed")


def start_anomaly_scheduler():
    """Start the anomaly detection on a 60-second interval."""
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(_run_all_checks, "interval", seconds=60, id="anomaly_checks")
    scheduler.start()
    logger.info("Anomaly detection scheduler started (60s interval)")
    return scheduler
