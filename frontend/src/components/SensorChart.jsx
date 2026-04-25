import { useState, useEffect } from 'react'
import Chart from 'react-apexcharts'
import { getAggregate, getRawData } from '../api'

const RANGES = [
  { label: '1H', hours: 1, bucket: '1 minute' },
  { label: '6H', hours: 6, bucket: '5 minutes' },
  { label: '24H', hours: 24, bucket: '15 minutes' },
  { label: '7D', hours: 168, bucket: '1 hour' },
  { label: '30D', hours: 720, bucket: '6 hours' },
]

function round2(v) {
  return v != null ? Math.round(v * 100) / 100 : v
}

export default function SensorChart({ deviceId, metric, theme = 'dark' }) {
  const [rangeIdx, setRangeIdx] = useState(2) // default 24H
  const [series, setSeries] = useState([])

  useEffect(() => {
    if (!deviceId || !metric) return

    const range = RANGES[rangeIdx]
    const end = new Date().toISOString()
    const start = new Date(Date.now() - range.hours * 3600000).toISOString()

    if (range.hours <= 1) {
      getRawData(deviceId, metric, start, end).then((data) => {
        setSeries([{
          name: metric,
          data: data.reverse().map((d) => ({ x: new Date(d.time).getTime(), y: round2(d.value) })),
        }])
      }).catch(console.error)
    } else {
      getAggregate(deviceId, metric, start, end, range.bucket).then((data) => {
        setSeries([
          {
            name: 'avg',
            data: data.reverse().map((d) => ({ x: new Date(d.time).getTime(), y: round2(d.avg) })),
          },
          {
            name: 'min',
            data: data.map((d) => ({ x: new Date(d.time).getTime(), y: round2(d.min) })),
          },
          {
            name: 'max',
            data: data.map((d) => ({ x: new Date(d.time).getTime(), y: round2(d.max) })),
          },
        ])
      }).catch(console.error)
    }
  }, [deviceId, metric, rangeIdx])

  const isDark = theme === 'dark'

  const options = {
    chart: {
      type: 'line',
      background: 'transparent',
      toolbar: { show: true },
      zoom: { enabled: true },
    },
    theme: { mode: isDark ? 'dark' : 'light' },
    stroke: { width: 2, curve: 'smooth' },
    xaxis: { type: 'datetime' },
    yaxis: {
      title: { text: metric },
      labels: {
        formatter: (val) => val != null ? val.toFixed(2) : val,
      },
    },
    tooltip: {
      x: { format: 'HH:mm:ss dd MMM' },
      y: {
        formatter: (val) => val != null ? val.toFixed(2) : val,
      },
    },
    grid: { borderColor: isDark ? '#2a2d3a' : '#e5e7eb' },
    colors: ['#22c55e', '#3b82f6', '#8b5cf6'],
    legend: { show: series.length > 1 },
  }

  return (
    <div className="chart-panel">
      <h3>{deviceId} — {metric}</h3>
      <div style={{ display: 'flex', gap: 4, marginBottom: 8 }}>
        {RANGES.map((r, i) => (
          <button
            key={r.label}
            className={i === rangeIdx ? 'active' : ''}
            onClick={() => setRangeIdx(i)}
            style={{
              background: i === rangeIdx ? 'var(--accent-dim)' : 'transparent',
              border: '1px solid var(--border)',
              color: i === rangeIdx ? 'var(--accent)' : 'var(--text-dim)',
              padding: '2px 8px',
              borderRadius: 4,
              cursor: 'pointer',
              fontSize: '0.7rem',
            }}
          >
            {r.label}
          </button>
        ))}
      </div>
      {series.length > 0 ? (
        <Chart options={options} series={series} type="line" height={250} />
      ) : (
        <div className="empty" style={{ height: 250 }}>No data</div>
      )}
    </div>
  )
}
