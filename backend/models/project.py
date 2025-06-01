"""
Project data models
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from pathlib import Path

class ProjectStatus(str, Enum):
    """Project status enumeration"""
    CREATED = "created"
    UPLOADING = "uploading"
    INSTALLING = "installing"
    DEBUGGING = "debugging"
    DEPLOYED = "deployed"
    ERROR = "error"
    STOPPED = "stopped"

class ProjectCreate(BaseModel):
    """Project creation request model"""
    name: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    description: Optional[str] = Field(None, max_length=200)
    python_version: str = Field(default="3.11")

class FileUpload(BaseModel):
    """File upload information"""
    filename: str
    content: str
    size: int

class ProjectInfo(BaseModel):
    """Project information model"""
    id: str
    name: str
    description: Optional[str]
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    path: str
    python_version: str
    
    # MCP-specific fields
    mcp_script_uploaded: bool = False
    dependencies_installed: bool = False
    debug_session_active: bool = False
    deployment_active: bool = False
    service_port: Optional[int] = None
    
    # File information
    uploaded_files: List[str] = []
    requirements_file: Optional[str] = None

class MCPTool(BaseModel):
    """MCP tool information"""
    name: str
    description: str
    parameters: Dict[str, Any]

class MCPResource(BaseModel):
    """MCP resource information"""
    uri: str
    name: str
    description: str
    mime_type: str

class MCPServerInfo(BaseModel):
    """MCP server information"""
    name: str
    version: str
    tools: List[MCPTool] = []
    resources: List[MCPResource] = []

class DebugRequest(BaseModel):
    """Debug request model"""
    tool_name: str
    parameters: Dict[str, Any] = {}

class DebugResponse(BaseModel):
    """Debug response model"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float

class DeploymentConfig(BaseModel):
    """Deployment configuration"""
    service_name: str
    port: int = Field(default=3000, ge=1024, le=65535)
    auto_start: bool = True
    enable_logging: bool = True
    
class LogEntry(BaseModel):
    """Log entry model"""
    timestamp: datetime
    level: str
    message: str
    source: str

class ProjectStats(BaseModel):
    """Project statistics"""
    total_files: int
    total_size_bytes: int
    last_activity: Optional[datetime]
    uptime_seconds: Optional[int] = None 