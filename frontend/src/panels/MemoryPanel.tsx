/**
 * Memory Panel - Search and browse vector memory
 */
import { useState, useEffect, useCallback } from 'preact/hooks'
import { 
  searchMemory, getMemoryStatus, listFiles, getFile, reindex,
  type SearchResult, type MemoryStatus, type FileContent 
} from '../api'

export function MemoryPanel() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [status, setStatus] = useState<MemoryStatus | null>(null)
  const [files, setFiles] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [searchTime, setSearchTime] = useState(0)
  
  // Phase 2: File preview state
  const [previewFile, setPreviewFile] = useState<FileContent | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)
  
  // Phase 2: Reindex state
  const [reindexing, setReindexing] = useState(false)
  const [reindexResult, setReindexResult] = useState<string | null>(null)

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

  // Phase 2: File preview handler
  async function handleFileClick(filePath: string) {
    setPreviewLoading(true)
    setPreviewError(null)
    try {
      const content = await getFile(filePath)
      setPreviewFile(content)
    } catch (err) {
      console.error('Failed to load file:', err)
      setPreviewError(err instanceof Error ? err.message : 'Failed to load file')
    } finally {
      setPreviewLoading(false)
    }
  }

  function closePreview() {
    setPreviewFile(null)
    setPreviewError(null)
  }

  // Phase 2: Reindex handler
  async function handleReindex() {
    setReindexing(true)
    setReindexResult(null)
    try {
      const result = await reindex()
      if (result.status === 'complete') {
        setReindexResult(`✅ Indexed ${result.chunks_indexed ?? '?'} chunks`)
        // Refresh status
        loadStatus()
      } else {
        setReindexResult(`❌ ${result.error || 'Reindex failed'}`)
      }
    } catch (err) {
      console.error('Reindex failed:', err)
      setReindexResult(`❌ ${err instanceof Error ? err.message : 'Reindex failed'}`)
    } finally {
      setReindexing(false)
      // Clear message after 5 seconds
      setTimeout(() => setReindexResult(null), 5000)
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
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold">Indexed Files</h3>
          <button
            onClick={handleReindex}
            disabled={reindexing}
            className={`
              px-2 py-1 text-xs rounded transition-colors
              ${reindexing 
                ? 'bg-gh-border text-gh-text-muted cursor-not-allowed' 
                : 'bg-gh-accent text-white hover:bg-gh-accent/80'}
            `}
            title="Re-index vector memory"
          >
            {reindexing ? '⏳' : '🔄'} Reindex
          </button>
        </div>
        
        {reindexResult && (
          <div className={`
            text-xs mb-3 p-2 rounded
            ${reindexResult.startsWith('✅') 
              ? 'bg-green-500/10 text-green-400' 
              : 'bg-red-500/10 text-red-400'}
          `}>
            {reindexResult}
          </div>
        )}
        
        <div className="space-y-1 text-sm max-h-96 overflow-y-auto">
          {files.slice(0, 30).map((file) => (
            <div 
              key={file} 
              className="text-gh-text-muted truncate cursor-pointer hover:text-gh-accent transition-colors" 
              title={file}
              onClick={() => handleFileClick(file)}
            >
              📄 {file}
            </div>
          ))}
          {files.length > 30 && (
            <div className="text-gh-text-muted italic">
              +{files.length - 30} more...
            </div>
          )}
        </div>
      </div>
      
      {/* File Preview Modal */}
      {(previewFile || previewLoading || previewError) && (
        <FilePreviewModal
          file={previewFile}
          loading={previewLoading}
          error={previewError}
          onClose={closePreview}
        />
      )}
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

// Phase 2: File Preview Modal
function FilePreviewModal({
  file,
  loading,
  error,
  onClose,
}: {
  file: FileContent | null
  loading: boolean
  error: string | null
  onClose: () => void
}) {
  // Close on escape key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-gh-card border border-gh-border rounded-lg w-full max-w-4xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gh-border">
          <div className="flex-1 min-w-0">
            {loading ? (
              <span className="text-gh-text-muted">Loading...</span>
            ) : error ? (
              <span className="text-red-400">Error</span>
            ) : (
              <>
                <div className="font-medium truncate">{file?.path}</div>
                <div className="text-xs text-gh-text-muted">
                  {file?.size_bytes ? `${(file.size_bytes / 1024).toFixed(1)} KB` : ''}
                </div>
              </>
            )}
          </div>
          <button
            onClick={onClose}
            className="ml-4 px-3 py-1 text-gh-text-muted hover:text-gh-text transition-colors"
          >
            ✕
          </button>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <span className="text-gh-text-muted">Loading file content...</span>
            </div>
          ) : error ? (
            <div className="bg-red-500/10 border border-red-500/30 rounded p-4 text-red-400">
              {error}
            </div>
          ) : (
            <pre className="text-sm text-gh-text whitespace-pre-wrap break-words font-mono bg-gh-bg p-4 rounded">
              {file?.content}
            </pre>
          )}
        </div>
      </div>
    </div>
  )
}
