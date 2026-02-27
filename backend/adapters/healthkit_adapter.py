"""HealthKit adapter - interfaces with healthkit_internal"""
import subprocess
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from ..config import settings


def _get_paths():
    """Get workspace and healthkit paths from settings"""
    workspace = Path(settings.workspace_path).expanduser()
    healthkit = Path(settings.healthkit_path).expanduser()
    return workspace, healthkit


def _get_python_exec():
    """Get python executable, preferring venv if available.

    On Windows the venv layout is Scripts/python.exe, on Unix it's bin/python.
    """
    _, healthkit = _get_paths()
    if sys.platform == "win32":
        venv_python = healthkit / "venv" / "Scripts" / "python.exe"
    else:
        venv_python = healthkit / "venv" / "bin" / "python"
    return str(venv_python) if venv_python.exists() else sys.executable


class HealthkitAdapter:
    """Adapter for healthkit_internal monitoring system"""
    
    def get_status(self) -> dict:
        """Get current health status by running monitor or reading cached metrics"""
        workspace, healthkit = _get_paths()
        
        # First try to read cached metrics from latest run
        metrics_file = healthkit / "logs" / "latest_metrics.json"
        issues_file = healthkit / "logs" / "latest_issues.json"
        config_file = healthkit / "config.json"
        
        metrics = {}
        issues = []
        mode = "observe"
        
        # Load config for mode
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                mode = config.get("mode", "observe")
            except Exception:
                pass
        
        # Load cached metrics
        if metrics_file.exists():
            try:
                with open(metrics_file) as f:
                    metrics = json.load(f)
            except Exception:
                pass
        
        # Load cached issues
        if issues_file.exists():
            try:
                with open(issues_file) as f:
                    issues = json.load(f)
            except Exception:
                pass
        
        # Build snapshot from cached data
        timestamp = metrics.get("timestamp", datetime.now().isoformat())
        memory_metrics = metrics.get("memory", {})
        service_metrics = metrics.get("services", {})
        
        # Calculate uptime from service statuses
        services = []
        up_count = 0
        for svc_name, svc_status in service_metrics.items():
            # Normalize service name
            name = svc_name.replace("_status", "")
            status = "up" if svc_status in ["accessible", "synced", "up"] else (
                "disabled" if svc_status == "disabled" else "down"
            )
            if status == "up":
                up_count += 1
            services.append({"name": name, "status": status})
        
        total_services = len(services) if services else 1
        uptime_percent = (up_count / total_services) * 100 if total_services else 100.0
        
        # Convert issues to API format
        api_issues = []
        for i, issue in enumerate(issues):
            api_issues.append({
                "id": f"issue_{i}",
                "severity": issue.get("severity", "warning"),
                "message": issue.get("message", str(issue)),
                "detected_at": timestamp,
                "can_auto_heal": issue.get("can_auto_heal", False)
            })
        
        return {
            "timestamp": timestamp,
            "mode": mode.upper(),
            "uptime_percent": uptime_percent,
            "metrics": {
                "memory_md_kb": memory_metrics.get("memory_md_size_kb", 0),
                "workspace_kb": memory_metrics.get("workspace_size_kb", 0),
                "vector_chunks": memory_metrics.get("vector_chunks", 0),
                "graph_nodes": memory_metrics.get("graph_nodes", 0),
                "graph_edges": memory_metrics.get("graph_edges", 0)
            },
            "services": services,
            "issues": api_issues
        }
    
    def get_history(self, hours: int = 24) -> list[dict]:
        """Get health history from report files"""
        workspace, healthkit = _get_paths()
        logs_dir = healthkit / "logs"
        
        if not logs_dir.exists():
            return []
        
        points = []
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Parse report files
        for report_file in sorted(logs_dir.glob("report_*.txt")):
            try:
                # Extract timestamp from filename: report_YYYYMMDD_HHMMSS.txt
                name_parts = report_file.stem.split("_")
                if len(name_parts) >= 3:
                    date_str = name_parts[1]
                    time_str = name_parts[2]
                    timestamp = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    
                    if timestamp < cutoff:
                        continue
                    
                    # Parse report content
                    content = report_file.read_text()
                    point = self._parse_report(content, timestamp)
                    if point:
                        points.append(point)
            except Exception:
                continue
        
        # Also check for JSON metrics logs
        for metrics_file in sorted(logs_dir.glob("metrics_*.json")):
            try:
                with open(metrics_file) as f:
                    data = json.load(f)
                
                timestamp_str = data.get("timestamp", "")
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    if timestamp.replace(tzinfo=None) < cutoff:
                        continue
                    
                    memory = data.get("memory", {})
                    services = data.get("services", {})
                    
                    # Count up services
                    up = sum(1 for v in services.values() if v in ["accessible", "synced", "up"])
                    
                    points.append({
                        "timestamp": timestamp_str,
                        "memory_md_kb": memory.get("memory_md_size_kb", 0),
                        "workspace_kb": memory.get("workspace_size_kb", 0),
                        "issues_count": 0,  # Would need issues file
                        "services_up": up,
                        "services_total": len(services)
                    })
            except Exception:
                continue
        
        # If no history, return single point from current status
        if not points:
            status = self.get_status()
            points.append({
                "timestamp": status["timestamp"],
                "memory_md_kb": status["metrics"].get("memory_md_kb", 0),
                "workspace_kb": status["metrics"].get("workspace_kb", 0),
                "issues_count": len(status.get("issues", [])),
                "services_up": sum(1 for s in status["services"] if s["status"] == "up"),
                "services_total": len(status["services"])
            })
        
        return sorted(points, key=lambda x: x["timestamp"])
    
    def _parse_report(self, content: str, timestamp: datetime) -> dict | None:
        """Parse a text report file into a history point"""
        try:
            memory_md_kb = 0
            workspace_kb = 0
            issues_count = 0
            services_up = 0
            services_total = 0
            
            for line in content.split('\n'):
                line = line.strip()
                
                if "MEMORY.md:" in line:
                    # Extract KB value
                    parts = line.split("MEMORY.md:")
                    if len(parts) > 1:
                        num_str = parts[1].strip().split()[0]
                        memory_md_kb = float(num_str)
                
                elif "Workspace:" in line:
                    parts = line.split("Workspace:")
                    if len(parts) > 1:
                        num_str = parts[1].strip().split()[0]
                        workspace_kb = float(num_str)
                
                elif "Detected Issues" in line:
                    # Format: "⚠️  Detected Issues (N):"
                    import re
                    nums = re.findall(r'\((\d+)\)', line)
                    if nums:
                        issues_count = int(nums[0])
                
                elif any(svc in line for svc in ["Ollama:", "ChromaDB:", "Vector Memory:"]):
                    services_total += 1
                    if any(status in line for status in ["accessible", "synced", "up"]):
                        services_up += 1
            
            return {
                "timestamp": timestamp.isoformat(),
                "memory_md_kb": memory_md_kb,
                "workspace_kb": workspace_kb,
                "issues_count": issues_count,
                "services_up": services_up,
                "services_total": services_total if services_total > 0 else 3
            }
        except Exception:
            return None
    
    def get_monitors(self) -> list[dict]:
        """Get list of configured monitors"""
        workspace, healthkit = _get_paths()
        config_file = healthkit / "config.json"
        
        monitors = []
        
        # Default monitors based on healthkit structure
        default_monitors = [
            {"id": "context_bloat", "name": "Context Bloat Detector", "enabled": True, 
             "description": "Monitors MEMORY.md and workspace size thresholds"},
            {"id": "service_health", "name": "Service Health Detector", "enabled": True,
             "description": "Monitors Ollama, ChromaDB, and Vector Memory services"},
            {"id": "model_failure", "name": "Model Failure Detector", "enabled": True,
             "description": "Scans logs for model API failures"},
            {"id": "config_integrity", "name": "Config Integrity Detector", "enabled": True,
             "description": "Validates config against oracle invariants"}
        ]
        
        # Check config for service-specific enabled states
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                
                services = config.get("services", {})
                
                # Update enabled state based on config
                for monitor in default_monitors:
                    if monitor["id"] == "service_health":
                        # Check if any service is enabled
                        enabled = any(
                            svc.get("enabled", True) 
                            for svc in services.values()
                        )
                        monitor["enabled"] = enabled
            except Exception:
                pass
        
        return default_monitors
    
    def run_check(self) -> dict:
        """Run a health check now and return results"""
        workspace, healthkit = _get_paths()
        monitor_script = healthkit / "monitor.py"
        
        if not monitor_script.exists():
            return self.get_status()  # Fallback to cached
        
        try:
            # Run monitor.py with venv python if available
            python_exec = _get_python_exec()
            result = subprocess.run(
                [python_exec, str(monitor_script)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(healthkit)
            )
            
            # The script saves to latest_metrics.json, so read fresh status
            return self.get_status()
        except subprocess.TimeoutExpired:
            return {
                "timestamp": datetime.now().isoformat(),
                "mode": "ERROR",
                "uptime_percent": 0,
                "metrics": {},
                "services": [],
                "issues": [{
                    "id": "timeout",
                    "severity": "critical",
                    "message": "Health check timed out after 60s",
                    "detected_at": datetime.now().isoformat(),
                    "can_auto_heal": False
                }]
            }
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "mode": "ERROR",
                "uptime_percent": 0,
                "metrics": {},
                "services": [],
                "issues": [{
                    "id": "error",
                    "severity": "critical",
                    "message": f"Health check failed: {str(e)}",
                    "detected_at": datetime.now().isoformat(),
                    "can_auto_heal": False
                }]
            }
