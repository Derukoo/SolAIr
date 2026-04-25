import { useState, useEffect } from 'react'
import { getLatest } from '../api'

const UNITS = {
  temperature: '°C',
  humidity: '%',
  lux: ' lx',
  voltage: ' V',
  current: ' A',
}

const DECIMALS = {
  temperature: 1,
  humidity: 1,
  lux: 0,
  voltage: 2,
  current: 2,
}

export default function KPICards({ devices = [] }) {
  const [data, setData] = useState([])

  useEffect(() => {
    const load = () => getLatest().then(setData).catch(console.error)
    load()
    const id = setInterval(load, 5000)
    return () => clearInterval(id)
  }, [])

  const filtered = devices.length > 0
    ? data.filter((d) => devices.includes(d.device_id))
    : data

  return (
    <div className="kpi-grid">
      {filtered.map((d) => (
        <div className="kpi-card" key={`${d.device_id}-${d.metric}`}>
          <div className="label">{d.metric}</div>
          <div className="value">
            {d.value.toFixed(DECIMALS[d.metric] ?? 2)}
            <span style={{ fontSize: '0.9rem', fontWeight: 400 }}>
              {UNITS[d.metric] || ''}
            </span>
          </div>
          <div className="device">{d.device_id}</div>
        </div>
      ))}
      {filtered.length === 0 && <div className="empty">Waiting for sensor data...</div>}
    </div>
  )
}
