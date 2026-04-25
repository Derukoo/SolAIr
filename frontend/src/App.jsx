import { useState, useEffect } from 'react'
import { getDevices } from './api'
import KPICards from './components/KPICards'
import SensorChart from './components/SensorChart'
import AlertsPanel from './components/AlertsPanel'
import Sidebar from './components/Sidebar'

const METRICS = ['temperature', 'humidity', 'lux', 'voltage', 'current']

function SolarPanelIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="4" width="20" height="14" rx="2" />
      <line x1="12" y1="4" x2="12" y2="18" />
      <line x1="2" y1="11" x2="22" y2="11" />
      <line x1="7" y1="4" x2="7" y2="18" />
      <line x1="17" y1="4" x2="17" y2="18" />
      <line x1="12" y1="18" x2="12" y2="22" />
      <line x1="8" y1="22" x2="16" y2="22" />
    </svg>
  )
}

export default function App() {
  const [devices, setDevices] = useState([])
  const [activeDevices, setActiveDevices] = useState(new Set())
  const [page, setPage] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [theme, setTheme] = useState(() =>
    localStorage.getItem('solair-theme') || 'dark'
  )

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('solair-theme', theme)
  }, [theme])

  useEffect(() => {
    getDevices().then((d) => {
      setDevices(d)
      setActiveDevices(new Set(d))
    }).catch(console.error)
  }, [])

  const toggleDevice = (id) => {
    setActiveDevices((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const visibleDevices = devices.filter((d) => activeDevices.has(d))

  const deviceToggles = (
    <div className="device-toggles">
      {devices.map((d) => (
        <button
          key={d}
          className={`device-btn ${activeDevices.has(d) ? 'active' : ''}`}
          onClick={() => toggleDevice(d)}
        >
          <SolarPanelIcon />
          {d}
        </button>
      ))}
    </div>
  )

  return (
    <div className="app-layout">
      <Sidebar
        page={page}
        setPage={setPage}
        isOpen={sidebarOpen}
        setIsOpen={setSidebarOpen}
        theme={theme}
        setTheme={setTheme}
      />

      <main className={`main-content ${!sidebarOpen ? 'expanded' : ''}`}>
        <div className="page-header">
          <h1>
            {page === 'dashboard' && 'Dashboard'}
            {page === 'graphs' && 'Graphs'}
            {page === 'alerts' && 'Alerts'}
          </h1>
          {(page === 'dashboard' || page === 'graphs') && deviceToggles}
        </div>

        {page === 'dashboard' && (
          <>
            <KPICards devices={visibleDevices} />
          </>
        )}

        {page === 'graphs' && (
          <div className="chart-grid">
            {visibleDevices.flatMap((dev) =>
              METRICS.map((m) => (
                <SensorChart key={`${dev}-${m}`} deviceId={dev} metric={m} theme={theme} />
              ))
            )}
          </div>
        )}

        {page === 'alerts' && (
          <AlertsPanel />
        )}
      </main>
    </div>
  )
}
