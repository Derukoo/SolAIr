"""Tests for /api/alerts endpoints."""

import pytest


@pytest.mark.asyncio
async def test_alerts_empty(client):
    resp = await client.get("/api/alerts")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_alerts_summary_empty(client):
    resp = await client.get("/api/alerts/summary")
    assert resp.status_code == 200
    assert resp.json() == {}


@pytest.mark.asyncio
async def test_alerts_list(seeded_client):
    resp = await seeded_client.get("/api/alerts")
    assert resp.status_code == 200
    alerts = resp.json()
    assert len(alerts) == 2


@pytest.mark.asyncio
async def test_alerts_filter_severity(seeded_client):
    resp = await seeded_client.get("/api/alerts", params={"severity": "critical"})
    assert resp.status_code == 200
    alerts = resp.json()
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "critical"


@pytest.mark.asyncio
async def test_alerts_filter_acknowledged(seeded_client):
    resp = await seeded_client.get("/api/alerts", params={"acknowledged": False})
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await seeded_client.get("/api/alerts", params={"acknowledged": True})
    assert resp.status_code == 200
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_alerts_summary(seeded_client):
    resp = await seeded_client.get("/api/alerts/summary")
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["warning"] == 1
    assert summary["critical"] == 1


@pytest.mark.asyncio
async def test_acknowledge_alert(seeded_client):
    # Get alert ID
    resp = await seeded_client.get("/api/alerts")
    alert_id = resp.json()[0]["id"]

    # Acknowledge it
    resp = await seeded_client.post(f"/api/alerts/{alert_id}/acknowledge")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    # Verify it's acknowledged
    resp = await seeded_client.get("/api/alerts", params={"acknowledged": True})
    assert len(resp.json()) == 1
