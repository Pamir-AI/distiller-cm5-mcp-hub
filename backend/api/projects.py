"""
Projects API endpoints
"""

from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.models.project import (
    ProjectCreate, ProjectInfo, ProjectStats
)
from backend.services.project_manager import project_manager

router = APIRouter()

@router.post("/projects", response_model=ProjectInfo)
async def create_project(project_data: ProjectCreate):
    """Create a new MCP-Server project"""
    try:
        project = await project_manager.create_project(project_data)
        return project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects", response_model=List[ProjectInfo])
async def list_projects():
    """List all projects"""
    try:
        projects = await project_manager.list_projects()
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}", response_model=ProjectInfo)
async def get_project(project_id: str):
    """Get project information"""
    project = await project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    try:
        success = await project_manager.delete_project(project_id)
        if success:
            return {"message": "Project deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete project")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/install")
async def install_dependencies(project_id: str):
    """Install project dependencies"""
    try:
        success = await project_manager.install_dependencies(project_id)
        if success:
            return {"message": "Dependencies installed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to install dependencies")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(project_id: str):
    """Get project statistics"""
    try:
        stats = await project_manager.get_project_stats(project_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/files")
async def list_project_files(project_id: str):
    """List files in the project"""
    project = await project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        from pathlib import Path
        project_path = Path(project.path)
        files = []
        
        if project_path.exists():
            for file_path in project_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(project_path)
                    files.append({
                        "name": str(relative_path),
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime
                    })
        
        return {"files": files}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 