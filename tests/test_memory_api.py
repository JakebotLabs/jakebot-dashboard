"""Tests for memory API endpoints"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.config import settings


@pytest.mark.asyncio
async def test_system_status():
    """Test system status endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/system/status")
    
    assert resp.status_code == 200
    data = resp.json()
    assert "products" in data
    assert "dashboard_version" in data
    assert "python_version" in data
    assert "platform" in data
    assert "persistent_memory" in data["products"]
    assert "agent_healthkit" in data["products"]


@pytest.mark.asyncio
async def test_memory_files():
    """Test memory files listing"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/memory/files")
    
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_memory_search():
    """Test memory search endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/memory/search?q=memory&n=3")
    
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert "query" in data
    assert "took_ms" in data
    assert data["query"] == "memory"
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_memory_status():
    """Test memory status endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/memory/status")
    
    assert resp.status_code == 200
    data = resp.json()
    assert "chunks" in data
    assert "nodes" in data
    assert "edges" in data
    assert "files_indexed" in data
    assert "last_sync" in data
    assert "db_size_mb" in data


@pytest.mark.asyncio
async def test_health():
    """Test health check endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/health")
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_search_missing_query():
    """Test that search without query param returns 422"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/memory/search")
    
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_auth_required_when_enabled():
    """Test that auth is enforced when enabled"""
    from fastapi.exceptions import HTTPException
    
    # Save original settings
    original_enabled = settings.auth_enabled
    original_token = settings.auth_token
    
    try:
        # Enable auth
        settings.auth_enabled = True
        settings.auth_token = "test-secret-token-12345"
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            with pytest.raises(HTTPException) as exc_info:
                await ac.get("/api/memory/files")
        
        assert exc_info.value.status_code == 401
    finally:
        # Restore original settings
        settings.auth_enabled = original_enabled
        settings.auth_token = original_token


@pytest.mark.asyncio
async def test_auth_valid_token():
    """Test that valid token is accepted"""
    # Save original settings
    original_enabled = settings.auth_enabled
    original_token = settings.auth_token
    
    try:
        # Enable auth
        settings.auth_enabled = True
        settings.auth_token = "test-secret-token-12345"
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/memory/files",
                headers={"Authorization": "Bearer test-secret-token-12345"}
            )
        
        assert resp.status_code == 200
    finally:
        # Restore original settings
        settings.auth_enabled = original_enabled
        settings.auth_token = original_token


# Phase 2 tests

@pytest.mark.asyncio
async def test_memory_file_read():
    """Test reading a file from workspace"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/memory/file?path=MEMORY.md")
    
    # May be 200 or 404 depending on whether MEMORY.md exists
    assert resp.status_code in [200, 404]
    if resp.status_code == 200:
        data = resp.json()
        assert "path" in data
        assert "content" in data
        assert "size_bytes" in data


@pytest.mark.asyncio
async def test_memory_file_traversal():
    """Test that path traversal is blocked"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/memory/file?path=../../../etc/passwd")
    
    # Should be 400 (bad request) for path traversal attempt
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_memory_graph():
    """Test getting the knowledge graph"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/memory/graph")
    
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "edges" in data
    assert "data" in data


@pytest.mark.asyncio
async def test_health_status():
    """Test health status endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/health/status")
    
    assert resp.status_code == 200
    data = resp.json()
    assert "timestamp" in data
    assert "mode" in data
    assert "uptime_percent" in data
    assert "metrics" in data
    assert "services" in data
    assert "issues" in data


@pytest.mark.asyncio
async def test_health_history():
    """Test health history endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/health/history?hours=24")
    
    assert resp.status_code == 200
    data = resp.json()
    assert "window" in data
    assert "points" in data
    assert isinstance(data["points"], list)


@pytest.mark.asyncio
async def test_health_monitors():
    """Test health monitors listing endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/health/monitors")
    
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
