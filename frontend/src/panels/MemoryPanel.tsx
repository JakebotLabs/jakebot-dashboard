/**
 * Memory Panel - Search and browse vector memory
 */
import { useState, useEffect, useCallback } from 'preact/hooks'
import { searchMemory, getMemoryStatus, listFiles, type SearchResult, type MemoryStatus } from '../api'

export function MemoryPanel() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [status, setStatus] = useState<MemoryStatus | null>(null)
  const [files, setFiles] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [searchTime, setSearchTime] = useState(0)

  const performSearch = useCallback(async () => {
    setLoading(true)
    try {
      const response = await searchMemory(query, 5)
      setResults(response.results)
      setSearchTime(response.took_ms)
    } catch (err) {
      console.error('Search failed:', err)
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [query])

  // Load status and files on mount
  useEffect(() => {
    loadStatus()
    loadFiles()
  }, [])

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      return
    }

    const timer = setTimeout(() => {
      performSearch()
    }, 300)

    return () => clearTimeout(timer)
  }, [query, performSearch])

  async function loadStatus() {
    try {
      const s = await getMemoryStatus()
      setStatus(s)
    } catch (err) {
      console.error('Failed to load status:', err)
    }
  }

  async function loadFiles() {
    try {
      const f = await listFiles()
      setFiles(f)
    } catch (err) {
      console.error('Failed to load files:', err)
    }
  }

  return (
    <div className="flex h-full gap-4">
      {/* Main content */}
      <div className="flex-1 space-y-4">
        {/* Status cards */}
        <div className="grid grid-cols-4 gap-4">
          <StatCard label="Chunks" value={status?.chunks ?? 0} />
          <StatCard label="Nodes" value={status?.nodes ?? 0} />
          <StatCard label="Edges" value={status?.edges ?? 0} />
          <StatCard label="Files" value={status?.files_indexed ?? 0} />
        </div>

        {/* Search bar */}
        <div className="bg-gh-card border border-gh-border rounded-lg p-4">
          <input
            type="text"
            value={query}
            onInput={(e) => setQuery((e.target as HTMLInputElement).value)}
            placeholder="Search memory..."
            className="w-full bg-gh-bg border border-gh-border rounded px-4 py-2 text-gh-text focus:border-gh-accent focus:outline-none"
          />
          {query && (
            <div className="mt-2 text-sm text-gh-text-muted">
              {loading ? 'Searching...' : `${results.length} results in ${searchTime}ms`}
            </div>
          )}
        </div>

        {/* Results */}
        <div className="space-y-3">
          {results.map((result) => (
            <ResultCard key={result.chunk_id} result={result} />
          ))}
        </div>

        {!query && (
          <div className="text-center text-gh-text-muted py-12">
            <p>Start typing to search memory...</p>
          </div>
        )}
      </div>

      {/* Sidebar */}
      <div className="w-64 bg-gh-card border border-gh-border rounded-lg p-4">
        <h3 className="text-sm font-semibold mb-3">Indexed Files</h3>
        <div className="space-y-1 text-sm">
          {files.slice(0, 20).map((file) => (
            <div key={file} className="text-gh-text-muted truncate" title={file}>
              {file}
            </div>
          ))}
          {files.length > 20 && (
            <div className="text-gh-text-muted italic">
              +{files.length - 20} more...
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-gh-card border border-gh-border rounded-lg p-4">
      <div className="text-gh-text-muted text-sm mb-1">{label}</div>
      <div className="text-2xl font-semibold text-gh-accent">{value.toLocaleString()}</div>
    </div>
  )
}

function ResultCard({ result }: { result: SearchResult }) {
  return (
    <div className="bg-gh-card border border-gh-border rounded-lg p-4 hover:border-gh-accent transition-colors">
      <div className="flex justify-between items-start mb-2">
        <div className="text-sm font-medium text-gh-accent truncate flex-1">
          {result.source || 'Unknown'}
        </div>
        <div className="text-xs text-gh-text-muted ml-2">
          {(result.score * 100).toFixed(0)}%
        </div>
      </div>
      {result.section && (
        <div className="text-xs text-gh-text-muted mb-2">{result.section}</div>
      )}
      <div className="text-sm text-gh-text leading-relaxed">
        {result.content}
      </div>
    </div>
  )
}
