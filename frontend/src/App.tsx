/**
 * Jakebot Labs Dashboard - Main App
 */
import { useState, useEffect } from 'preact/hooks'
import { MemoryPanel } from './panels/MemoryPanel'
import { getSystemStatus, type SystemStatus } from './api'
import './index.css'

type Tab = 'memory' | 'health'

export function App() {
  const [activeTab, setActiveTab] = useState<Tab>('memory')
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)

  useEffect(() => {
    loadSystemStatus()
  }, [])

  async function loadSystemStatus() {
    try {
      const status = await getSystemStatus()
      setSystemStatus(status)
    } catch (err) {
      console.error('Failed to load system status:', err)
    }
  }

  return (
    <div className="min-h-screen bg-gh-bg text-gh-text">
      {/* Header */}
      <header className="bg-gh-card border-b border-gh-border">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold">🤖 Jakebot Labs Dashboard</h1>
              {systemStatus && (
                <span className="text-xs text-gh-text-muted">
                  v{systemStatus.dashboard_version}
                </span>
              )}
            </div>
            <div className="flex gap-2">
              <TabButton
                active={activeTab === 'memory'}
                onClick={() => setActiveTab('memory')}
              >
                Memory
              </TabButton>
              <TabButton
                active={activeTab === 'health'}
                onClick={() => setActiveTab('health')}
              >
                Health
              </TabButton>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {activeTab === 'memory' && <MemoryPanel />}
        {activeTab === 'health' && <HealthPlaceholder />}
      </main>
    </div>
  )
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: any
}) {
  return (
    <button
      onClick={onClick}
      className={`
        px-4 py-2 rounded font-medium transition-colors
        ${
          active
            ? 'bg-gh-accent text-white'
            : 'bg-gh-bg text-gh-text-muted hover:bg-gh-border'
        }
      `}
    >
      {children}
    </button>
  )
}

function HealthPlaceholder() {
  return (
    <div className="bg-gh-card border border-gh-border rounded-lg p-8 text-center">
      <h2 className="text-xl font-semibold mb-2">Health Monitoring</h2>
      <p className="text-gh-text-muted">Coming in Week 2</p>
    </div>
  )
}
