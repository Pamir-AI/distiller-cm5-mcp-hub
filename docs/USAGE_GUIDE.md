# MCP-Server Development Platform Usage Guide

## Overview

The MCP-Server Development Platform is a comprehensive web application designed for rapid creation, debugging, and deployment of MCP-Server services on Raspberry Pi 5.

## Installation

### Quick Installation

1. **Clone or download the project to your Raspberry Pi 5**
2. **Navigate to the project directory**
3. **Run the installation script:**
   ```bash
   cd mcp_dev_platform
   chmod +x scripts/install.sh
   ./scripts/install.sh
   ```

### Manual Installation

1. **Install system dependencies:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install python3 python3-pip python3-venv git curl wget
   ```

2. **Install uv package manager:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source ~/.bashrc
   ```

3. **Install Python dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Create directories:**
   ```bash
   mkdir -p projects logs
   ```

5. **Install systemd service:**
   ```bash
   sudo cp config/systemd/mcp-dev-platform.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable mcp-dev-platform
   sudo systemctl start mcp-dev-platform
   ```

## Getting Started

### 1. Access the Platform

Open your web browser and navigate to:
```
http://[your-raspberry-pi-ip]:8000
```

### 2. Create Your First Project

1. **Click "New Project" in the project management panel**
2. **Enter project details:**
   - **Project Name**: `my-first-mcp-server`
   - **Description**: Optional description
   - **Python Version**: Select Python version (default: 3.11)
3. **Click "Create Project"**

### 3. Upload MCP Script

#### Option A: Drag & Drop
- Drag your `.py` files directly to the upload area
- Files are automatically uploaded and processed

#### Option B: Text Upload
- Enter filename (e.g., `server.py`)
- Paste your MCP script code
- Click "Upload Text"

#### Option C: File Browser
- Click the upload area to open file browser
- Select multiple files to upload

### 4. Install Dependencies

1. **Click "Install Dependencies"**
2. **The platform will:**
   - Detect `requirements.txt` or `pyproject.toml`
   - Install dependencies using `uv`
   - Update project status

### 5. Debug Your MCP Server

1. **Click "Start Debug" to begin debug session**
2. **Switch to the "Tools" tab**
3. **View discovered MCP tools**
4. **Test tools:**
   - Select a tool from dropdown
   - Enter parameters in JSON format
   - Click "Execute Tool"
   - View results in real-time

### 6. Deploy Your Service

1. **Switch to "Deployment" tab**
2. **Configure deployment:**
   - Service name
   - Port (default: 3000)
   - Auto-start on boot
   - Enable logging
3. **Click "Deploy Service"**
4. **Access your deployed service at the provided URL**

## Interface Overview

### Project Management Panel (Left Side)

- **Project Creation Form**: Create new MCP projects
- **File Upload Section**: Upload scripts and files
- **Project Actions**: Install dependencies, debug, deploy
- **Project List**: View and select existing projects

### Debug & Testing Area (Right Side)

#### Tools Tab
- **Available Tools**: List of discovered MCP tools
- **Tool Testing**: Execute tools with parameters
- **Results Display**: View execution results and timing

#### Resources Tab
- **MCP Resources**: View available resources (coming soon)

#### Logs Tab
- **Service Logs**: View real-time service logs
- **Log Controls**: Refresh and clear logs

#### Deployment Tab
- **Deployment Config**: Configure service deployment
- **Status Display**: View deployment status and access URL

## Sample MCP Script

Here's a simple MCP server script to get you started:

```python
#!/usr/bin/env python3
"""
Sample MCP Server
A simple example MCP server with basic tools
"""

import asyncio
import json
from typing import Any, Dict

class SimpleMCPServer:
    def __init__(self):
        self.name = "Simple MCP Server"
        self.version = "1.0.0"
        
    async def list_tools(self) -> list:
        """List available tools"""
        return [
            {
                "name": "echo",
                "description": "Echo back the input message",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo back"
                        }
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "add_numbers",
                "description": "Add two numbers together",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            }
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool"""
        if name == "echo":
            return {"result": f"Echo: {arguments.get('message', '')}"}
        
        elif name == "add_numbers":
            a = arguments.get('a', 0)
            b = arguments.get('b', 0)
            return {"result": a + b, "operation": f"{a} + {b}"}
        
        else:
            raise ValueError(f"Unknown tool: {name}")

async def main():
    server = SimpleMCPServer()
    print(f"Starting {server.name} v{server.version}")
    
    # Simple test
    tools = await server.list_tools()
    print(f"Available tools: {[tool['name'] for tool in tools]}")
    
    # Test echo tool
    result = await server.call_tool("echo", {"message": "Hello MCP!"})
    print(f"Echo test: {result}")
    
    # Test add_numbers tool
    result = await server.call_tool("add_numbers", {"a": 5, "b": 3})
    print(f"Add test: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

Save this as `server.py` and upload it to your project.

## Workflow Examples

### Example 1: Simple Calculator MCP

1. **Create project**: `calculator-mcp`
2. **Upload script**: Calculator with add, subtract, multiply, divide tools
3. **Test tools**: Use debug interface to test calculations
4. **Deploy**: Make available on network

### Example 2: File Management MCP

1. **Create project**: `file-manager-mcp`
2. **Upload script**: File operations (list, read, write, delete)
3. **Install deps**: File handling libraries
4. **Debug**: Test file operations safely
5. **Deploy**: Production file management service

### Example 3: API Integration MCP

1. **Create project**: `api-integration-mcp`
2. **Upload script**: API client with multiple endpoints
3. **Add requirements**: `httpx`, `pydantic`
4. **Debug**: Test API calls and responses
5. **Deploy**: Service with network access

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
sudo systemctl status mcp-dev-platform

# View logs
sudo journalctl -u mcp-dev-platform -f

# Common fixes
sudo systemctl restart mcp-dev-platform
```

#### Project Creation Fails
- Ensure project name is unique
- Check available disk space
- Verify uv is installed correctly

#### Debug Session Issues
- Ensure project has MCP script uploaded
- Check if dependencies are installed
- Verify script syntax

#### Deployment Problems
- Check port availability
- Verify systemd permissions
- Ensure service script is valid

### Log Locations

- **Platform logs**: `journalctl -u mcp-dev-platform`
- **Project logs**: `./logs/`
- **Service logs**: Individual service systemd logs

### Configuration

Edit `.env` file to customize:

```bash
# Server settings
HOST=0.0.0.0
PORT=8000

# Debug settings
DEBUG=false

# MCP settings
MCP_INSPECTOR_ENABLED=true
MCP_DEFAULT_PORT=3000

# Security settings
MAX_FILE_SIZE_MB=10
```

## Advanced Features

### Multiple Project Management
- Run multiple MCP services simultaneously
- Automatic port allocation
- Independent debugging sessions

### Real-time Monitoring
- WebSocket-based real-time updates
- Live log streaming
- Service health monitoring

### Security Features
- File type validation
- Size limits
- Sandboxed execution
- Process isolation

## API Reference

### REST Endpoints

- `POST /api/projects` - Create project
- `GET /api/projects` - List projects
- `POST /api/projects/{id}/upload` - Upload files
- `POST /api/projects/{id}/install` - Install dependencies
- `POST /api/debug/{id}/start` - Start debug session
- `POST /api/deploy/{id}` - Deploy service
- `GET /api/deploy/{id}/status` - Get deployment status

### WebSocket Endpoints

- `/api/debug/{id}/ws` - Real-time debug communication

## Best Practices

### Project Organization
```
my-mcp-project/
├── server.py          # Main MCP server
├── requirements.txt   # Dependencies
├── config.json       # Configuration
├── tools/            # Tool implementations
└── tests/            # Test files
```

### Security
- Use specific dependency versions
- Validate all inputs
- Limit resource usage
- Monitor service health

### Performance
- Use async/await for I/O operations
- Implement proper error handling
- Cache frequently used data
- Monitor memory usage

## Support

### Getting Help
- Check the troubleshooting section
- Review logs for error messages
- Ensure all dependencies are installed
- Verify network connectivity

### Contributing
- Report bugs via GitHub issues
- Submit feature requests
- Contribute documentation improvements
- Share example MCP scripts

### Resources
- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [uv Package Manager](https://github.com/astral-sh/uv)
- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/) 