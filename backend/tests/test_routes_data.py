"""Tests for /api/data endpoints."""

import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_devices_returns_list(client):
    resp = await client.get("/api/data/devices")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_metrics_returns_list(client):
    resp = await client.get("/api/data/metrics")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_latest_returns_list(client):
    resp = await client.get("/api/data/latest")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_devices_includes_seeded(seeded_client):
    resp = await seeded_client.get("/api/data/devices")
    assert resp.status_code == 200
    devices = resp.json()
    assert "unit-0" in devices
    assert "unit-1" in devices


@pytest.mark.asyncio
async def test_metrics_includes_seeded(seeded_client):
    resp = await seeded_client.get("/api/data/metrics")
    assert resp.status_code == 200
    metrics = resp.json()
    assert "temperature" in metrics
    assert "humidity" in metrics


@pytest.mark.asyncio
async def test_latest_includes_seeded(seeded_client):
    resp = await seeded_client.get("/api/data/latest")
    assert resp.status_code == 200
    data = resp.json()
    device_metrics = {(r["device_id"], r["metric"]) for r in data}
    assert ("unit-0", "temperature") in device_metrics
    assert ("unit-0", "humidity") in device_metrics
    assert ("unit-1", "temperature") in device_metrics


@pytest.mark.asyncio
async def test_latest_filter_by_device(seeded_client):
    resp = await seeded_client.get("/api/data/latest", params={"device_id": "unit-1"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert all(r["device_id"] == "unit-1" for r in data)


@pytest.mark.asyncio
async def test_raw_returns_data(seeded_client):
    resp = await seeded_client.get("/api/data/raw", params={"device_id": "unit-0", "metric": "temperature"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 5
    for row in data:
        assert "time" in row
        assert "value" in row


@pytest.mark.asyncio
async def test_raw_nonexistent_device(seeded_client):
    resp = await seeded_client.get("/api/data/raw", params={"device_id": "nope", "metric": "temperature"})
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_aggregate_returns_buckets(seeded_client):
    resp = await seeded_client.get(
        "/api/data/aggregate",
        params={"device_id": "unit-0", "metric": "temperature", "bucket": "1 hour"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    row = data[0]
    assert "time" in row
    assert "avg" in row
    assert "min" in row
    assert "max" in row
    assert "count" in row
