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
