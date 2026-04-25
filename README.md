# SolAIr — IoT Sensor Monitor & Analytics Dashboard

An end-to-end IoT platform: ESP32 firmware reads five sensors, publishes over
MQTT, and a full-stack dashboard ingests, analyzes, and visualizes the data
with anomaly detection.

---

## Architecture

```
ESP32 (firmware/)        MQTT Broker         Backend (FastAPI)         Frontend (React)
 DHT11, BH1750,    -->  Mosquitto      -->  MQTT Subscriber     -->   Dashboard
 Voltage, Current       port 1883           + REST API                KPIs, Charts,
                                            + Anomaly Engine          Alerts
                                                 |
                                            TimescaleDB
                                            (PostgreSQL)
```

---

## Project Structure

```
SolAIr/
├── firmware/                   # ESP32 PlatformIO project
│   ├── platformio.ini
│   ├── settings.ini            # WiFi/MQTT config (gitignored)
│   ├── settings.ini.example
│   ├── load_settings.py
│   ├── include/
│   │   ├── sensors.h
│   │   └── mqtt_client.h
│   └── src/
│       ├── main.cpp
│       ├── sensors.cpp
│       └── mqtt_client.cpp
├── backend/                    # FastAPI + anomaly detection
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-test.txt
│   ├── pytest.ini
│   ├── app/
│   │   ├── main.py             # FastAPI app + lifespan
│   │   ├── config.py           # Environment-based settings
│   │   ├── database.py         # Async SQLAlchemy engine
│   │   ├── models.py           # ORM models
│   │   ├── mqtt_ingestion.py   # MQTT subscriber -> TimescaleDB
│   │   ├── anomaly.py          # Threshold / Z-score / drift detection
│   │   ├── routes_data.py      # /api/data/* endpoints
│   │   └── routes_alerts.py    # /api/alerts/* endpoints
│   └── tests/
│       ├── conftest.py             # Shared fixtures (DB engine, test clients)
│       ├── test_routes_data.py     # /api/data/* endpoint tests
│       ├── test_routes_alerts.py   # /api/alerts/* endpoint tests
│       └── test_mqtt_ingestion.py  # MQTT message handling tests
├── frontend/                   # React + Vite + ApexCharts
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx             # Layout, routing, device toggles
│       ├── api.js
│       ├── index.css           # Eco theme (dark/light), layout
│       └── components/
│           ├── Sidebar.jsx     # Hamburger nav — Dashboard / Graphs / Alerts
│           ├── KPICards.jsx    # KPI grid with device filtering
│           ├── SensorChart.jsx # Charts with 2dp precision
│           └── AlertsPanel.jsx
├── db/
│   └── init/
│       └── 001_schema.sql      # TimescaleDB schema + hypertables
├── mosquitto/
│   └── config/
│       └── mosquitto.conf
├── docker-compose.yml
├── CLAUDE.md
└── README.md
```

---

## Hardware

| Component | Interface | Pin(s) |
|---|---|---|
| ESP32-DEVKITC (CP2102, WROOM-32D) | USB | -- |
| DHT11 -- Temperature & Humidity | Digital | 32 |
| GY-30 BH1750FVI -- Light (Lux) | I2C | SDA=21, SCL=22 |
| Voltage Sensor 0-25V | ADC | 36 |
| ACS712 5A -- Current | ADC | 39 |

---

## Quick Start

### 1. Start the stack

```bash
docker compose up -d
```

This starts:
- **Mosquitto** MQTT broker on port 1883
- **TimescaleDB** on port 5432 (auto-creates schema on first run)
- **Backend** API on port 8000
- **Frontend** dashboard on port 3000

### 2. Configure and flash the firmware

```bash
cd firmware
cp settings.ini.example settings.ini
# Edit settings.ini with your WiFi credentials and broker IP
```

Build and flash:

```bash
~/.platformio/penv/bin/pio run -e device_0 -t upload
```

### 3. Open the dashboard

Navigate to [http://localhost:3000](http://localhost:3000)

The dashboard has three pages accessible via the sidebar:
- **Dashboard** — KPI cards showing latest readings per device
- **Graphs** — Time-series charts for all sensors with range selectors
- **Alerts** — Alert list with severity filters and acknowledgment

Use the solar-panel toggle buttons to show/hide individual devices.
The dark/light mode switch is at the bottom of the sidebar.

---

## Firmware Configuration

Edit `firmware/settings.ini`:

```ini
[wifi]
ssid     = YOUR_WIFI_SSID
password = YOUR_WIFI_PASSWORD

[mqtt]
broker_ip   = 192.168.1.100
broker_port = 1883
topic_base  = solair

[devices]
device_0 = solair-unit-0
device_1 = solair-unit-1
```

### Multi-device support

Each PlatformIO environment maps to a device ID. To add a third board:

1. Add to `firmware/platformio.ini`:
   ```ini
   [env:device_2]
   upload_port  = /dev/ttyUSB2
   monitor_port = /dev/ttyUSB2
   ```
2. Add to `firmware/settings.ini`:
   ```ini
   device_2 = solair-unit-2
   ```

---

## MQTT Topic Structure

Each sensor publishes to its own subtopic:

```
solair/<device-id>/temperature
solair/<device-id>/humidity
solair/<device-id>/lux
solair/<device-id>/voltage
solair/<device-id>/current
```

### Wildcard subscriptions

| Pattern | Result |
|---|---|
| `solair/+/temperature` | Temperature from all devices |
| `solair/solair-unit-0/#` | All sensors from unit 0 |
| `solair/#` | Everything |

### Test with mosquitto_sub

```bash
mosquitto_sub -h localhost -t "solair/#"
```

---

## Ports Reference

| Service | Port | Protocol | Description |
|---|---|---|---|
| Mosquitto | 1883 | MQTT | Broker — receives sensor payloads from ESP32 devices |
| TimescaleDB | 5432 | PostgreSQL | Time-series database (user: `solair`, password: `solair_dev`, db: `solair`) |
| Backend | 8000 | HTTP | FastAPI REST API + MQTT ingestion + anomaly engine |
| Frontend | 3000 | HTTP | React dashboard (Vite dev server) |

---

## REST API

Base URL: `http://localhost:8000`

### Health

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Service health check — returns `{"status": "ok"}` |

### Data endpoints

#### `GET /api/data/devices`

List all known device IDs. No parameters.

```bash
curl http://localhost:8000/api/data/devices
# ["solair-unit-0", "solair-unit-1"]
```

#### `GET /api/data/metrics`

List all known metric names. No parameters.

```bash
curl http://localhost:8000/api/data/metrics
# ["current", "humidity", "lux", "temperature", "voltage"]
```

#### `GET /api/data/latest`

Latest reading for each device+metric pair.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `device_id` | string | no | *(all)* | Filter to a single device |

```bash
# All devices
curl http://localhost:8000/api/data/latest

# Single device
curl "http://localhost:8000/api/data/latest?device_id=solair-unit-0"
```

Response:
```json
[
  {"device_id": "solair-unit-0", "metric": "temperature", "value": 22.0, "time": "2026-04-18T12:35:17+00:00"},
  ...
]
```

#### `GET /api/data/raw`

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

# With explicit time range
curl "http://localhost:8000/api/data/raw?device_id=solair-unit-0&metric=voltage&start=2026-04-18T00:00:00Z&end=2026-04-18T12:00:00Z&limit=500"
```

Response:
```json
[
  {"time": "2026-04-18T12:35:17+00:00", "value": 22.0},
  ...
]
```

#### `GET /api/data/aggregate`

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
  {"time": "2026-04-18T12:00:00+00:00", "avg": 22.3, "min": 21.0, "max": 24.0, "stddev": 0.8, "count": 150},
  ...
]
```

### Alert endpoints

#### `GET /api/alerts`

List alerts with optional filters.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `device_id` | string | no | *(all)* | Filter by device |
| `severity` | string | no | *(all)* | Filter by severity (`info`, `warning`, `critical`) |
| `acknowledged` | bool | no | *(all)* | Filter by acknowledgment status |
| `limit` | int | no | 100 | Max rows returned (max 1000) |

```bash
# All alerts
curl http://localhost:8000/api/alerts

# Unacknowledged warnings only
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

#### `GET /api/alerts/summary`

Count of active (unacknowledged) alerts grouped by severity. No parameters.

```bash
curl http://localhost:8000/api/alerts/summary
# {"warning": 3, "critical": 1}
```

#### `POST /api/alerts/{id}/acknowledge`

Mark an alert as acknowledged.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `id` | int (path) | **yes** | Alert ID |

```bash
curl -X POST http://localhost:8000/api/alerts/1/acknowledge
# {"status": "ok", "alert_id": 1}
```

---

## Data Processing Pipeline

Data flows through the system in four stages:

```
1. Sensor Reads        2. MQTT Transport       3. Ingestion            4. Analysis
ESP32 (2s interval) -> Mosquitto broker    ->  Python listener    ->  Anomaly engine (60s)
 - 64-sample ADC avg    solair/<id>/<metric>    parse topic+payload    threshold check
 - NaN / range check    individual floats       INSERT sensor_data     Z-score check
 - per-metric publish                                                  drift check
```

### On-device processing (`firmware/src/sensors.cpp`)

The ESP32 performs basic signal conditioning before publishing:

- **ADC averaging**: Each analog read (voltage, current) averages 64 samples
  to reduce noise (line 19).
- **Voltage calibration**: Raw ADC value is converted using the 1:5 divider
  ratio and 3.3V / 4095-bit reference (lines 24-30).
- **Current calibration**: ACS712 output is offset-corrected (subtract 2.5V
  midpoint) and divided by the 185 mV/A sensitivity (lines 54-55).
- **Validation**: DHT11 readings are checked for NaN; lux readings are checked
  for negative values. Invalid readings are skipped (lines 46-49).

### Backend ingestion (`backend/app/mqtt_ingestion.py`)

A daemon thread subscribes to `solair/#` and for each message:
1. Parses the topic into `device_id` and `metric` (lines 36-43).
2. Converts the payload to a float with error handling (line 46).
3. Inserts into the `sensor_data` hypertable with the current UTC timestamp.

### TimescaleDB aggregation (`db/init/001_schema.sql`)

Raw data is automatically rolled up into continuous aggregates:

| Aggregate | Bucket | Stats | Refresh |
|---|---|---|---|
| `sensor_data_hourly` | 1 hour | avg, min, max, stddev, count | Every hour |
| `sensor_data_daily` | 1 day | avg, min, max, stddev, count | Every day |

A 90-day retention policy drops old raw data; aggregates are retained
indefinitely.

---

## Anomaly Detection

The anomaly engine (`backend/app/anomaly.py`) runs three complementary
algorithms every 60 seconds. All detection is server-side — the ESP32 does no
anomaly logic. No ML models are used; detection is purely statistical.

### 1. Static threshold violations (lines 73-108)

Checks the most recent reading (within the last 5 minutes) for each
device+metric against hardcoded bounds:

| Metric | Limit | Severity |
|---|---|---|
| Temperature | > 40°C | critical |
| Humidity | > 85% | warning |
| Voltage | > 16.5V | critical |
| Current | > 5.0A | critical |

Good for catching clear-cut dangerous conditions (overheating, overcurrent).

### 2. Z-score detection (lines 111-154)

Detects sudden spikes or drops relative to recent behavior, even when the
reading is within absolute thresholds.

- **Window**: 24 hours of historical data
- **Threshold**: Z-score >= 3.0 (3 standard deviations from the mean)
- **Min samples**: 30 readings required to compute a reliable baseline
- **Severity**: warning

**How it works**: For each device+metric, the engine computes the mean and
standard deviation over the last 24 hours. It then calculates
`Z = |latest_value - mean| / stddev`. A Z-score of 3+ means the reading is
statistically unusual for that sensor's recent behavior.

**Example**: If voltage averages 14.5V with stddev 0.2V over 24h, a reading
of 15.3V gives Z = (15.3-14.5)/0.2 = 4.0 — an anomaly, even though 15.3V is
well within the 16.5V absolute threshold.

### 3. Long-term drift detection (lines 157-204)

Catches gradual degradation that happens too slowly for Z-score to flag —
the key algorithm for detecting solar panel efficiency loss.

- **Baseline**: Average over days 8-37 (30-day window, excluding the recent period)
- **Recent**: Average over the last 7 days
- **Threshold**: Drift > 2x the historical standard deviation
- **Min samples**: 100 readings per period
- **Severity**: info
- **Rate limit**: Max 1 alert per device+metric per 24 hours

**How it works**: Compares the recent 7-day average against a 30-day
historical baseline. If the shift exceeds twice the historical standard
deviation, a drift alert is raised.

**Example — panel degradation**: If voltage averaged 15.5V (stddev 0.3V) over
the historical period but has dropped to 14.2V over the last 7 days, the
drift is 1.3V. The threshold is 2 × 0.3 = 0.6V. Since 1.3 > 0.6, a drift
alert fires — indicating possible panel soiling, wiring degradation, or
battery issues.

### Alert rate limiting

To prevent alert spam, each algorithm checks for recent duplicates before
inserting:

| Algorithm | Cooldown |
|---|---|
| Threshold | 30 minutes per device+metric |
| Z-score | 30 minutes per device+metric |
| Drift | 24 hours per device+metric |

### Alert lifecycle

1. Anomaly engine inserts an alert with severity, type, value, and threshold.
2. Alert appears in the dashboard's Alerts panel (auto-refreshes every 10s).
3. User acknowledges the alert via `POST /api/alerts/{id}/acknowledge`.
4. Acknowledged alerts are hidden from the default view but retained in the
   database.

---

## Database

TimescaleDB schema (`db/init/001_schema.sql`):

- **sensor_data** — hypertable partitioned by time
- **sensor_data_hourly** — continuous aggregate (auto-refreshed)
- **sensor_data_daily** — continuous aggregate (auto-refreshed)
- **alerts** — threshold/zscore/drift alerts with acknowledgment tracking
- 90-day retention policy on raw data (aggregates survive)

---

## Commands Reference

### Docker

```bash
docker compose up -d          # Start all services
docker compose down           # Stop all services
docker compose logs -f backend  # Follow backend logs
docker compose ps             # Check service status
```

### Tests

Tests run inside the backend container against the live TimescaleDB instance.
Each test uses a database transaction that is rolled back after completion,
so no test data persists.

```bash
# Install test dependencies (one-time)
docker compose exec backend pip install pytest pytest-asyncio httpx

# Run all tests
docker compose exec backend python -m pytest tests/ -v

# Run a specific test file
docker compose exec backend python -m pytest tests/test_routes_data.py -v

# Run a single test by name
docker compose exec backend python -m pytest tests/test_routes_alerts.py -k "test_acknowledge_alert" -v
```

#### Test structure

| File | Covers | Count |
|---|---|---|
| `tests/test_routes_data.py` | `/api/health`, `/api/data/*` endpoints (devices, metrics, latest, raw, aggregate) | 11 |
| `tests/test_routes_alerts.py` | `/api/alerts/*` endpoints (list, filter, summary, acknowledge) | 6 |
| `tests/test_mqtt_ingestion.py` | MQTT message parsing, topic validation, payload validation, DB insert | 4 |

#### How fixtures work

- **`client`** — FastAPI test client with an empty transaction. Good for testing
  endpoints with no data or when you seed data within the test itself.
- **`seeded_client`** — Same as `client` but pre-loaded with sensor readings
  (unit-0: 5 temperature + 1 humidity, unit-1: 1 temperature) and 2 alerts
  (1 warning, 1 critical). Rolled back after the test.

Both fixtures override the `get_db` dependency so requests use the test
transaction instead of the production connection pool.

#### Manual endpoint testing

With the stack running (`docker compose up -d`), you can test endpoints
directly with curl:

```bash
# Health check
curl http://localhost:8000/api/health

# List devices
curl http://localhost:8000/api/data/devices

# Latest readings
curl http://localhost:8000/api/data/latest

# Raw data for a device+metric
curl "http://localhost:8000/api/data/raw?device_id=solair-unit-0&metric=temperature"

# Aggregated data with 5-minute buckets
curl "http://localhost:8000/api/data/aggregate?device_id=solair-unit-0&metric=temperature&bucket=5 minutes"

# Unacknowledged alerts
curl "http://localhost:8000/api/alerts?acknowledged=false"

# Alert summary
curl http://localhost:8000/api/alerts/summary

# Acknowledge alert #1
curl -X POST http://localhost:8000/api/alerts/1/acknowledge
```

#### MQTT testing

```bash
# Subscribe to all topics (from host)
mosquitto_sub -h localhost -t "solair/#"

# Publish a test reading (from host)
mosquitto_pub -h localhost -t "solair/test-device/temperature" -m "25.5"

# Then verify it arrived in the API
curl "http://localhost:8000/api/data/latest?device_id=test-device"

# Or attach to the mosquitto container directly
docker compose exec mosquitto mosquitto_sub -t "solair/#"
```

#### Database inspection

```bash
# Row count
docker compose exec timescaledb psql -U solair -c "SELECT COUNT(*) FROM sensor_data;"

# Latest 10 readings
docker compose exec timescaledb psql -U solair -c \
  "SELECT time, device_id, metric, value FROM sensor_data ORDER BY time DESC LIMIT 10;"

# Check alerts
docker compose exec timescaledb psql -U solair -c "SELECT * FROM alerts ORDER BY created_at DESC LIMIT 5;"
```

### Firmware

```bash
cd firmware
~/.platformio/penv/bin/pio run                          # Build all devices
~/.platformio/penv/bin/pio run -e device_0 -t upload    # Flash device 0
~/.platformio/penv/bin/pio device monitor -e device_0   # Serial monitor
```
