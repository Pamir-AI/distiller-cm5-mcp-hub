# How to Write MCP (Model Context Protocol) Servers

This guide demonstrates how to create MCP servers using the patterns established in our Pi Camera MCP Server implementation. It's designed to help AI coding assistants understand and replicate effective MCP server patterns.

## Table of Contents
1. [MCP Overview](#mcp-overview)
2. [Project Structure](#project-structure)
3. [Standard Project Template](#standard-project-template)
4. [UV Setup and Configuration](#uv-setup-and-configuration)
5. [Core Implementation Patterns](#core-implementation-patterns)
6. [Tool Design Best Practices](#tool-design-best-practices)
7. [Error Handling Strategies](#error-handling-strategies)
8. [Transport Configuration](#transport-configuration)
9. [Testing and Debugging](#testing-and-debugging)
10. [Complete Example](#complete-example)

## MCP Overview

Model Context Protocol (MCP) enables AI assistants to interact with external systems through standardized tools. Key concepts:

- **Server**: Provides tools and resources to clients
- **Client**: AI assistant that uses MCP tools
- **Tools**: Functions that clients can call
- **Transport**: Communication layer (stdio, SSE, HTTP)

## Project Structure

```
project/
├── server.py          # MCP server implementation
├── [domain].py        # Domain-specific logic (e.g., camera.py)
├── requirements.txt   # Dependencies
└── README.md         # Usage instructions
```

**Key Principle**: Separate MCP server logic from domain logic for maintainability.

## Standard Project Template

Use this template to quickly bootstrap new MCP server projects:

### File Structure
```
your-mcp-project/
├── server.py              # Main MCP server implementation
├── domain.py              # Domain-specific logic (rename appropriately)
├── pyproject.toml         # UV/Python project configuration
├── requirements.txt       # Legacy pip requirements (optional)
├── README.md             # Project documentation
└── tests/                # Test directory (optional)
    └── test_domain.py
```

### pyproject.toml Template
```toml
[project]
name = "distiller-cm5-your-service-mcp"
version = "1.0.0"
description = "Your Service MCP Server - Brief description of functionality"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.1.2",
    # Add your specific dependencies here
    # "distiller-cm5-sdk",  # If using custom wheel
]

[[project.authors]]
name = "Your Name"
email = "your.email@example.com"

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
]

[project.scripts]
distiller-cm5-your-service-mcp = "server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["."]

# Uncomment if using custom wheels
# [tool.uv.sources]
# your-custom-package = { path = "/path/to/your/wheel.whl" }

[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers"
testpaths = ["tests"]
asyncio_mode = "auto"
```

### server.py Template
```python
#!/usr/bin/env python3
"""
Your Service MCP Server

Brief description of what this server provides.
"""

import argparse
import sys
from mcp.server.fastmcp import FastMCP

# Import your domain logic
try:
    from domain import YourDomainClass
    domain = YourDomainClass()
except ImportError as e:
    print(f"Warning: Failed to import domain logic: {e}")
    domain = None

# Create MCP server
mcp = FastMCP("Your Service MCP Server")

@mcp.tool()
async def example_tool(param: str) -> str:
    """
    Example tool implementation.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
    """
    try:
        if domain is None:
            return "Service not available: domain logic not loaded"
        
        result = domain.example_method(param)
        return f"Result: {result}"
    except Exception as e:
        raise ValueError(f"Tool failed: {str(e)}")

@mcp.tool()
async def get_status() -> str:
    """
    Get service status and health information.
    
    Returns:
        Service status information
    """
    try:
        if domain is None:
            return "Status: Service not available - domain logic not loaded"
        
        status = domain.get_status()
        return f"Status: {status}"
    except Exception as e:
        return f"Status: Error - {str(e)}"

def main():
    """Main entry point with transport configuration."""
    parser = argparse.ArgumentParser(description='Your Service MCP Server')
    parser.add_argument('--transport', 
                       choices=['stdio', 'sse', 'streamable-http'], 
                       default='stdio',
                       help='Transport protocol to use')
    parser.add_argument('--host', default='localhost',
                       help='Host for SSE/HTTP transport')
    parser.add_argument('--port', type=int, default=3000,
                       help='Port for SSE/HTTP transport')
    
    args = parser.parse_args()
    
    try:
        if args.transport == 'stdio':
            mcp.run()
        elif args.transport == 'sse':
            mcp.settings.host = args.host
            mcp.settings.port = args.port
            mcp.run(transport="sse")
        elif args.transport == 'streamable-http':
            mcp.settings.host = args.host
            mcp.settings.port = args.port
            mcp.run(transport="streamable-http")
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### domain.py Template
```python
"""
Domain-specific logic for Your Service.

Keep all hardware/service-specific code here, separate from MCP logic.
"""

import logging

logger = logging.getLogger(__name__)

class YourDomainClass:
    """Domain logic for your service."""
    
    def __init__(self):
        """Initialize the domain service."""
        self.initialized = False
        try:
            self._initialize()
            self.initialized = True
            logger.info("Domain service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize domain service: {e}")
            # Don't raise - allow graceful degradation
    
    def _initialize(self):
        """Initialize hardware/service connections."""
        # Add your initialization logic here
        pass
    
    def example_method(self, param: str) -> str:
        """Example domain method."""
        if not self.initialized:
            raise RuntimeError("Service not initialized")
        
        # Your domain logic here
        return f"Processed: {param}"
    
    def get_status(self) -> str:
        """Get current service status."""
        if not self.initialized:
            return "Not initialized"
        
        # Add your status checking logic here
        return "Service running normally"
    
    def cleanup(self):
        """Clean up resources."""
        try:
            # Add cleanup logic here
            logger.info("Domain service cleaned up")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
```

### README.md Template
```markdown
# Your Service MCP Server

Brief description of what this MCP server provides.

## Features

- Feature 1: Description
- Feature 2: Description
- Status Monitoring: Health checks and diagnostics

## Installation

1. Clone or copy this project
2. Install dependencies using UV:
   ```bash
   uv sync
   ```

## Usage

### Run the MCP Server

```bash
# Using UV
uv run distiller-cm5-your-service-mcp

# Or directly
uv run python server.py
```

### Alternative Transport Methods

```bash
# SSE transport
uv run python server.py --transport sse --host localhost --port 3000

# HTTP transport  
uv run python server.py --transport streamable-http --host localhost --port 3000
```

## Available Tools

### 1. `example_tool`
Description of what this tool does.

**Parameters:**
- `param` (str): Description of parameter

**Returns:** Description of return value

### 2. `get_status`
Get service status and health information.

**Parameters:** None

**Returns:** Service status information

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy .
```

## Troubleshooting

### Common Issues

1. **Service not available**
   - Check dependencies are installed
   - Verify hardware/service connections
   - Check logs for initialization errors

2. **Tool failures**
   - Use `get_status` tool to check service health
   - Verify parameters are correct
   - Check system permissions

## Dependencies

- Python 3.11+
- MCP library
- Your specific dependencies
```

## UV Setup and Configuration

UV is the recommended tool for Python dependency management in MCP projects. Here's how to set it up:

### 1. Installing UV

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

### 2. Project Initialization

```bash
# Create new project
mkdir your-mcp-project
cd your-mcp-project

# Initialize with uv (creates pyproject.toml)
uv init

# Or use the template pyproject.toml from above
```

### 3. Dependency Management

```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --dev

# Add new dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Update dependencies
uv sync --upgrade
```

### 4. Running Commands

```bash
# Run your server
uv run python server.py

# Run with entry point (if configured)
uv run distiller-cm5-your-service-mcp

# Run tests
uv run pytest

# Run any command in the virtual environment
uv run your-command
```

### 5. Custom Wheel Dependencies

For projects that depend on custom wheels (like distiller-cm5-sdk):

```toml
[tool.uv.sources]
your-custom-package = { path = "/absolute/path/to/wheel.whl" }
```

### 6. Virtual Environment

```bash
# UV automatically creates and manages virtual environments
# Located in .venv/ directory

# Activate manually (rarely needed)
source .venv/bin/activate

# Deactivate
deactivate
```

### 7. Common UV Commands

| Command | Purpose |
|---------|---------|
| `uv sync` | Install/update dependencies |
| `uv add package` | Add dependency |
| `uv remove package` | Remove dependency |
| `uv run command` | Run command in venv |
| `uv pip list` | List installed packages |
| `uv pip freeze` | Export requirements |

### 8. Best Practices

1. **Always use `uv run`** instead of activating venv manually
2. **Pin Python version** in `requires-python` field
3. **Use dev dependencies** for development tools
4. **Commit `pyproject.toml`** but not `.venv/`
5. **Use `[tool.uv.sources]`** for local/custom packages

### 9. Migration from pip

If you have an existing `requirements.txt`:

```bash
# Install from requirements.txt
uv pip install -r requirements.txt

# Generate pyproject.toml dependencies
uv pip freeze | uv add -
```

This UV setup ensures consistent, reproducible builds across different environments and simplifies dependency management for MCP projects.

## Core Implementation Patterns

### 1. FastMCP Setup

```python
#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP, Image
import asyncio

# Create MCP server instance
mcp = FastMCP("Your Service Name")
```

### 2. Tool Definition Pattern

```python
@mcp.tool()
async def tool_name(param1: str, param2: int = 10) -> str:
    """
    Clear, descriptive docstring explaining what the tool does.
    
    Args:
        param1: Description of parameter
        param2: Optional parameter with default
        
    Returns:
        Description of return value
    """
    try:
        # Tool implementation
        result = your_domain_logic(param1, param2)
        return result
    except Exception as e:
        raise ValueError(f"Tool failed: {str(e)}")
```

### 3. Domain Logic Separation

**server.py** (MCP layer):
```python
@mcp.tool()
async def get_camera_snapshot() -> Image:
    """Capture a snapshot from the Pi Camera."""
    try:
        img_bytes = camera.capture_snapshot()  # Domain logic call
        return Image(data=img_bytes, format="jpeg")
    except Exception as e:
        raise ValueError(f"Failed to capture snapshot: {str(e)}")
```

**camera.py** (Domain layer):
```python
def capture_snapshot() -> bytes:
    """Domain-specific implementation."""
    # Hardware interaction logic here
    return img_bytes
```

## Tool Design Best Practices

### 1. Return Type Patterns

| Data Type | Return Pattern | Example |
|-----------|---------------|---------|
| Text | `str` | Status messages, reports |
| Images | `Image(data=bytes, format="jpeg")` | Photos, charts |
| Structured Data | `str` (formatted) | JSON, tables, lists |
| Binary Data | `Image` or base64 `str` | Files, media |

### 2. Parameter Design

```python
# Good: Clear types and defaults
async def process_image(
    quality: int = 95,
    format: str = "jpeg",
    resize_width: int = None
) -> Image:

# Avoid: Unclear parameters
async def process(opts: dict) -> str:
```

### 3. Docstring Standards

```python
@mcp.tool()
async def example_tool(param: str) -> str:
    """
    One-line summary of what the tool does.
    
    Longer description if needed. Explain:
    - What the tool accomplishes
    - When to use it
    - Any important limitations
    
    Args:
        param: Clear description of the parameter
        
    Returns:
        Description of return value and format
    """
```

## Error Handling Strategies

### 1. Graceful Degradation

```python
def capture_snapshot() -> bytes:
    """Always return something useful, even if hardware fails."""
    try:
        # Try real hardware
        return real_camera_capture()
    except Exception as e:
        print(f"Camera failed: {e}, generating test image...")
        return generate_test_image()  # Fallback
```

### 2. Informative Error Messages

```python
@mcp.tool()
async def get_status() -> str:
    """Return detailed status including error context."""
    try:
        return check_hardware_status()
    except ImportError:
        return "Module not installed. Install with: pip install required-module"
    except PermissionError:
        return "Permission denied. Check hardware access permissions."
    except Exception as e:
        return f"Unexpected error: {str(e)}. Check system logs."
```

### 3. Resource Cleanup

```python
def capture_snapshot() -> bytes:
    camera = None
    try:
        camera = initialize_camera()
        return camera.capture()
    except Exception as e:
        raise
    finally:
        # Always cleanup resources
        if camera is not None:
            camera.close()
```

## Transport Configuration

### 1. Multi-Transport Support

```python
def main():
    parser = argparse.ArgumentParser(description='Your MCP Server')
    parser.add_argument('--transport', 
                       choices=['stdio', 'sse', 'streamable-http'], 
                       default='stdio')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=3000)
    
    args = parser.parse_args()
    
    if args.transport == 'stdio':
        mcp.run()
    elif args.transport == 'sse':
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="sse")
    # ... other transports
```

### 2. Transport Use Cases

- **stdio**: Local development, direct integration
- **sse**: Web applications, real-time updates
- **streamable-http**: API integration, webhooks

## Testing and Debugging

### 1. Local Testing

```python
if __name__ == "__main__":
    # Allow running domain logic directly for testing
    result = your_domain_function()
    print(f"Test result: {result}")
```

### 2. Debug Output

```python
@mcp.tool()
async def debug_tool() -> str:
    """Tool that provides system debugging information."""
    debug_info = {
        "system": platform.system(),
        "python_version": sys.version,
        "dependencies": check_dependencies(),
        "hardware": check_hardware_status()
    }
    return json.dumps(debug_info, indent=2)
```

## Complete Example

Here's a minimal but complete MCP server:

```python
#!/usr/bin/env python3
"""
Example MCP Server
Demonstrates core patterns for MCP server implementation.
"""

import argparse
from mcp.server.fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("Example MCP Server")

@mcp.tool()
async def echo(message: str) -> str:
    """
    Echo a message back to the client.
    
    Args:
        message: The message to echo
        
    Returns:
        The echoed message with timestamp
    """
    try:
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        return f"[{timestamp}] Echo: {message}"
    except Exception as e:
        raise ValueError(f"Echo failed: {str(e)}")

@mcp.tool()
async def get_system_info() -> str:
    """
    Get basic system information.
    
    Returns:
        System information as formatted text
    """
    try:
        import platform
        import sys
        
        info = f"""System Information:
- Platform: {platform.system()}
- Python: {sys.version}
- Architecture: {platform.machine()}
"""
        return info
    except Exception as e:
        return f"Failed to get system info: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='Example MCP Server')
    parser.add_argument('--transport', default='stdio',
                       choices=['stdio', 'sse', 'streamable-http'])
    args = parser.parse_args()
    
    if args.transport == 'stdio':
        mcp.run()
    # Add other transports as needed

if __name__ == "__main__":
    main()
```

## Key Takeaways

1. **Separation of Concerns**: Keep MCP logic separate from domain logic
2. **Error Handling**: Always provide graceful fallbacks and clear error messages
3. **Documentation**: Write clear docstrings for every tool
4. **Resource Management**: Always clean up resources in finally blocks
5. **Flexibility**: Support multiple transport protocols
6. **Testing**: Make domain logic testable independently
7. **User Experience**: Return meaningful, formatted responses

This pattern scales from simple utilities to complex integrations while maintaining reliability and usability. 