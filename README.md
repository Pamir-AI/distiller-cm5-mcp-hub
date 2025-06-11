# Distiller MCP Hub

A comprehensive Model Context Protocol (MCP) server hub with a shared transport layer that supports multiple transport protocols (stdio, HTTP, SSE). This project provides a reusable MCP transport implementation and includes several example MCP servers.

## Overview

The MCP Hub consists of:
- **Shared Transport Layer** (`mcp_transport.py`) - A standalone transport implementation supporting stdio, HTTP, and Server-Sent Events (SSE), in case you using core mcp, if you are using fastmcp (like what we showed in the /projects) dont worry bout this
- **Example MCP Servers** - Ready-to-use implementations for hardware control and AI interactions
- **Development Tools** - Utilities for testing and validation

## Transport Protocols

### stdio Transport
Traditional MCP protocol using standard input/output streams.
```bash
uv run python server.py --transport stdio
```

### HTTP Transport
RESTful HTTP API for MCP operations.
```bash
uv run python server.py --transport streamable-http --port 8001
```

### SSE Transport (Server-Sent Events)
Real-time streaming protocol for web applications.
```bash
uv run python server.py --transport sse --port 8001
```

## Included MCP Servers

### Speaker MCP (`projects/speaker-mcp/`)
Text-to-speech functionality using Piper TTS library.

**Features:**
- Convert text to speech with adjustable volume
- Save audio files or play directly
- List and manage generated TTS files
- Support for multiple TTS models
- Audio file cleanup utilities

**Usage:**
```bash
cd projects/speaker-mcp
uv run python server.py --transport sse --port 8001
```

### Camera MCP (`projects/camera-mcp/`)
Camera control and image capture functionality.

### Mic MCP (`projects/mic-mcp/`)
Microphone control and audio recording functionality.

## Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd distiller-cm5-mcp-hub
```

2. **Install dependencies:**
```bash
uv sync
```

3. **Install individual project dependencies:**
```bash
cd projects/speaker-mcp
uv sync
```

## Quick Start

1. **Run a basic MCP server with SSE transport:**
```bash
cd projects/speaker-mcp
uv run python server.py --transport sse --port 8001
```

2. **Access the API documentation:**
Open `http://localhost:8001/docs` in your browser

3. **Health check:**
```bash
curl http://localhost:8001/health
```

4. **Test MCP endpoint:**
```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "id": 1}'
```

## Development

### Creating a New MCP Server

1. **Create a new project directory:**
```bash
mkdir projects/my-mcp
cd projects/my-mcp
```

2. **Import and use the transport layer:**
```python
#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from mcp_transport import MCPTransport

# Create transport instance
transport = MCPTransport(
    server_name="My MCP Server",
    server_version="1.0.0",
    server_description="Custom MCP implementation"
)

# Set your handlers
transport.set_handlers(
    list_tools=my_list_tools_handler,
    call_tool=my_call_tool_handler
)

# Run with arguments
if __name__ == "__main__":
    parser = transport.create_argument_parser("My MCP Server")
    args = parser.parse_args()
    
    import asyncio
    asyncio.run(transport.run_server(args.transport, args.host, args.port))
```

3. **Implement your MCP handlers:**
```python
async def my_list_tools_handler():
    # Return list of available tools
    pass

async def my_call_tool_handler(tool_name: str, arguments: dict):
    # Implement tool execution logic
    pass
```

### Testing

Run the sanity check to validate your MCP server:
```bash
python sanity_check.py
```

## API Endpoints

When running with HTTP or SSE transport:

- `GET /` - Server information
- `POST /` - MCP JSON-RPC endpoint
- `GET /sse` - SSE connection endpoint
- `POST /sse` - SSE message endpoint  
- `POST /mcp` - Alternative MCP endpoint
- `GET /health` - Health check
- `GET /docs` - API documentation (FastAPI)

## Dependencies

### Core Dependencies
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `websockets` - WebSocket support
- `httpx` - HTTP client
- `psutil` - System monitoring

### Development Dependencies
- `pytest` - Testing framework
- `black` - Code formatting
- `isort` - Import sorting

## Configuration

The transport layer can be configured through environment variables:

- `MCP_HOST` - Server host (default: localhost)
- `MCP_PORT` - Server port (default: 3000)
- `MCP_TRANSPORT` - Transport type (stdio, sse, streamable-http)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Architecture

```
distiller-cm5-mcp-hub/
├── mcp_transport.py          # Shared transport layer
├── sanity_check.py          # Validation utilities
├── projects/                # MCP server implementations
│   ├── speaker-mcp/        # Text-to-speech server
│   ├── camera-mcp/         # Camera control server
│   └── mic-mcp/            # Microphone server
└── requirements.txt         # Python dependencies
```

## License

[Add your license information here]

## Support

For questions or issues, please [create an issue](link-to-issues) or contact the development team. 