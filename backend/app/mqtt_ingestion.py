"""
MQTT subscriber that ingests sensor data into TimescaleDB.

Listens to solair/<device_id>/<metric> topics and inserts rows
into the sensor_data hypertable.
"""

import logging
import threading
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from sqlalchemy import create_engine, text

from .config import settings

logger = logging.getLogger("solair.mqtt")

# Sync engine for the MQTT callback thread (asyncpg cannot be used outside asyncio)
_sync_engine = None


def _get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    return _sync_engine


def _on_connect(client, userdata, flags, reason_code, properties):
    logger.info("Connected to MQTT broker (rc=%s), subscribing to %s", reason_code, settings.mqtt_topic)
    client.subscribe(settings.mqtt_topic)


def _on_message(client, userdata, msg):
    # Topic format: solair/<device_id>/<metric>
    parts = msg.topic.split("/")
    if len(parts) < 3:
        return

    device_id = parts[1]
    metric = parts[2]

    try:
        value = float(msg.payload.decode())
    except (ValueError, UnicodeDecodeError):
        logger.warning("Bad payload on %s: %s", msg.topic, msg.payload)
        return

    engine = _get_sync_engine()
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO sensor_data (time, device_id, metric, value) VALUES (:t, :d, :m, :v)"),
            {"t": datetime.now(timezone.utc), "d": device_id, "m": metric, "v": value},
        )
        conn.commit()


def start_mqtt_listener():
    """Start the MQTT subscriber in a background daemon thread."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="solair-backend")
    client.on_connect = _on_connect
    client.on_message = _on_message

    def _run():
        while True:
            try:
                logger.info("Connecting to MQTT broker at %s:%d", settings.mqtt_broker, settings.mqtt_port)
                client.connect(settings.mqtt_broker, settings.mqtt_port, keepalive=60)
                client.loop_forever()
            except Exception as exc:
                logger.error("MQTT connection failed: %s — retrying in 5s", exc)
                time.sleep(5)

    thread = threading.Thread(target=_run, daemon=True, name="mqtt-ingestion")
    thread.start()
    return client
