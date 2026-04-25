# SolAIr — Project Instructions

## Rules
- Every time the project code or structure is updated, README.md MUST be updated to reflect the changes.

## Hardware
- ESP32-DEVKITC Core Board CP2102, ESP32 Development Board ESP32-WROOM-32D
- DHT11 temperature and humidity sensor — PIN 32
- GY-30 BH1750FVI lux sensor — I2C (SCL=22, SDA=21)
- Arduino Voltage Sensor 0-25V — PIN 36
- Current Sensor ACS712 5A — PIN 39

## IoT Best Practices
- **Secure credentials**: WiFi passwords and API keys must never be committed to git. Use `settings.ini` (gitignored) with a `.example` template checked in.
- **Unique device identity**: Every device must have a unique ID used in MQTT client-id and topic paths to avoid broker collisions.
- **Resilient connectivity**: WiFi and MQTT connections must auto-reconnect on failure without blocking sensor reads longer than necessary.
- **Structured payloads**: Always publish sensor data as JSON with `device_id` and a timestamp/millis field so consumers can correlate and deduplicate.
- **Minimal blocking**: Avoid long `delay()` calls in the main loop. Prefer non-blocking timing (`millis()` checks) where possible; the current 2s delay is acceptable because the DHT11 requires it.
- **Modular firmware**: Keep sensor logic, network logic, and orchestration in separate compilation units (`sensors.cpp`, `mqtt_client.cpp`, `main.cpp`).
- **Topic hierarchy**: Use a structured MQTT topic scheme (e.g., `solair/data/<device-id>`) to allow easy wildcard subscriptions and per-device filtering.
- **Validate at boundaries**: Validate sensor readings before publishing (NaN checks, range checks) — don't send garbage to the broker.
- **OTA readiness**: Keep firmware size well under flash limits to leave room for OTA update partitions in the future.
- **Log verbosely on serial**: Print connection state, errors, and publish confirmations to serial for debugging; this costs nothing in production.
