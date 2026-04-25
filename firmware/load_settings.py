"""
PlatformIO extra script — reads settings.ini and injects
WiFi / MQTT / device-ID values as compile-time -D flags.
"""

import configparser
import os

Import("env")  # noqa: F821  — PlatformIO built-in

config = configparser.RawConfigParser()
config.read(os.path.join(env.subst("$PROJECT_DIR"), "settings.ini"))

wifi_ssid     = config.get("wifi", "ssid",        fallback="CHANGE_ME")
wifi_password = config.get("wifi", "password",     fallback="CHANGE_ME")
broker_ip     = config.get("mqtt", "broker_ip",    fallback="192.168.1.100")
broker_port   = config.get("mqtt", "broker_port",  fallback="1883")
topic_base    = config.get("mqtt", "topic_base",   fallback="solair")

# Resolve device ID from the [devices] section using the current
# PlatformIO environment name (e.g. "device_0").
pio_env   = env.subst("$PIOENV")
device_id = config.get("devices", pio_env, fallback=pio_env)

# Topic prefix: e.g. "solair/solair-unit-0"
mqtt_prefix = topic_base + "/" + device_id

env.Append(CPPDEFINES=[
    ("WIFI_SSID",        env.StringifyMacro(wifi_ssid)),
    ("WIFI_PASSWORD",    env.StringifyMacro(wifi_password)),
    ("MQTT_BROKER_IP",   env.StringifyMacro(broker_ip)),
    ("MQTT_BROKER_PORT", broker_port),
    ("MQTT_PREFIX",      env.StringifyMacro(mqtt_prefix)),
    ("DEVICE_ID",        env.StringifyMacro(device_id)),
])
