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
