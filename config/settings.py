"""
Application configuration settings
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings configuration"""
    
    # Application settings
    app_name: str = "MCP-Server Development Platform"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # File paths
    base_dir: Path = Path(__file__).parent.parent
    projects_dir: Path = base_dir / "projects"
    logs_dir: Path = base_dir / "logs"
    templates_dir: Path = base_dir / "frontend" / "templates"
    static_dir: Path = base_dir / "frontend" / "static"
    
    # MCP settings
    mcp_inspector_enabled: bool = Field(default=True, env="MCP_INSPECTOR_ENABLED")
    mcp_default_port: int = Field(default=3000, env="MCP_DEFAULT_PORT")
    
    # System settings
    uv_command: str = Field(default="uv", env="UV_COMMAND")
    python_command: str = Field(default="python3", env="PYTHON_COMMAND")
    max_concurrent_projects: int = Field(default=10, env="MAX_CONCURRENT_PROJECTS")
    
    # Deployment settings
    systemd_service_dir: Path = Path("/etc/systemd/system")
    service_user: str = Field(default="pi", env="SERVICE_USER")
    service_group: str = Field(default="pi", env="SERVICE_GROUP")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings() 