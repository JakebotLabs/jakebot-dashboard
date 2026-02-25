"""Health API models"""
from pydantic import BaseModel


class ServiceStatus(BaseModel):
    """Individual service status"""
    name: str
    status: str  # "up" | "down" | "disabled"


class HealthIssue(BaseModel):
    """Detected health issue"""
    id: str
    severity: str  # "warning" | "critical"
    message: str
    detected_at: str
    can_auto_heal: bool = False


class HealthSnapshot(BaseModel):
    """Current health status snapshot"""
    timestamp: str
    mode: str
    uptime_percent: float
    metrics: dict
    services: list[ServiceStatus]
    issues: list[HealthIssue]


class HistoryPoint(BaseModel):
    """Single point in health history"""
    timestamp: str
    memory_md_kb: float
    workspace_kb: float
    issues_count: int
    services_up: int
    services_total: int


class HealthHistory(BaseModel):
    """Health history over time window"""
    window: str
    points: list[HistoryPoint]


class Monitor(BaseModel):
    """Monitor configuration"""
    id: str
    name: str
    enabled: bool
    description: str = ""
