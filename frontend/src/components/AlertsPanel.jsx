import { useState, useEffect } from 'react'
import { getAlerts, getAlertSummary, acknowledgeAlert } from '../api'

export default function AlertsPanel() {
  const [alerts, setAlerts] = useState([])
  const [summary, setSummary] = useState({})
  const [showAcked, setShowAcked] = useState(false)

  const load = () => {
    getAlerts({ acknowledged: showAcked ? undefined : false, limit: 50 })
      .then(setAlerts)
      .catch(console.error)
    getAlertSummary().then(setSummary).catch(console.error)
  }

  useEffect(() => {
    load()
    const id = setInterval(load, 10000)
    return () => clearInterval(id)
  }, [showAcked])

  const handleAck = async (id) => {
    await acknowledgeAlert(id)
    load()
  }

  const totalActive = Object.values(summary).reduce((a, b) => a + b, 0)

  return (
    <div className="alerts-section">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h2>Alerts {totalActive > 0 && <span style={{ color: 'var(--red)' }}>({totalActive} active)</span>}</h2>
        <button
          onClick={() => setShowAcked(!showAcked)}
          style={{
            background: 'transparent',
            border: '1px solid var(--border)',
            color: 'var(--text-dim)',
            padding: '4px 10px',
            borderRadius: 6,
            cursor: 'pointer',
            fontSize: '0.75rem',
          }}
        >
          {showAcked ? 'Hide acknowledged' : 'Show all'}
        </button>
      </div>

      <div className="alert-summary">
        {summary.critical > 0 && <span className="badge critical">{summary.critical} critical</span>}
        {summary.warning > 0 && <span className="badge warning">{summary.warning} warning</span>}
        {summary.info > 0 && <span className="badge info">{summary.info} info</span>}
      </div>

      {alerts.length === 0 && <div className="empty">No alerts</div>}

      {alerts.map((a) => (
        <div className="alert-row" key={a.id}>
          <span className={`badge ${a.severity}`}>{a.severity}</span>
          <span className={`badge`} style={{ background: 'rgba(255,255,255,0.05)' }}>{a.alert_type}</span>
          <span className="message">{a.message}</span>
          <span className="time">{new Date(a.created_at).toLocaleString()}</span>
          {!a.acknowledged && (
            <button onClick={() => handleAck(a.id)}>Ack</button>
          )}
        </div>
      ))}
    </div>
  )
}
