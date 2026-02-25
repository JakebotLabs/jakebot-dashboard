"""Configuration management for Jakebot Dashboard"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Dashboard configuration"""
    host: str = "127.0.0.1"
    port: int = 7842
    auth_enabled: bool = False
    auth_token: str = ""
    workspace_path: str = "/home/jakebot/.openclaw/workspace"
    vector_memory_path: str = "/home/jakebot/.openclaw/workspace/vector_memory"
    healthkit_path: str = "/home/jakebot/.openclaw/workspace/healthkit_internal"
    
    model_config = SettingsConfigDict(env_prefix="JAKEBOT_DASHBOARD_")


settings = Settings()
