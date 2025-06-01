"""
Deployment API endpoints
Handles service deployment and process management
"""

import asyncio
import subprocess
import time
import signal
import os
from typing import Dict, List
from pathlib import Path
from fastapi import APIRouter, HTTPException

from backend.models.project import (
    DeploymentConfig, ProjectStatus, LogEntry
)
from backend.services.project_manager import project_manager
from config.settings import settings

router = APIRouter()

class SimpleDeploymentManager:
    """Manages simple process-based service deployment"""
    
    def __init__(self):
        self.deployed_services: Dict[str, Dict] = {}
        self.port_allocator = PortAllocator(start_port=3000)
        self.processes: Dict[str, subprocess.Popen] = {}
    
    async def deploy_service(self, project_id: str, config: DeploymentConfig) -> Dict:
        """Deploy the MCP service as a simple process"""
        project = await project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        try:
            # Stop existing service if running
            if project_id in self.deployed_services:
                await self.stop_service(project_id)
            
            # Update project status
            project.status = ProjectStatus.DEPLOYED
            project.deployment_active = True
            
            # Allocate port if not specified or if specified port is in use
            if config.port and not self._is_port_available(config.port):
                print(f"Warning: Requested port {config.port} is not available, allocating alternative")
                port = self.port_allocator.allocate()
            elif config.port:
                port = config.port
                self.port_allocator.allocated_ports.add(port)  # Mark as allocated
            else:
                port = self.port_allocator.allocate()
            
            project.service_port = port
            
            # Start the service process
            process = await self._start_service_process(project, config, port)
            
            if process and process.poll() is None:
                # Store deployment info
                self.deployed_services[project_id] = {
                    "service_name": config.service_name,
                    "port": port,
                    "start_time": time.time(),
                    "config": config.model_dump(),
                    "process_id": process.pid
                }
                self.processes[project_id] = process
                
                # Update project metadata
                await project_manager._save_project_metadata(project)
                
                return {
                    "project_id": project_id,
                    "service_name": config.service_name,
                    "port": port,
                    "status": "deployed",
                    "access_url": f"http://localhost:{port}",
                    "process_id": process.pid
                }
            else:
                # Process failed to start or died immediately
                process_error = "Process failed to start"
                if process:
                    try:
                        stdout, stderr = process.communicate(timeout=5)
                        if stderr:
                            process_error = f"Process error: {stderr}"
                        elif stdout:
                            process_error = f"Process output: {stdout}"
                    except subprocess.TimeoutExpired:
                        process_error = "Process started but may have issues (timeout getting output)"
                
                # Free the allocated port if process failed
                self.port_allocator.free(port)
                raise RuntimeError(f"Failed to start service process: {process_error}")
            
        except Exception as e:
            project.status = ProjectStatus.ERROR
            await project_manager._save_project_metadata(project)
            # Log the full error for debugging
            print(f"Deployment failed for project {project_id}: {str(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")
    
    async def _start_service_process(self, project, config: DeploymentConfig, port: int) -> subprocess.Popen:
        """Start the service as a simple Python process"""
        project_path = Path(project.path)
        
        # Find the main file (server.py, main.py, etc.)
        search_paths = [
            project_path,
            project_path / "src",
            project_path / "server"
        ]
        
        main_files = ['server.py', 'main.py', 'app.py', '__main__.py']
        main_file = None
        main_file_path = None
        
        for search_path in search_paths:
            if search_path.exists():
                for filename in main_files:
                    file_path = search_path / filename
                    if file_path.exists():
                        main_file = filename
                        main_file_path = file_path
                        break
            if main_file:
                break
        
        if not main_file:
            # Try to find any Python file that looks like an entry point
            for search_path in search_paths:
                if search_path.exists():
                    for py_file in search_path.glob('*.py'):
                        # Check if file contains main function or if __name__ == "__main__"
                        try:
                            content = py_file.read_text()
                            if ('if __name__ == "__main__"' in content or 
                                'def main(' in content or 
                                'async def main(' in content):
                                main_file = py_file.name
                                main_file_path = py_file
                                break
                        except:
                            continue
                if main_file:
                    break
        
        if not main_file:
            raise RuntimeError(f"No executable Python file found. Searched in: {[str(p) for p in search_paths]}")
        
        # Set up environment
        env = os.environ.copy()
        env['PORT'] = str(port)
        env['PYTHONPATH'] = str(project_path)
        
        # Create logs directory for this project
        try:
            logs_dir = settings.logs_dir / project.id
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Create log file paths
            log_file = logs_dir / f"service_{port}.log"
            error_log_file = logs_dir / f"service_{port}_error.log"
            
            # Store log file paths for later retrieval
            if not hasattr(self, 'log_files'):
                self.log_files = {}
            self.log_files[project.id] = {
                'stdout': str(log_file),
                'stderr': str(error_log_file)
            }
            
        except Exception as e:
            print(f"Warning: Could not create log files: {e}. Using PIPE instead.")
            # Fallback to PIPE if log file creation fails
            log_file = None
            error_log_file = None
        
        # Start the process from the directory containing the main file
        working_dir = main_file_path.parent
        cmd = [settings.python_command, str(main_file_path)]
        
        # Open log files safely
        stdout_handle = None
        stderr_handle = None
        
        try:
            if log_file and error_log_file:
                stdout_handle = open(log_file, 'w', buffering=1)
                stderr_handle = open(error_log_file, 'w', buffering=1)
                
                process = subprocess.Popen(
                    cmd,
                    cwd=str(working_dir),
                    env=env,
                    stdout=stdout_handle,
                    stderr=stderr_handle,
                    text=True
                )
            else:
                # Fallback to PIPE if log files couldn't be created
                process = subprocess.Popen(
                    cmd,
                    cwd=str(working_dir),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            # Give it a moment to start
            await asyncio.sleep(2)
            
            # Store file handles for later cleanup
            if not hasattr(self, 'log_handles'):
                self.log_handles = {}
            if stdout_handle and stderr_handle:
                self.log_handles[project.id] = {
                    'stdout': stdout_handle,
                    'stderr': stderr_handle
                }
            
            return process
            
        except Exception as e:
            # Clean up file handles if process creation failed
            if stdout_handle:
                stdout_handle.close()
            if stderr_handle:
                stderr_handle.close()
            raise e
    
    async def stop_service(self, project_id: str) -> bool:
        """Stop the deployed service"""
        project = await project_manager.get_project(project_id)
        if not project:
            return False
        
        try:
            # Stop the process
            if project_id in self.processes:
                process = self.processes[project_id]
                if process.poll() is None:  # Process is still running
                    try:
                        process.terminate()
                        # Wait a bit for graceful shutdown
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            # Force kill if not responding
                            process.kill()
                            process.wait()
                    except Exception as e:
                        print(f"Error stopping process: {e}")
                
                del self.processes[project_id]
            
            # Close log file handles if they exist
            if hasattr(self, 'log_handles') and project_id in self.log_handles:
                try:
                    handles = self.log_handles[project_id]
                    if 'stdout' in handles:
                        handles['stdout'].close()
                    if 'stderr' in handles:
                        handles['stderr'].close()
                    del self.log_handles[project_id]
                except Exception as e:
                    print(f"Error closing log handles: {e}")
            
            # Update project status
            project.deployment_active = False
            project.status = ProjectStatus.STOPPED
            await project_manager._save_project_metadata(project)
            
            # Free the port
            if project_id in self.deployed_services:
                port = self.deployed_services[project_id]["port"]
                self.port_allocator.free(port)
                del self.deployed_services[project_id]
            
            return True
            
        except Exception as e:
            print(f"Failed to stop service: {e}")
            return False
    
    async def get_service_status(self, project_id: str) -> Dict:
        """Get service deployment status"""
        project = await project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if project_id not in self.deployed_services:
            return {
                "deployed": False,
                "project_id": project_id
            }
        
        deployment = self.deployed_services[project_id]
        
        # Check if process is still running
        is_active = False
        if project_id in self.processes:
            process = self.processes[project_id]
            is_active = process.poll() is None
        
        return {
            "deployed": True,
            "active": is_active,
            "project_id": project_id,
            "service_name": deployment["service_name"],
            "port": deployment["port"],
            "uptime": time.time() - deployment["start_time"],
            "access_url": f"http://localhost:{deployment['port']}",
            "process_id": deployment.get("process_id")
        }
    
    async def get_service_logs(self, project_id: str, lines: int = 50) -> List[LogEntry]:
        """Get service logs from log files"""
        if project_id not in self.deployed_services:
            return []
        
        try:
            logs = []
            
            # Check if we have log files for this project
            if hasattr(self, 'log_files') and project_id in self.log_files:
                log_file_paths = self.log_files[project_id]
                
                # Read stdout log file
                stdout_path = log_file_paths['stdout']
                if os.path.exists(stdout_path):
                    try:
                        with open(stdout_path, 'r') as f:
                            stdout_lines = f.readlines()[-lines:]
                            for line in stdout_lines:
                                line = line.strip()
                                if line:
                                    # Parse log level from line if possible
                                    level = "INFO"
                                    if "ERROR" in line.upper() or "FAILED" in line.upper():
                                        level = "ERROR"
                                    elif "WARNING" in line.upper() or "WARN" in line.upper():
                                        level = "WARNING"
                                    elif "DEBUG" in line.upper():
                                        level = "DEBUG"
                                    elif "🚀" in line or "✅" in line or "Starting" in line:
                                        level = "SUCCESS"
                                    
                                    logs.append(LogEntry(
                                        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                                        level=level,
                                        message=line,
                                        source="stdout"
                                    ))
                    except Exception as e:
                        logs.append(LogEntry(
                            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                            level="ERROR",
                            message=f"Error reading stdout log: {str(e)}",
                            source="system"
                        ))
                
                # Read stderr log file
                stderr_path = log_file_paths['stderr']
                if os.path.exists(stderr_path):
                    try:
                        with open(stderr_path, 'r') as f:
                            stderr_lines = f.readlines()[-lines//2:]  # Reserve half space for stderr
                            for line in stderr_lines:
                                line = line.strip()
                                if line:
                                    logs.append(LogEntry(
                                        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                                        level="ERROR",
                                        message=line,
                                        source="stderr"
                                    ))
                    except Exception as e:
                        logs.append(LogEntry(
                            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                            level="ERROR",
                            message=f"Error reading stderr log: {str(e)}",
                            source="system"
                        ))
            
            # Also add process status
            if project_id in self.processes:
                process = self.processes[project_id]
                if process.poll() is None:
                    logs.append(LogEntry(
                        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                        level="INFO",
                        message=f"Service is running with PID {process.pid}",
                        source="deployment"
                    ))
                else:
                    logs.append(LogEntry(
                        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                        level="ERROR",
                        message=f"Service process has stopped (exit code: {process.returncode})",
                        source="deployment"
                    ))
            
            return logs[-lines:]  # Return only the requested number of lines
            
        except Exception as e:
            return [LogEntry(
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                level="ERROR",
                message=f"Failed to get logs: {str(e)}",
                source="deployment"
            )]
    
    async def restart_service(self, project_id: str) -> bool:
        """Restart the deployed service"""
        try:
            # Get the current config
            if project_id not in self.deployed_services:
                return False
            
            config_data = self.deployed_services[project_id]["config"]
            config = DeploymentConfig(**config_data)
            
            # Stop and redeploy
            await self.stop_service(project_id)
            await asyncio.sleep(1)  # Brief pause
            result = await self.deploy_service(project_id, config)
            
            return result["status"] == "deployed"
            
        except Exception as e:
            print(f"Failed to restart service: {e}")
            return False
    
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except OSError:
            return False


class PortAllocator:
    """Manages port allocation for services"""
    
    def __init__(self, start_port: int = 3000, end_port: int = 3999):
        self.start_port = start_port
        self.end_port = end_port
        self.allocated_ports = set()
    
    def allocate(self) -> int:
        """Allocate a free port"""
        for port in range(self.start_port, self.end_port + 1):
            if port not in self.allocated_ports:
                self.allocated_ports.add(port)
                return port
        raise RuntimeError("No free ports available")
    
    def free(self, port: int):
        """Free an allocated port"""
        self.allocated_ports.discard(port)
    
    def is_allocated(self, port: int) -> bool:
        """Check if port is allocated"""
        return port in self.allocated_ports


# Global deployment manager instance
deployment_manager = SimpleDeploymentManager()

@router.post("/deploy/{project_id}")
async def deploy_service(project_id: str, config: DeploymentConfig):
    """Deploy the MCP service"""
    try:
        result = await deployment_manager.deploy_service(project_id, config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deploy/{project_id}/stop")
async def stop_service(project_id: str):
    """Stop the deployed service"""
    success = await deployment_manager.stop_service(project_id)
    if success:
        return {"message": "Service stopped successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to stop service")

@router.post("/deploy/{project_id}/restart")
async def restart_service(project_id: str):
    """Restart the deployed service"""
    success = await deployment_manager.restart_service(project_id)
    if success:
        return {"message": "Service restarted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to restart service")

@router.get("/deploy/{project_id}/status")
async def get_deployment_status(project_id: str):
    """Get deployment status"""
    try:
        status = await deployment_manager.get_service_status(project_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/deploy/{project_id}/logs")
async def get_service_logs(project_id: str, lines: int = 50):
    """Get service logs"""
    try:
        logs = await deployment_manager.get_service_logs(project_id, lines)
        return {"logs": [log.model_dump() for log in logs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/deploy/ports/available")
async def get_available_ports():
    """Get list of available ports"""
    allocated = list(deployment_manager.port_allocator.allocated_ports)
    available = [
        port for port in range(3000, 4000) 
        if port not in allocated
    ][:10]  # Return first 10 available ports
    
    return {
        "allocated_ports": allocated,
        "available_ports": available
    }

@router.get("/deploy/{project_id}/logs/raw")
async def get_service_logs_raw(project_id: str):
    """Get raw log file paths for debugging"""
    try:
        # Check if project exists
        project = await project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        logs_info = {
            "project_id": project_id,
            "logs_directory": str(settings.logs_dir / project_id),
            "log_files": []
        }
        
        # Check if deployment manager has log files for this project
        if hasattr(deployment_manager, 'log_files') and project_id in deployment_manager.log_files:
            log_file_paths = deployment_manager.log_files[project_id]
            for log_type, log_path in log_file_paths.items():
                file_exists = os.path.exists(log_path)
                file_size = os.path.getsize(log_path) if file_exists else 0
                logs_info["log_files"].append({
                    "type": log_type,
                    "path": log_path,
                    "exists": file_exists,
                    "size_bytes": file_size
                })
        
        # Check for any other log files in the project logs directory
        logs_dir = settings.logs_dir / project_id
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                logs_info["log_files"].append({
                    "type": "discovered",
                    "path": str(log_file),
                    "exists": True,
                    "size_bytes": log_file.stat().st_size
                })
        
        return logs_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/deploy/{project_id}/debug")
async def debug_deployment(project_id: str):
    """Debug deployment issues"""
    try:
        # Check if project exists
        project = await project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_path = Path(project.path)
        
        debug_info = {
            "project_id": project_id,
            "project_path": str(project_path),
            "project_exists": project_path.exists(),
            "project_status": project.status.value if hasattr(project.status, 'value') else str(project.status),
            "deployment_active": getattr(project, 'deployment_active', False),
            "service_port": getattr(project, 'service_port', None),
            "search_results": {}
        }
        
        # Check for main files
        search_paths = [
            project_path,
            project_path / "src",
            project_path / "server"
        ]
        
        main_files = ['server.py', 'main.py', 'app.py', '__main__.py']
        
        for search_path in search_paths:
            path_key = str(search_path.relative_to(project_path)) if search_path != project_path else "root"
            debug_info["search_results"][path_key] = {
                "exists": search_path.exists(),
                "files": []
            }
            
            if search_path.exists():
                try:
                    all_files = list(search_path.glob("*.py"))
                    debug_info["search_results"][path_key]["files"] = [f.name for f in all_files]
                    
                    # Check for main files specifically
                    found_main_files = []
                    for filename in main_files:
                        file_path = search_path / filename
                        if file_path.exists():
                            found_main_files.append(filename)
                    debug_info["search_results"][path_key]["main_files"] = found_main_files
                except Exception as e:
                    debug_info["search_results"][path_key]["error"] = str(e)
        
        # Check deployment manager state
        debug_info["deployment_manager"] = {
            "has_deployed_services": project_id in deployment_manager.deployed_services,
            "has_processes": project_id in deployment_manager.processes,
            "has_log_files": hasattr(deployment_manager, 'log_files') and project_id in deployment_manager.log_files,
            "has_log_handles": hasattr(deployment_manager, 'log_handles') and project_id in deployment_manager.log_handles
        }
        
        if project_id in deployment_manager.deployed_services:
            debug_info["deployment_info"] = deployment_manager.deployed_services[project_id]
        
        # Check logs directory
        logs_dir = settings.logs_dir / project_id
        debug_info["logs"] = {
            "logs_dir": str(logs_dir),
            "logs_dir_exists": logs_dir.exists(),
            "log_files": []
        }
        
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                debug_info["logs"]["log_files"].append({
                    "name": log_file.name,
                    "size": log_file.stat().st_size,
                    "path": str(log_file)
                })
        
        return debug_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 