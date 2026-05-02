# Firmware Guide

The firmware is a PlatformIO project targeting the ESP32-DEVKITC (WROOM-32D).

---

## Windows

### Installing PlatformIO

Download the installer script and run it with Python (Python 3.6+ required):

```cmd
curl -fsSO https://raw.githubusercontent.com/platformio/platformio-core-installer/master/get-platformio.py
python get-platformio.py
```

After installation, add PlatformIO to your PATH so the `pio` command is
available in any terminal. Open **System Properties → Environment Variables**
and append the following to the `Path` variable:

```
C:\Users\<YourUsername>\.platformio\penv\Scripts
```

Replace `<YourUsername>` with your Windows username (e.g., `Mahdi Nouni`).
Open a new terminal and verify with `pio --version`.

### COM ports

On Windows, ESP32 boards appear as `COM` ports (e.g., `COM3`, `COM4`) instead
of `/dev/ttyUSB*`. Check Device Manager under **Ports (COM & LPT)** to find the
correct port number after plugging in the board.

Use the correct port in `platformio.ini` (see [Multi-Device Setup](#multi-device-setup))
and replace all `/dev/ttyUSB*` references with your `COM` port.

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

**Linux** — use the full path if `pio` is not on your PATH:

```bash
# Build all device environments
~/.platformio/penv/bin/pio run

# Build and flash a specific device
~/.platformio/penv/bin/pio run -e device_0 -t upload

# Open the serial monitor
~/.platformio/penv/bin/pio device monitor -e device_0
```

**Windows** — once `C:\Users\<YourUsername>\.platformio\penv\Scripts` is on
your PATH (see [Windows](#windows)):

```cmd
pio run
pio run -e device_0 -t upload
pio device monitor -e device_0
```

---

## Multi-Device Setup

Each PlatformIO environment maps to a device ID. To add a third board:

1. Add to `firmware/platformio.ini`:

   Linux:
   ```ini
   [env:device_2]
   upload_port  = /dev/ttyUSB2
   monitor_port = /dev/ttyUSB2
   ```

   Windows:
   ```ini
   [env:device_2]
   upload_port  = COM4
   monitor_port = COM4
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
