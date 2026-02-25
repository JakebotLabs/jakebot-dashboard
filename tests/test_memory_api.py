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
