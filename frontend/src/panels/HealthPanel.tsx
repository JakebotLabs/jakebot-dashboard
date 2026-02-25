/**
 * Health Panel - System health monitoring and alerts
 */
import { useState, useEffect, useCallback } from 'preact/hooks'
import {
  getHealthStatus,
  runHealthCheck,
  type HealthSnapshot,
  type HealthIssue
} from '../api'

export function HealthPanel() {
  const [status, setStatus] = useState<HealthSnapshot | null>(null)
  const [loading, setLoading] = useState(true)
  const [checking, setChecking] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadStatus = useCallback(async () => {
    try {
      setError(null)
      const data = await getHealthStatus()
      setStatus(data)
    } catch (err) {
      console.error('Failed to load health status:', err)
      setError(err instanceof Error ? err.message : 'Failed to load health status')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadStatus()
    // Refresh every 30 seconds
    const interval = setInterval(loadStatus, 30000)
    return () => clearInterval(interval)
  }, [loadStatus])

  async function handleRunCheck() {
    setChecking(true)
    try {
      const data = await runHealthCheck()
      setStatus(data)
      setError(null)
    } catch (err) {
      console.error('Health check failed:', err)
      setError(err instanceof Error ? err.message : 'Health check failed')
    } finally {
      setChecking(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gh-text-muted">Loading health status...</div>
      </div>
    )
  }

  if (error && !status) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
        <div className="text-red-400 font-medium">Error</div>
        <div className="text-gh-text-muted mt-1">{error}</div>
        <button
          onClick={loadStatus}
          className="mt-3 px-4 py-2 bg-gh-accent text-white rounded hover:bg-gh-accent/80 transition-colors"
        >
          Retry
        </button>
      </div>
    )
  }

  const metrics = status?.metrics
  const servicesUp = status?.services.filter(s => s.status === 'up').length ?? 0
  const servicesTotal = status?.services.length ?? 0

  return (
    <div className="space-y-6">
      {/* Header with mode badge and run check button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold">System Health</h2>
          {status && (
            <span className={`
              px-2 py-1 text-xs font-medium rounded
              ${status.mode === 'HEAL' 
                ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'}
            `}>
              {status.mode}
            </span>
          )}
        </div>
        <button
          onClick={handleRunCheck}
          disabled={checking}
          className={`
            px-4 py-2 rounded font-medium transition-colors
            ${checking 
              ? 'bg-gh-border text-gh-text-muted cursor-not-allowed' 
              : 'bg-gh-accent text-white hover:bg-gh-accent/80'}
          `}
        >
          {checking ? 'Running...' : 'Run Check'}
        </button>
      </div>

      {error && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 text-sm text-yellow-400">
          {error}
        </div>
      )}

      {/* Metric tiles */}
      <div className="grid grid-cols-5 gap-4">
        <MetricTile
          label="MEMORY.md"
          value={metrics?.memory_md_kb ?? 0}
          unit="KB"
          icon="📄"
        />
        <MetricTile
          label="Workspace"
          value={metrics?.workspace_kb ?? 0}
          unit="KB"
          icon="📁"
        />
        <MetricTile
          label="Vector Chunks"
          value={metrics?.vector_chunks ?? 0}
          icon="🔢"
        />
        <MetricTile
          label="Graph Nodes"
          value={metrics?.graph_nodes ?? 0}
          icon="🔗"
        />
        <MetricTile
          label="Services"
          value={servicesUp}
          total={servicesTotal}
          icon="⚙️"
        />
      </div>

      {/* Services grid */}
      <div className="bg-gh-card border border-gh-border rounded-lg p-4">
        <h3 className="text-sm font-semibold mb-3">Services</h3>
        <div className="grid grid-cols-3 gap-3">
          {status?.services.map((service) => (
            <ServiceCard key={service.name} name={service.name} status={service.status} />
          ))}
        </div>
      </div>

      {/* Issues/Alerts log */}
      <div className="bg-gh-card border border-gh-border rounded-lg p-4">
        <h3 className="text-sm font-semibold mb-3">
          Issues {status?.issues.length ? `(${status.issues.length})` : ''}
        </h3>
        {status?.issues.length === 0 ? (
          <div className="text-gh-text-muted text-sm py-4 text-center">
            ✅ No issues detected
          </div>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {status?.issues.map((issue) => (
              <IssueCard key={issue.id} issue={issue} />
            ))}
          </div>
        )}
      </div>

      {/* Last update timestamp */}
      {status && (
        <div className="text-xs text-gh-text-muted text-right">
          Last updated: {new Date(status.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  )
}

function MetricTile({
  label,
  value,
  unit,
  total,
  icon,
}: {
  label: string
  value: number
  unit?: string
  total?: number
  icon: string
}) {
  return (
    <div className="bg-gh-card border border-gh-border rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{icon}</span>
        <span className="text-gh-text-muted text-sm">{label}</span>
      </div>
      <div className="text-2xl font-semibold text-gh-accent">
        {typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 1 }) : value}
        {unit && <span className="text-sm text-gh-text-muted ml-1">{unit}</span>}
        {total !== undefined && (
          <span className="text-sm text-gh-text-muted">/{total}</span>
        )}
      </div>
    </div>
  )
}

function ServiceCard({ name, status }: { name: string; status: string }) {
  const statusConfig = {
    up: { icon: '✅', bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400' },
    down: { icon: '❌', bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400' },
    disabled: { icon: '⏸️', bg: 'bg-gray-500/10', border: 'border-gray-500/30', text: 'text-gray-400' },
  }
  
  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.down

  return (
    <div className={`${config.bg} border ${config.border} rounded-lg p-3`}>
      <div className="flex items-center gap-2">
        <span>{config.icon}</span>
        <span className="font-medium capitalize">{name.replace(/_/g, ' ')}</span>
      </div>
      <div className={`text-xs ${config.text} mt-1 uppercase`}>
        {status}
      </div>
    </div>
  )
}

function IssueCard({ issue }: { issue: HealthIssue }) {
  const severityConfig = {
    warning: { icon: '⚠️', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30' },
    critical: { icon: '🚨', bg: 'bg-red-500/10', border: 'border-red-500/30' },
  }
  
  const config = severityConfig[issue.severity as keyof typeof severityConfig] || severityConfig.warning

  return (
    <div className={`${config.bg} border ${config.border} rounded-lg p-3`}>
      <div className="flex items-start gap-2">
        <span className="text-lg">{config.icon}</span>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium">{issue.message}</div>
          <div className="flex items-center gap-3 mt-1 text-xs text-gh-text-muted">
            <span>{new Date(issue.detected_at).toLocaleTimeString()}</span>
            <span className="uppercase">{issue.severity}</span>
            {issue.can_auto_heal && (
              <span className="text-green-400">Auto-healable</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
