# REST API Reference

Base URL: `http://localhost:8000`

---

## Health

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Service health check — returns `{"status": "ok"}` |

---

## Data Endpoints

### GET `/api/data/devices`

List all known device IDs. No parameters.

```bash
curl http://localhost:8000/api/data/devices
# ["solair-unit-0", "solair-unit-1"]
```

### GET `/api/data/metrics`

List all known metric names. No parameters.

```bash
curl http://localhost:8000/api/data/metrics
# ["current", "humidity", "lux", "temperature", "voltage"]
```

### GET `/api/data/latest`

Latest reading for each device+metric pair.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `device_id` | string | no | *(all)* | Filter to a single device |

```bash
curl http://localhost:8000/api/data/latest
curl "http://localhost:8000/api/data/latest?device_id=solair-unit-0"
```

Response:
```json
[
  {"device_id": "solair-unit-0", "metric": "temperature", "value": 22.0, "time": "2026-04-18T12:35:17+00:00"}
]
```

### GET `/api/data/raw`

Raw time-series readings for a specific device+metric.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `device_id` | string | **yes** | — | Device ID |
| `metric` | string | **yes** | — | Metric name (`temperature`, `humidity`, `lux`, `voltage`, `current`) |
| `start` | ISO 8601 | no | *1 hour ago* | Start of time range |
| `end` | ISO 8601 | no | *now* | End of time range |
| `limit` | int | no | 1000 | Max rows returned (max 10000) |

```bash
curl "http://localhost:8000/api/data/raw?device_id=solair-unit-0&metric=temperature"

curl "http://localhost:8000/api/data/raw?device_id=solair-unit-0&metric=voltage&start=2026-04-18T00:00:00Z&end=2026-04-18T12:00:00Z&limit=500"
```

Response:
```json
[
  {"time": "2026-04-18T12:35:17+00:00", "value": 22.0}
]
```

### GET `/api/data/aggregate`

Downsampled aggregates using TimescaleDB `time_bucket`.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `device_id` | string | **yes** | — | Device ID |
| `metric` | string | **yes** | — | Metric name |
| `start` | ISO 8601 | no | *24 hours ago* | Start of time range |
| `end` | ISO 8601 | no | *now* | End of time range |
| `bucket` | string | no | `1 hour` | Bucket size — e.g. `5 minutes`, `1 hour`, `1 day` |

```bash
curl "http://localhost:8000/api/data/aggregate?device_id=solair-unit-0&metric=temperature&bucket=1 hour"
```

Response:
```json
[
  {"time": "2026-04-18T12:00:00+00:00", "avg": 22.3, "min": 21.0, "max": 24.0, "stddev": 0.8, "count": 150}
]
```

---

## Alert Endpoints

### GET `/api/alerts`

List alerts with optional filters.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `device_id` | string | no | *(all)* | Filter by device |
| `severity` | string | no | *(all)* | Filter by severity (`info`, `warning`, `critical`) |
| `acknowledged` | bool | no | *(all)* | Filter by acknowledgment status |
| `limit` | int | no | 100 | Max rows returned (max 1000) |

```bash
curl http://localhost:8000/api/alerts
curl "http://localhost:8000/api/alerts?severity=warning&acknowledged=false"
```

Response:
```json
[
  {
    "id": 1,
    "created_at": "2026-04-18T12:00:00+00:00",
    "device_id": "solair-unit-0",
    "metric": "temperature",
    "severity": "warning",
    "alert_type": "threshold",
    "message": "Temperature high",
    "value": 41.0,
    "threshold": 40.0,
    "acknowledged": false,
    "acknowledged_at": null
  }
]
```

### GET `/api/alerts/summary`

Count of active (unacknowledged) alerts grouped by severity. No parameters.

```bash
curl http://localhost:8000/api/alerts/summary
# {"warning": 3, "critical": 1}
```

### POST `/api/alerts/{id}/acknowledge`

Mark an alert as acknowledged.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `id` | int (path) | **yes** | Alert ID |

```bash
curl -X POST http://localhost:8000/api/alerts/1/acknowledge
# {"status": "ok", "alert_id": 1}
```
