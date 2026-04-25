# Testing

Tests run inside the backend container against the live TimescaleDB instance.
Each test uses a database transaction that is rolled back after completion,
so no test data persists.

---

## Running Tests

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

---

## Test Structure

| File | Covers | Count |
|---|---|---|
| `tests/test_routes_data.py` | `/api/health`, `/api/data/*` endpoints | 11 |
| `tests/test_routes_alerts.py` | `/api/alerts/*` endpoints | 6 |
| `tests/test_mqtt_ingestion.py` | MQTT message parsing, topic/payload validation, DB insert | 4 |

---

## Fixtures

Defined in `tests/conftest.py`:

- **`client`** — FastAPI test client with an empty transaction. Use for testing
  endpoints with no data or when you seed data within the test.
- **`seeded_client`** — Same as `client` but pre-loaded with sensor readings
  (unit-0: 5 temperature + 1 humidity, unit-1: 1 temperature) and 2 alerts
  (1 warning, 1 critical). Rolled back after the test.

Both fixtures override the `get_db` dependency so requests use the test
transaction instead of the production connection pool.

---

## Manual Verification

With the stack running (`docker compose up -d`):

### Endpoint Testing

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/data/devices
curl http://localhost:8000/api/data/latest
curl "http://localhost:8000/api/data/raw?device_id=solair-unit-0&metric=temperature"
curl "http://localhost:8000/api/data/aggregate?device_id=solair-unit-0&metric=temperature&bucket=5 minutes"
curl "http://localhost:8000/api/alerts?acknowledged=false"
curl http://localhost:8000/api/alerts/summary
curl -X POST http://localhost:8000/api/alerts/1/acknowledge
```

### MQTT Testing

```bash
# Subscribe to all topics
mosquitto_sub -h localhost -t "solair/#"

# Publish a test reading
mosquitto_pub -h localhost -t "solair/test-device/temperature" -m "25.5"

# Verify it arrived
curl "http://localhost:8000/api/data/latest?device_id=test-device"

# Or subscribe from inside the container
docker compose exec mosquitto mosquitto_sub -t "solair/#"
```

### Database Inspection

```bash
# Row count
docker compose exec timescaledb psql -U solair -c "SELECT COUNT(*) FROM sensor_data;"

# Latest 10 readings
docker compose exec timescaledb psql -U solair -c \
  "SELECT time, device_id, metric, value FROM sensor_data ORDER BY time DESC LIMIT 10;"

# Check alerts
docker compose exec timescaledb psql -U solair -c \
  "SELECT * FROM alerts ORDER BY created_at DESC LIMIT 5;"
```
