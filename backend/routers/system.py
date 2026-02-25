"""System API endpoints"""
import sys
import platform
from pathlib import Path
from fastapi import APIRouter
from ..config import settings

router = APIRouter(tags=["system"])


@router.get("/system/status")
async def get_system_status():
    """Get system and product status"""
    workspace = Path(settings.workspace_path).expanduser()
    vector_memory_path = Path(settings.vector_memory_path).expanduser()
    healthkit_path = Path(settings.healthkit_path).expanduser()
    
    # Check persistent_memory
    pm_installed = vector_memory_path.exists() and (vector_memory_path / "venv").exists()
    pm_status = "ready" if pm_installed else "not_installed"
    if pm_installed:
        # Quick health check
        chroma_db = vector_memory_path / "chroma_db"
        if not chroma_db.exists():
            pm_status = "error"
    
    # Check agent_healthkit
    hk_installed = healthkit_path.exists()
    hk_status = "ready" if hk_installed else "not_installed"
    
    return {
        "dashboard_version": "0.2.0a1",
        "products": {
            "persistent_memory": {
                "installed": pm_installed,
                "path": str(vector_memory_path) if pm_installed else None,
                "status": pm_status
            },
            "agent_healthkit": {
                "installed": hk_installed,
                "path": str(healthkit_path) if hk_installed else None,
                "status": hk_status
            }
        },
        "python_version": sys.version,
        "platform": platform.platform()
    }
