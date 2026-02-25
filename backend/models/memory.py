"""Memory API models"""
from pydantic import BaseModel


class SearchResult(BaseModel):
    """Single search result from vector memory"""
    chunk_id: str
    content: str
    source: str
    section: str
    score: float


class SearchResponse(BaseModel):
    """Search response with results and metadata"""
    results: list[SearchResult]
    query: str
    took_ms: float


class MemoryStatus(BaseModel):
    """Memory system status"""
    chunks: int
    nodes: int
    edges: int
    files_indexed: int
    last_sync: str
    last_sync_ago: str
    db_size_mb: float


# Phase 2 additions
class FileContent(BaseModel):
    """File content response"""
    path: str
    content: str
    size_bytes: int


class DeleteChunkResponse(BaseModel):
    """Chunk deletion response"""
    chunk_id: str
    deleted: bool


class ReindexJob(BaseModel):
    """Reindex job status"""
    job_id: str
    status: str  # "running" | "complete" | "failed"
    started_at: str
    completed_at: str | None = None
    chunks_indexed: int | None = None
    error: str | None = None


class GraphExport(BaseModel):
    """Graph export response"""
    nodes: int
    edges: int
    data: dict  # raw networkx JSON
