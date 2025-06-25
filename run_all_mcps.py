#!/usr/bin/env python3
"""
MCP Hub Manager - Manages multiple MCP services based on configuration
"""
import json
import subprocess
import signal
import sys
import os
import time
import logging
from threading import Thread, Event
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MCPHub')

class MCPManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = True
        self.shutdown_event = Event()
        self.base_dir = "/opt/distiller-cm5-mcp-hub/projects"
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
    
    def load_config(self) -> Dict[str, Any]:
        """Load MCP configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            raise
    
    def start_mcp(self, name: str, config: Dict[str, Any]) -> bool:
        """Start a single MCP service"""
        try:
            project_dir = os.path.join(self.base_dir, config['project_dir'])
            
            if not os.path.exists(project_dir):
                logger.error(f"Project directory not found: {project_dir}")
                return False
            
            if not os.path.exists(os.path.join(project_dir, 'server.py')):
                logger.error(f"server.py not found in {project_dir}")
                return False
            
            port = config['port']
            host = config.get('host', 'localhost')
            cmd = ["uv", "run", "python", "server.py", "--transport", "sse", "--host", host, "--port", str(port)]
            
            logger.info(f"Starting {name} ({config.get('description', 'MCP Service')})")
            logger.info(f"  Directory: {project_dir}")
            logger.info(f"  Host: {host}")
            logger.info(f"  Port: {port}")
            logger.info(f"  Command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes[name] = process
            logger.info(f"Started {name} successfully (PID: {process.pid})")
            
            # Start a thread to handle this process's output
            Thread(target=self._handle_process_output, args=(name, process), daemon=True).start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {name}: {e}")
            return False
    
    def _handle_process_output(self, name: str, process: subprocess.Popen):
        """Handle output from a specific MCP process"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    logger.info(f"[{name}] {line.strip()}")
        except Exception as e:
            logger.error(f"Error reading output from {name}: {e}")
    
    def monitor_processes(self):
        """Monitor all processes and restart them if they die"""
        logger.info("Starting process monitor")
        
        while self.running and not self.shutdown_event.is_set():
            try:
                # Check each process
                for name, process in list(self.processes.items()):
                    if process.poll() is not None:  # Process has terminated
                        exit_code = process.returncode
                        logger.warning(f"MCP {name} terminated with exit code {exit_code}")
                        
                        if self.running:  # Only restart if we're not shutting down
                            logger.info(f"Restarting {name}...")
                            
                            # Remove the dead process
                            del self.processes[name]
                            
                            # Reload config and restart
                            try:
                                config = self.load_config()
                                mcp_config = config.get(name)
                                
                                if mcp_config and mcp_config.get('enabled', False):
                                    time.sleep(2)  # Brief delay before restart
                                    self.start_mcp(name, mcp_config)
                                else:
                                    logger.info(f"MCP {name} is disabled in config, not restarting")
                            except Exception as e:
                                logger.error(f"Failed to restart {name}: {e}")
                
                # Wait before next check
                self.shutdown_event.wait(5)
                
            except Exception as e:
                logger.error(f"Error in process monitor: {e}")
                time.sleep(5)
        
        logger.info("Process monitor stopped")
    
    def start_all(self):
        """Start all enabled MCP services"""
        try:
            config = self.load_config()
            started_count = 0
            
            for name, mcp_config in config.items():
                if mcp_config.get('enabled', False):
                    if self.start_mcp(name, mcp_config):
                        started_count += 1
                    else:
                        logger.error(f"Failed to start {name}")
                else:
                    logger.info(f"MCP {name} is disabled, skipping")
            
            if started_count == 0:
                logger.warning("No MCP services were started")
                return False
            
            logger.info(f"Started {started_count} MCP service(s)")
            
            # Start the process monitor
            monitor_thread = Thread(target=self.monitor_processes, daemon=True)
            monitor_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start MCP services: {e}")
            return False
    
    def shutdown(self):
        """Shutdown all MCP services gracefully"""
        logger.info("Shutting down MCP Hub...")
        self.running = False
        self.shutdown_event.set()
        
        # Terminate all processes
        for name, process in self.processes.items():
            try:
                logger.info(f"Stopping {name} (PID: {process.pid})")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                    logger.info(f"Stopped {name} gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing {name}")
                    process.kill()
                    process.wait()
                    
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
        
        logger.info("MCP Hub shutdown complete")
    
    def run(self):
        """Main run loop"""
        logger.info("Starting MCP Hub Manager")
        
        if not self.start_all():
            logger.error("Failed to start MCP services")
            sys.exit(1)
        
        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.shutdown()

def main():
    config_path = "/opt/distiller-cm5-mcp-hub/mcp_config.json"
    
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    manager = MCPManager(config_path)
    manager.run()

if __name__ == "__main__":
    main() 