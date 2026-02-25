"""Health API endpoints"""
from fastapi import APIRouter, Query
from ..models.health import (
    HealthSnapshot, HealthHistory, HistoryPoint,
    ServiceStatus, HealthIssue, Monitor
)
from ..adapters.healthkit_adapter import HealthkitAdapter

router = APIRouter(tags=["health"])
adapter = HealthkitAdapter()


@router.get("/health/status", response_model=HealthSnapshot)
async def get_health_status():
    """Get current health status snapshot"""
    data = adapter.get_status()
    
    return HealthSnapshot(
        timestamp=data["timestamp"],
        mode=data["mode"],
        uptime_percent=data["uptime_percent"],
        metrics=data["metrics"],
        services=[ServiceStatus(**s) for s in data["services"]],
        issues=[HealthIssue(**i) for i in data["issues"]]
    )


@router.get("/health/history", response_model=HealthHistory)
async def get_health_history(
    hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve")
):
    """Get health history over time window"""
    points = adapter.get_history(hours)
    
    return HealthHistory(
        window=f"{hours}h",
        points=[HistoryPoint(**p) for p in points]
    )


@router.get("/health/monitors", response_model=list[Monitor])
async def get_monitors():
    """Get list of configured monitors"""
    monitors = adapter.get_monitors()
    return [Monitor(**m) for m in monitors]


@router.post("/health/check", response_model=HealthSnapshot)
async def run_health_check():
    """Run a health check now"""
    data = adapter.run_check()
    
    return HealthSnapshot(
        timestamp=data["timestamp"],
        mode=data["mode"],
        uptime_percent=data["uptime_percent"],
        metrics=data["metrics"],
        services=[ServiceStatus(**s) for s in data["services"]],
        issues=[HealthIssue(**i) for i in data["issues"]]
    )
