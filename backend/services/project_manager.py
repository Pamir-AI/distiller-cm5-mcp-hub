"""
Project management service
Handles project creation, file operations, and lifecycle management
"""

import asyncio
import json
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiofiles
from fastapi import HTTPException

from backend.models.project import (
    ProjectInfo, ProjectStatus, ProjectCreate, ProjectStats
)
from config.settings import settings


class ProjectManager:
    """Manages MCP-Server projects"""
    
    def __init__(self):
        self.projects: Dict[str, ProjectInfo] = {}
        self.active_processes: Dict[str, subprocess.Popen] = {}
        
    async def create_project(self, project_data: ProjectCreate) -> ProjectInfo:
        """Create a new MCP-Server project"""
        project_id = str(uuid.uuid4())
        project_path = settings.projects_dir / project_data.name
        
        # Check if project already exists
        if project_path.exists():
            raise HTTPException(status_code=400, detail="Project already exists")
        
        try:
            # Create project directory
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize uv project
            await self._run_uv_command(
                ["init", "--python", project_data.python_version],
                cwd=project_path
            )
            
            # Create project info
            project_info = ProjectInfo(
                id=project_id,
                name=project_data.name,
                description=project_data.description,
                status=ProjectStatus.CREATED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                path=str(project_path),
                python_version=project_data.python_version
            )
            
            # Save project metadata
            await self._save_project_metadata(project_info)
            
            self.projects[project_id] = project_info
            return project_info
            
        except Exception as e:
            # Cleanup on failure
            if project_path.exists():
                shutil.rmtree(project_path)
            raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")
    
    async def install_dependencies(self, project_id: str) -> bool:
        """Install project dependencies using uv"""
        project = await self.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_path = Path(project.path)
        
        try:
            # Update project status
            project.status = ProjectStatus.INSTALLING
            await self._save_project_metadata(project)
            
            # Install dependencies
            if project.requirements_file:
                if project.requirements_file == "requirements.txt":
                    await self._run_uv_command(
                        ["pip", "install", "-r", "requirements.txt"],
                        cwd=project_path
                    )
                elif project.requirements_file == "pyproject.toml":
                    await self._run_uv_command(
                        ["sync"],
                        cwd=project_path
                    )
            else:
                # Install common MCP dependencies
                await self._run_uv_command(
                    ["add", "mcp", "pydantic", "asyncio"],
                    cwd=project_path
                )
            
            # Update project status
            project.dependencies_installed = True
            project.status = ProjectStatus.CREATED
            project.updated_at = datetime.now()
            
            await self._save_project_metadata(project)
            self.projects[project_id] = project
            
            return True
            
        except Exception as e:
            project.status = ProjectStatus.ERROR
            await self._save_project_metadata(project)
            raise HTTPException(status_code=500, detail=f"Failed to install dependencies: {str(e)}")
    
    async def get_project(self, project_id: str) -> Optional[ProjectInfo]:
        """Get project information"""
        if project_id in self.projects:
            return self.projects[project_id]
        
        # Try to load from disk
        try:
            metadata_path = settings.projects_dir / f"{project_id}.json"
            if metadata_path.exists():
                async with aiofiles.open(metadata_path, 'r') as f:
                    data = await f.read()
                    project_info = ProjectInfo.model_validate_json(data)
                    self.projects[project_id] = project_info
                    return project_info
        except Exception:
            pass
        
        return None
    
    async def list_projects(self) -> List[ProjectInfo]:
        """List all projects"""
        projects = []
        processed_dirs = set()
        
        # First, load all project metadata files
        for metadata_file in settings.projects_dir.glob("*.json"):
            try:
                async with aiofiles.open(metadata_file, 'r') as f:
                    data = await f.read()
                    project_info = ProjectInfo.model_validate_json(data)
                    projects.append(project_info)
                    self.projects[project_info.id] = project_info
                    # Mark this directory as processed
                    processed_dirs.add(Path(project_info.path).name)
            except Exception:
                continue
        
        # Then, scan for directories that don't have metadata files (imported projects)
        for project_dir in settings.projects_dir.iterdir():
            if (project_dir.is_dir() and 
                not project_dir.name.startswith('.') and 
                project_dir.name not in processed_dirs):
                
                try:
                    imported_project = await self._import_existing_project(project_dir)
                    if imported_project:
                        projects.append(imported_project)
                        self.projects[imported_project.id] = imported_project
                except Exception as e:
                    print(f"Failed to import project {project_dir.name}: {e}")
                    continue
        
        return projects
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        project = await self.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        try:
            # Stop any running processes
            if project_id in self.active_processes:
                process = self.active_processes[project_id]
                process.terminate()
                del self.active_processes[project_id]
            
            # Remove project directory
            project_path = Path(project.path)
            if project_path.exists():
                shutil.rmtree(project_path)
            
            # Remove metadata file
            metadata_path = settings.projects_dir / f"{project_id}.json"
            if metadata_path.exists():
                metadata_path.unlink()
            
            # Remove from memory
            if project_id in self.projects:
                del self.projects[project_id]
            
            return True
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")
    
    async def get_project_stats(self, project_id: str) -> ProjectStats:
        """Get project statistics"""
        project = await self.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_path = Path(project.path)
        total_files = 0
        total_size = 0
        
        print(f"Checking project path: {project_path}")
        print(f"Path exists: {project_path.exists()}")
        
        # Directories and files to exclude from counting
        exclude_dirs = {'.venv', 'venv', '.git', '__pycache__', '.pytest_cache', 
                       'node_modules', '.mypy_cache', '.coverage', 'dist', 'build',
                       '.env', '.vscode', '.idea'}
        exclude_files = {'uv.lock', '.gitignore', '.DS_Store', '.env', 'poetry.lock',
                        'requirements.txt.bak', '*.pyc', '*.pyo', '*.pyd'}
        
        # File extensions to include (relevant for MCP projects)
        include_extensions = {'.py', '.toml', '.txt', '.md', '.json', '.yaml', '.yml', 
                             '.cfg', '.ini', '.sh', '.dockerfile', '.requirements'}
        
        if project_path.exists():
            files_found = []
            for file_path in project_path.rglob("*"):
                if file_path.is_file():
                    # Skip if in excluded directory
                    if any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs):
                        continue
                    
                    # Skip excluded files
                    if file_path.name in exclude_files:
                        continue
                    
                    # Include only relevant file extensions
                    if file_path.suffix.lower() in include_extensions or file_path.name in {
                        'Dockerfile', 'Makefile', 'LICENSE', 'CHANGELOG', 'MANIFEST.in'
                    }:
                        total_files += 1
                        total_size += file_path.stat().st_size
                        files_found.append(str(file_path.relative_to(project_path)))
            
            print(f"Found {total_files} relevant files: {files_found[:10]}...")  # Show first 10 files
        
        uptime = None
        if project_id in self.active_processes:
            # Calculate uptime if process is running
            uptime = 0  # Placeholder - implement actual uptime calculation
        
        result = ProjectStats(
            total_files=total_files,
            total_size_bytes=total_size,
            last_activity=project.updated_at,
            uptime_seconds=uptime
        )
        
        print(f"Returning stats: {result}")
        return result
    
    async def _run_uv_command(self, args: List[str], cwd: Path) -> subprocess.CompletedProcess:
        """Run a uv command asynchronously"""
        cmd = [settings.uv_command] + args
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Command failed: {stderr.decode()}")
        
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr
        )
    
    async def _save_project_metadata(self, project: ProjectInfo) -> None:
        """Save project metadata to disk"""
        metadata_path = settings.projects_dir / f"{project.id}.json"
        
        async with aiofiles.open(metadata_path, 'w') as f:
            await f.write(project.model_dump_json(indent=2))

    async def _import_existing_project(self, project_dir: Path) -> Optional[ProjectInfo]:
        """Import an existing MCP project directory"""
        try:
            # Check if it looks like an MCP project
            pyproject_path = project_dir / "pyproject.toml"
            readme_path = project_dir / "README.md"
            python_version_path = project_dir / ".python-version"
            
            # Must have either pyproject.toml or be clearly an MCP project
            if not pyproject_path.exists():
                return None
            
            # Read project information
            project_name = project_dir.name
            description = ""
            python_version = "3.11"  # default
            requirements_file = None
            
            # Extract info from pyproject.toml
            if pyproject_path.exists():
                try:
                    # Try to use tomllib (Python 3.11+) or tomli
                    try:
                        import tomllib
                        async with aiofiles.open(pyproject_path, 'rb') as f:
                            content = await f.read()
                            pyproject_data = tomllib.loads(content.decode('utf-8'))
                    except ImportError:
                        try:
                            import tomli
                            async with aiofiles.open(pyproject_path, 'rb') as f:
                                content = await f.read()
                                pyproject_data = tomli.loads(content.decode('utf-8'))
                        except ImportError:
                            # Fallback: basic text parsing
                            async with aiofiles.open(pyproject_path, 'r') as f:
                                content = await f.read()
                                if 'mcp' not in content.lower():
                                    return None  # Not an MCP project
                                # Extract name from content if possible
                                for line in content.split('\n'):
                                    if line.strip().startswith('name ='):
                                        project_name = line.split('=')[1].strip().strip('"\'')
                                        break
                                requirements_file = "pyproject.toml"
                                pyproject_data = None
                    
                    if pyproject_data and 'project' in pyproject_data:
                        proj_info = pyproject_data['project']
                        if 'name' in proj_info:
                            project_name = proj_info['name']
                        if 'description' in proj_info:
                            description = proj_info['description']
                        
                        # Check if it has MCP dependencies
                        deps = proj_info.get('dependencies', [])
                        has_mcp = any('mcp' in str(dep).lower() for dep in deps)
                        if not has_mcp:
                            return None  # Not an MCP project
                    
                    requirements_file = "pyproject.toml"
                except Exception:
                    pass
            
            # Check for Python version
            if python_version_path.exists():
                try:
                    async with aiofiles.open(python_version_path, 'r') as f:
                        version_content = await f.read()
                        python_version = version_content.strip()
                except Exception:
                    pass
            
            # Extract description from README if not found
            if not description and readme_path.exists():
                try:
                    async with aiofiles.open(readme_path, 'r') as f:
                        readme_content = await f.read()
                        lines = readme_content.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                description = line[:200]  # First non-header line, truncated
                                break
                except Exception:
                    pass
            
            # Create project info
            project_id = str(uuid.uuid4())
            project_info = ProjectInfo(
                id=project_id,
                name=project_name,
                description=description or f"Imported MCP project: {project_name}",
                status=ProjectStatus.CREATED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                path=str(project_dir),
                python_version=python_version,
                requirements_file=requirements_file,
                dependencies_installed=True,  # Assume dependencies are installed in imported projects
                mcp_script_uploaded=True,  # Assume it's a complete MCP project
                uploaded_files=[]  # Will be populated if needed
            )
            
            # Save metadata for future use
            await self._save_project_metadata(project_info)
            
            return project_info
            
        except Exception as e:
            print(f"Error importing project {project_dir.name}: {e}")
            return None


# Global project manager instance
project_manager = ProjectManager() 