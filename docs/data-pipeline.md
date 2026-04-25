# Data Pipeline

Data flows through the system in four stages:

```
1. Sensor Reads        2. MQTT Transport       3. Ingestion            4. Analysis
ESP32 (2s interval) -> Mosquitto broker    ->  Python listener    ->  Anomaly engine (60s)
 - 64-sample ADC avg    solair/<id>/<metric>    parse topic+payload    threshold check
 - NaN / range check    individual floats       INSERT sensor_data     Z-score check
 - per-metric publish                                                  drift check
```

---

## Stage 1: On-Device Processing

Source: `firmware/src/sensors.cpp`

The ESP32 performs basic signal conditioning before publishing:

- **ADC averaging**: Each analog read (voltage, current) averages 64 samples
  to reduce noise.
- **Voltage calibration**: Raw ADC value is converted using the 1:5 divider
  ratio and 3.3V / 4095-bit reference.
- **Current calibration**: ACS712 output is offset-corrected (subtract 2.5V
  midpoint) and divided by the 185 mV/A sensitivity.
- **Validation**: DHT11 readings are checked for NaN; lux readings are checked
  for negative values. Invalid readings are skipped entirely.

---

## Stage 2: MQTT Transport

Each sensor publishes to its own subtopic:

```
solair/<device-id>/temperature
solair/<device-id>/humidity
solair/<device-id>/lux
solair/<device-id>/voltage
solair/<device-id>/current
```

### Wildcard Subscriptions

| Pattern | Result |
|---|---|
| `solair/+/temperature` | Temperature from all devices |
| `solair/solair-unit-0/#` | All sensors from unit 0 |
| `solair/#` | Everything |

---

## Stage 3: Backend Ingestion

Source: `backend/app/mqtt_ingestion.py`

A daemon thread subscribes to `solair/#` and for each message:
1. Parses the topic into `device_id` and `metric`.
2. Converts the payload to a float with error handling.
3. Inserts into the `sensor_data` hypertable with the current UTC timestamp.

---

## Stage 4: Storage and Aggregation

Source: `db/init/001_schema.sql`

### Schema

- **sensor_data** — hypertable partitioned by time (raw readings)
- **alerts** — threshold/zscore/drift alerts with acknowledgment tracking

### Continuous Aggregates

Raw data is automatically rolled up:

| Aggregate | Bucket | Stats | Refresh |
|---|---|---|---|
| `sensor_data_hourly` | 1 hour | avg, min, max, stddev, count | Every hour |
| `sensor_data_daily` | 1 day | avg, min, max, stddev, count | Every day |

### Retention

A 90-day retention policy drops old raw data. Aggregates are retained
indefinitely.
