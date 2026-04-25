# Firmware Guide

The firmware is a PlatformIO project targeting the ESP32-DEVKITC (WROOM-32D).

---

## Configuration

Copy the example and fill in your credentials:

```bash
cd firmware
cp settings.ini.example settings.ini
```

Edit `settings.ini`:

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

`settings.ini` is gitignored — credentials never get committed.

---

## Building and Flashing

```bash
# Build all device environments
~/.platformio/penv/bin/pio run

# Build and flash a specific device
~/.platformio/penv/bin/pio run -e device_0 -t upload

# Open the serial monitor
~/.platformio/penv/bin/pio device monitor -e device_0
```

---

## Multi-Device Setup

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

3. Flash:
   ```bash
   ~/.platformio/penv/bin/pio run -e device_2 -t upload
   ```

---

## Source Layout

| File | Purpose |
|---|---|
| `src/main.cpp` | Setup, main loop, orchestration |
| `src/sensors.cpp` | Sensor reads with calibration and validation |
| `src/mqtt_client.cpp` | WiFi/MQTT connection management and publishing |
| `include/sensors.h` | Sensor function declarations |
| `include/mqtt_client.h` | MQTT function declarations |
| `load_settings.py` | PlatformIO build script that injects settings as `-D` flags |

---

## Serial Output

The firmware logs connection state, errors, and publish confirmations to
serial at 115200 baud. Example output:

```
Connecting to WiFi...
WiFi connected: 192.168.1.42
Connecting to MQTT broker...
MQTT connected
Published solair/solair-unit-0/temperature: 23.50
Published solair/solair-unit-0/humidity: 45.00
Published solair/solair-unit-0/lux: 312.00
Published solair/solair-unit-0/voltage: 14.82
Published solair/solair-unit-0/current: 1.23
```
