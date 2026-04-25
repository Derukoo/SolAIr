const BASE = '/api';

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export function getDevices() {
  return fetchJSON(`${BASE}/data/devices`);
}

export function getLatest(deviceId) {
  const params = deviceId ? `?device_id=${deviceId}` : '';
  return fetchJSON(`${BASE}/data/latest${params}`);
}

export function getRawData(deviceId, metric, start, end) {
  const params = new URLSearchParams({ device_id: deviceId, metric });
  if (start) params.set('start', start);
  if (end) params.set('end', end);
  return fetchJSON(`${BASE}/data/raw?${params}`);
}

export function getAggregate(deviceId, metric, start, end, bucket = '1 hour') {
  const params = new URLSearchParams({ device_id: deviceId, metric, bucket });
  if (start) params.set('start', start);
  if (end) params.set('end', end);
  return fetchJSON(`${BASE}/data/aggregate?${params}`);
}

export function getAlerts({ deviceId, severity, acknowledged, limit } = {}) {
  const params = new URLSearchParams();
  if (deviceId) params.set('device_id', deviceId);
  if (severity) params.set('severity', severity);
  if (acknowledged !== undefined) params.set('acknowledged', acknowledged);
  if (limit) params.set('limit', limit);
  return fetchJSON(`${BASE}/alerts?${params}`);
}

export function getAlertSummary() {
  return fetchJSON(`${BASE}/alerts/summary`);
}

export async function acknowledgeAlert(alertId) {
  const res = await fetch(`${BASE}/alerts/${alertId}/acknowledge`, { method: 'POST' });
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}
