# Pi Camera MCP Server

A Model Context Protocol (MCP) server that provides camera snapshot and status tools for Raspberry Pi Camera Module.

## Features

- **Camera Snapshot**: Capture high-quality images from the Pi Camera
- **Camera Status**: Check camera connection and configuration
- **FastAPI Integration**: RESTful API endpoints for camera operations
- **MCP Tools**: Standardized tools for AI model integration

## Requirements

- Python >= 3.11
- Raspberry Pi with Camera Module
- picamera2 library
- MCP compatible client

## Installation

```bash
# Install using uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

## Usage

### As MCP Server

```bash
distiller-cm5-cam-mcp
```

### API Endpoints

The server also provides FastAPI endpoints:

- `GET /snapshot` - Capture a camera snapshot
- `GET /status` - Get camera status

## Development

```bash
# Install development dependencies
uv sync --group dev

# Run tests
pytest

# Format code
black .
isort .

# Type checking
mypy .
```

## License

This project is part of the distiller-cm5-mcp-hub ecosystem. 