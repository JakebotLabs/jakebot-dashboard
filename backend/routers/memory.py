"""Memory API endpoints"""
import time
from fastapi import APIRouter, Query, HTTPException
from ..models.memory import (
    SearchResponse, SearchResult, MemoryStatus,
    FileContent, DeleteChunkResponse, ReindexJob, GraphExport
)
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


# Phase 2 endpoints
@router.get("/memory/file", response_model=FileContent)
async def read_file(path: str = Query(..., description="Relative path to file")):
    """Read a file from workspace (path traversal protected)"""
    try:
        data = adapter.read_file(path)
        return FileContent(**data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/chunk/{chunk_id}", response_model=DeleteChunkResponse)
async def delete_chunk(chunk_id: str):
    """Delete a chunk from vector memory"""
    deleted = adapter.delete_chunk(chunk_id)
    return DeleteChunkResponse(chunk_id=chunk_id, deleted=deleted)


@router.post("/memory/reindex", response_model=ReindexJob)
async def reindex_memory():
    """Trigger memory reindex"""
    result = adapter.reindex()
    return ReindexJob(**result)


@router.get("/memory/graph", response_model=GraphExport)
async def get_graph():
    """Get knowledge graph export"""
    data = adapter.get_graph()
    return GraphExport(**data)
