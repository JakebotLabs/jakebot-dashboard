/**
 * API client for Jakebot Dashboard
 */

const BASE = `${window.location.protocol}//${window.location.host}/api`

let authToken: string | null = null

export function setAuthToken(token: string) {
  authToken = token
}

function headers(): HeadersInit {
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  if (authToken) h['Authorization'] = `Bearer ${authToken}`
  return h
}

export interface SearchResult {
  chunk_id: string
  content: string
  source: string
  section: string
  score: number
}

export interface SearchResponse {
  results: SearchResult[]
  query: string
  took_ms: number
}

export interface MemoryStatus {
  chunks: number
  nodes: number
  edges: number
  files_indexed: number
  last_sync: string
  last_sync_ago: string
  db_size_mb: number
}

export interface SystemStatus {
  dashboard_version: string
  products: {
    persistent_memory: {
      installed: boolean
      path: string | null
      status: string
    }
    agent_healthkit: {
      installed: boolean
      path: string | null
      status: string
    }
  }
  python_version: string
  platform: string
}

export async function searchMemory(query: string, n = 5): Promise<SearchResponse> {
  const res = await fetch(`${BASE}/memory/search?q=${encodeURIComponent(query)}&n=${n}`, {
    headers: headers()
  })
  if (!res.ok) throw new Error(`Search failed: ${res.statusText}`)
  return res.json()
}

export async function getMemoryStatus(): Promise<MemoryStatus> {
  const res = await fetch(`${BASE}/memory/status`, {
    headers: headers()
  })
  if (!res.ok) throw new Error(`Status fetch failed: ${res.statusText}`)
  return res.json()
}

export async function listFiles(): Promise<string[]> {
  const res = await fetch(`${BASE}/memory/files`, {
    headers: headers()
  })
  if (!res.ok) throw new Error(`File list failed: ${res.statusText}`)
  return res.json()
}

export async function getSystemStatus(): Promise<SystemStatus> {
  const res = await fetch(`${BASE}/system/status`, {
    headers: headers()
  })
  if (!res.ok) throw new Error(`System status failed: ${res.statusText}`)
  return res.json()
}

// Phase 2 additions - Memory CRUD
export interface FileContent {
  path: string
  content: string
  size_bytes: number
}

export interface ReindexJob {
  job_id: string
  status: string
  started_at: string
  completed_at: string | null
  chunks_indexed: number | null
  error: string | null
}

export interface GraphExport {
  nodes: number
  edges: number
  data: Record<string, unknown>
}

export async function getFile(path: string): Promise<FileContent> {
  const res = await fetch(`${BASE}/memory/file?path=${encodeURIComponent(path)}`, {
    headers: headers()
  })
  if (!res.ok) throw new Error(`File fetch failed: ${res.statusText}`)
  return res.json()
}

export async function deleteChunk(chunkId: string): Promise<{ chunk_id: string; deleted: boolean }> {
  const res = await fetch(`${BASE}/memory/chunk/${encodeURIComponent(chunkId)}`, {
    method: 'DELETE',
    headers: headers()
  })
  if (!res.ok) throw new Error(`Chunk delete failed: ${res.statusText}`)
  return res.json()
}

export async function reindex(): Promise<ReindexJob> {
  const res = await fetch(`${BASE}/memory/reindex`, {
    method: 'POST',
    headers: headers()
  })
  if (!res.ok) throw new Error(`Reindex failed: ${res.statusText}`)
  return res.json()
}

export async function getGraph(): Promise<GraphExport> {
  const res = await fetch(`${BASE}/memory/graph`, {
    headers: headers()
  })
  if (!res.ok) throw new Error(`Graph fetch failed: ${res.statusText}`)
  return res.json()
}

// Phase 2 - Health API
export interface ServiceStatus {
  name: string
  status: string
}

export interface HealthIssue {
  id: string
  severity: string
  message: string
  detected_at: string
  can_auto_heal: boolean
}

export interface HealthMetrics {
  memory_md_kb: number
  workspace_kb: number
  vector_chunks: number
  graph_nodes: number
  graph_edges: number
}

export interface HealthSnapshot {
  timestamp: string
  mode: string
  uptime_percent: number
  metrics: HealthMetrics
  services: ServiceStatus[]
  issues: HealthIssue[]
}

export interface HistoryPoint {
  timestamp: string
  memory_md_kb: number
  workspace_kb: number
  issues_count: number
  services_up: number
  services_total: number
}

export interface HealthHistory {
  window: string
  points: HistoryPoint[]
}

export interface Monitor {
  id: string
  name: string
  enabled: boolean
  description: string
}

export async function getHealthStatus(): Promise<HealthSnapshot> {
  const res = await fetch(`${BASE}/health/status`, {
    headers: headers()
  })
  if (!res.ok) throw new Error(`Health status failed: ${res.statusText}`)
  return res.json()
}

export async function getHealthHistory(hours = 24): Promise<HealthHistory> {
  const res = await fetch(`${BASE}/health/history?hours=${hours}`, {
    headers: headers()
  })
  if (!res.ok) throw new Error(`Health history failed: ${res.statusText}`)
  return res.json()
}

export async function getHealthMonitors(): Promise<Monitor[]> {
  const res = await fetch(`${BASE}/health/monitors`, {
    headers: headers()
  })
  if (!res.ok) throw new Error(`Health monitors failed: ${res.statusText}`)
  return res.json()
}

export async function runHealthCheck(): Promise<HealthSnapshot> {
  const res = await fetch(`${BASE}/health/check`, {
    method: 'POST',
    headers: headers()
  })
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`)
  return res.json()
}
