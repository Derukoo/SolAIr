"""Tests for MQTT ingestion logic."""

from unittest.mock import MagicMock, patch

import pytest

from app.mqtt_ingestion import _on_message, _on_connect


def test_on_connect_subscribes():
    """on_connect should subscribe to the configured topic."""
    client = MagicMock()
    _on_connect(client, None, None, 0, None)
    client.subscribe.assert_called_once()


def test_on_message_ignores_short_topics():
    """Messages with fewer than 3 topic segments are silently dropped."""
    client = MagicMock()
    msg = MagicMock()
    msg.topic = "solair/unit-0"
    msg.payload = b"22.5"

    with patch("app.mqtt_ingestion._get_sync_engine") as mock_engine:
        _on_message(client, None, msg)
        mock_engine.assert_not_called()


def test_on_message_ignores_bad_payload():
    """Non-numeric payloads are dropped."""
    client = MagicMock()
    msg = MagicMock()
    msg.topic = "solair/unit-0/temperature"
    msg.payload = b"not-a-number"

    with patch("app.mqtt_ingestion._get_sync_engine") as mock_engine:
        _on_message(client, None, msg)
        mock_engine.assert_not_called()


def test_on_message_inserts_valid_reading():
    """Valid messages should trigger a DB insert."""
    client = MagicMock()
    msg = MagicMock()
    msg.topic = "solair/unit-0/temperature"
    msg.payload = b"22.5"

    mock_conn = MagicMock()
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
    mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

    with patch("app.mqtt_ingestion._get_sync_engine", return_value=mock_engine):
        _on_message(client, None, msg)

    mock_conn.execute.assert_called_once()
    mock_conn.commit.assert_called_once()

    # Verify the inserted values
    call_args = mock_conn.execute.call_args
    params = call_args[0][1]
    assert params["d"] == "unit-0"
    assert params["m"] == "temperature"
    assert params["v"] == 22.5
