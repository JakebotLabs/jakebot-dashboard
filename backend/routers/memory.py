"""Memory API endpoints"""
import time
from fastapi import APIRouter, Query
from ..models.memory import SearchResponse, SearchResult, MemoryStatus
from ..adapters.memory_adapter import MemoryAdapter

router = APIRouter(tags=["memory"])
adapter = MemoryAdapter()


@router.get("/memory/search", response_model=SearchResponse)
async def search_memory(
    q: str = Query(..., description="Search query"),
    n: int = Query(5, ge=1, le=20, description="Number of results")
):
    """Search vector memory"""
    start = time.time()
    results = adapter.search(q, n)
    took_ms = round((time.time() - start) * 1000, 2)
    
    return SearchResponse(
        results=[SearchResult(**r) for r in results],
        query=q,
        took_ms=took_ms
    )


@router.get("/memory/files")
async def list_files():
    """List indexed files"""
    return adapter.list_files()


@router.get("/memory/status", response_model=MemoryStatus)
async def get_memory_status():
    """Get memory system status"""
    status = adapter.get_status()
    last_sync, last_sync_ago = adapter.get_last_sync()
    db_size = adapter.get_db_size()
    files = adapter.list_files()
    
    return MemoryStatus(
        chunks=status.get('chunks', 0),
        nodes=status.get('nodes', 0),
        edges=status.get('edges', 0),
        files_indexed=len(files),
        last_sync=last_sync,
        last_sync_ago=last_sync_ago,
        db_size_mb=db_size
    )
