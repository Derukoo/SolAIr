-- SolAIr TimescaleDB schema

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Core time-series table: one row per sensor reading
CREATE TABLE sensor_data (
    time        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    device_id   TEXT        NOT NULL,
    metric      TEXT        NOT NULL,
    value       DOUBLE PRECISION NOT NULL
);

-- Convert to a hypertable (TimescaleDB), partitioned by time
SELECT create_hypertable('sensor_data', 'time');

-- Index for common query patterns
CREATE INDEX idx_sensor_device_metric ON sensor_data (device_id, metric, time DESC);

-- Alerts table
CREATE TABLE alerts (
    id          SERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    device_id   TEXT NOT NULL,
    metric      TEXT NOT NULL,
    severity    TEXT NOT NULL DEFAULT 'warning',  -- 'info', 'warning', 'critical'
    alert_type  TEXT NOT NULL,                    -- 'threshold', 'zscore', 'drift'
    message     TEXT NOT NULL,
    value       DOUBLE PRECISION,
    threshold   DOUBLE PRECISION,
    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ
);

CREATE INDEX idx_alerts_active ON alerts (acknowledged, created_at DESC);
CREATE INDEX idx_alerts_device ON alerts (device_id, created_at DESC);

-- Continuous aggregate for hourly downsampling
CREATE MATERIALIZED VIEW sensor_data_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    device_id,
    metric,
    AVG(value)    AS avg_value,
    MIN(value)    AS min_value,
    MAX(value)    AS max_value,
    STDDEV(value) AS stddev_value,
    COUNT(*)      AS sample_count
FROM sensor_data
GROUP BY bucket, device_id, metric
WITH NO DATA;

-- Refresh policy: materialize hourly aggregates automatically
SELECT add_continuous_aggregate_policy('sensor_data_hourly',
    start_offset    => INTERVAL '3 hours',
    end_offset      => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);

-- Continuous aggregate for daily downsampling
CREATE MATERIALIZED VIEW sensor_data_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS bucket,
    device_id,
    metric,
    AVG(value)    AS avg_value,
    MIN(value)    AS min_value,
    MAX(value)    AS max_value,
    STDDEV(value) AS stddev_value,
    COUNT(*)      AS sample_count
FROM sensor_data
GROUP BY bucket, device_id, metric
WITH NO DATA;

SELECT add_continuous_aggregate_policy('sensor_data_daily',
    start_offset    => INTERVAL '3 days',
    end_offset      => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day'
);

-- Data retention: drop raw data older than 90 days (aggregates survive)
SELECT add_retention_policy('sensor_data', INTERVAL '90 days');
