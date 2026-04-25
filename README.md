# SolAIr

An end-to-end IoT platform for solar panel monitoring. ESP32 microcontrollers
read environmental and electrical sensors, publish data over MQTT, and a
full-stack web dashboard ingests, analyzes, and visualizes everything in
real time — with built-in anomaly detection to catch failures early.

---

## Architecture

```
ESP32 Devices          MQTT Broker          Backend (FastAPI)          Frontend (React)
 DHT11, BH1750,   -->  Mosquitto      -->  MQTT Subscriber       -->  Dashboard
 Voltage, Current      port 1883           REST API                   KPIs, Charts,
                                           Anomaly Engine             Alerts
                                                |
                                           TimescaleDB
                                           (PostgreSQL)
```

Sensor data flows from the ESP32 through Mosquitto into a FastAPI backend that
stores readings in TimescaleDB (a time-series extension of PostgreSQL). The
anomaly engine runs server-side every 60 seconds, applying threshold checks,
Z-score spike detection, and long-term drift analysis. The React frontend
polls the REST API and renders live dashboards, charts, and alert panels.

---

## Hardware

| Component | Role | Interface | Pin(s) |
|---|---|---|---|
| **ESP32-DEVKITC** (CP2102, WROOM-32D) | Microcontroller | USB | -- |
| **DHT11** | Temperature & Humidity | Digital | GPIO 32 |
| **GY-30 BH1750FVI** | Ambient Light (Lux) | I2C | SDA=21, SCL=22 |
| **Voltage Sensor 0-25V** | Panel Voltage | ADC | GPIO 36 |
| **ACS712 5A** | Panel Current | ADC | GPIO 39 |

The voltage sensor uses a 1:5 resistive divider, giving an effective range of
0-25V. The ACS712 outputs an analog voltage proportional to current, centered
at 2.5V (0A), with 185 mV/A sensitivity. Both analog channels use 64-sample
averaging on the ESP32 to reduce noise.

---

## Quick Start

### Prerequisites

- **Docker** & **Docker Compose**
- **PlatformIO** (for ESP32 firmware only)

### 1. Clone and start the stack

```bash
git clone https://github.com/Derukoo/SolAIr.git
cd SolAIr
docker compose up -d
```

This starts four services:

| Service | Port | Description |
|---|---|---|
| **Frontend** | 3000 | React dashboard |
| **Backend** | 8000 | FastAPI REST API + anomaly engine |
| **Mosquitto** | 1883 | MQTT broker |
| **TimescaleDB** | 5432 | Time-series database |

### 2. Open the dashboard

Navigate to **http://localhost:3000**

The sidebar gives you three views:
- **Dashboard** — KPI cards with latest readings per device
- **Graphs** — Time-series charts with range selectors
- **Alerts** — Alert list with severity filters and acknowledgment

### 3. Flash the firmware (requires hardware)

```bash
cd firmware
cp settings.ini.example settings.ini
# Edit settings.ini with your WiFi credentials and broker IP
```

```bash
~/.platformio/penv/bin/pio run -e device_0 -t upload
```

### 4. Verify data flow

```bash
# Subscribe to all MQTT topics
mosquitto_sub -h localhost -t "solair/#"

# Or check the API directly
curl http://localhost:8000/api/data/latest
```

---

## Project Structure

```
SolAIr/
├── firmware/               # ESP32 PlatformIO project
│   ├── platformio.ini
│   ├── settings.ini.example
│   ├── include/            # Header files
│   └── src/                # main.cpp, sensors.cpp, mqtt_client.cpp
├── backend/                # FastAPI + anomaly detection
│   ├── Dockerfile
│   ├── app/                # Application code
│   └── tests/              # Pytest test suite
├── frontend/               # React + Vite + ApexCharts
│   ├── Dockerfile
│   └── src/                # Components, styles, API client
├── db/init/                # TimescaleDB schema
├── mosquitto/config/       # Broker configuration
├── docs/                   # Technical documentation
├── docker-compose.yml
└── README.md
```

---

## Documentation

Detailed technical documentation lives in the [`docs/`](docs/) folder:

| Document | Contents |
|---|---|
| [REST API Reference](docs/api-reference.md) | All endpoints, parameters, and example responses |
| [Anomaly Detection](docs/anomaly-detection.md) | Threshold, Z-score, and drift algorithms explained |
| [Data Pipeline](docs/data-pipeline.md) | Sensor reads, MQTT transport, ingestion, and aggregation |
| [Firmware Guide](docs/firmware-guide.md) | Configuration, multi-device setup, and serial debugging |
| [Testing](docs/testing.md) | Running tests, fixtures, and manual verification |

---

## License

This project is provided as-is for educational and personal use.
