# Distiller MCP Hub

A Model Context Protocol (MCP) server hub for the Distiller CM5 platform, providing hardware control capabilities for camera, microphone, and speaker systems through MCP services.

## Overview

The Distiller MCP Hub is a system that:
- **Manages multiple MCP services** (camera, microphone, speaker) through a centralized configuration
- **Integrates with the Distiller CM5 SDK** for hardware-specific AI functionality
- **Provides a systemd service** for production deployment with automatic startup and process monitoring
- **Uses uv workspace management** for clean dependency isolation between services
- **Supports multiple transport protocols** (stdio, SSE, HTTP) for flexible integration

## Architecture

```
distiller-mcp-hub/
├── run_all_mcps.py           # Main service orchestrator
├── mcp_config.json           # Service configuration
├── mcp.service               # systemd service definition
├── venv_wrapper.sh           # Virtual environment management
├── manage_mcp_service.sh     # Service management utilities
├── projects/                 # Individual MCP services (uv workspace)
│   ├── camera-mcp/          # Camera snapshot and status
│   ├── mic-mcp/             # Audio recording and transcription
│   └── speaker-mcp/         # Text-to-speech functionality
└── pyproject.toml           # Hub-level dependencies
```

## Prerequisites

### System Requirements
- **ARM64 Linux system** (Raspberry Pi CM5 or compatible)
- **Python 3.11+** (automatically managed)
- **uv package manager** (automatically installed)
- **Distiller CM5 SDK** (must be installed separately)

### Required Dependencies

The MCP Hub depends on the **Distiller CM5 SDK** which must be installed first:

```bash
# Install the Distiller CM5 SDK
git clone https://github.com/Pamir-AI/distiller-cm5-sdk.git
cd distiller-cm5-sdk
./build.sh && ./build-deb.sh
sudo dpkg -i dist/distiller-cm5-sdk_*_arm64.deb
sudo apt-get install -f
```

### Environment Variables

The MCP Hub automatically configures the following environment variables for proper SDK integration:

- `PYTHONPATH=/opt/distiller-cm5-sdk:/opt/distiller-cm5-sdk/src` - Python module search path
- `LD_LIBRARY_PATH=/opt/distiller-cm5-sdk/lib` - Native library search path

These are automatically set by:
1. **systemd service** - Environment variables in `mcp.service`
2. **venv_wrapper.sh** - Sources SDK activation script when available
3. **sdk_imports.py** - Programmatic environment setup in each MCP service

## Installation

### 1. Install via Debian Package (Recommended)

```bash
# Clone and build the MCP Hub
git clone https://github.com/Pamir-AI/distiller-mcp-hub.git
cd distiller-mcp-hub
chmod +x build-deb.sh
./build-deb.sh

# Install the package
sudo dpkg -i dist/distiller-mcp-hub_*_arm64.deb
sudo apt-get install -f

# The package installs to /opt/distiller-mcp-hub/
```

The installation process will:
- **Detect SDK availability** and configure environment automatically
- **Test SDK integration** during installation
- **Create isolated virtual environments** for each MCP service
- **Set up systemd service** with proper environment variables
- **Configure hardware permissions** (audio group, device access)

### 2. Development Installation

```bash
# Clone the repository
git clone https://github.com/Pamir-AI/distiller-mcp-hub.git
cd distiller-mcp-hub

# Install dependencies using uv
uv sync

# Install project dependencies in workspace
cd projects/camera-mcp && uv sync
cd ../mic-mcp && uv sync  
cd ../speaker-mcp && uv sync
```

## Configuration

### MCP Service Configuration

Edit `/opt/distiller-mcp-hub/mcp_config.json` to control which services run:

```json
{
  "camera": {
    "enabled": true,
    "port": 8001,
    "host": "0.0.0.0", 
    "project_dir": "camera-mcp",
    "description": "Camera MCP Service"
  },
  "mic": {
    "enabled": true,
    "port": 8002,
    "host": "0.0.0.0",
    "project_dir": "mic-mcp", 
    "description": "Microphone MCP Service"
  },
  "speaker": {
    "enabled": true,
    "port": 8003,
    "host": "0.0.0.0",
    "project_dir": "speaker-mcp",
    "description": "Speaker MCP Service"
  }
}
```

### Service Endpoints

When running, the services are available at:
- **Camera MCP**: `http://0.0.0.0:8001/sse` (SSE), `http://0.0.0.0:8001/health` (Health)
- **Microphone MCP**: `http://0.0.0.0:8002/sse` (SSE), `http://0.0.0.0:8002/health` (Health)  
- **Speaker MCP**: `http://0.0.0.0:8003/sse` (SSE), `http://0.0.0.0:8003/health` (Health)

## Usage

### Production Deployment (Recommended)

```bash
# Install and enable the systemd service
cd /opt/distiller-mcp-hub
./manage_mcp_service.sh install
./manage_mcp_service.sh enable
./manage_mcp_service.sh start

# Check service status
./manage_mcp_service.sh status

# View logs
./manage_mcp_service.sh logs
```

### Manual Execution

```bash
# Start all configured MCP services
cd /opt/distiller-mcp-hub
./venv_wrapper.sh run_all_mcps.py

# Or run individual services
./venv_wrapper.sh --project camera-mcp server.py --transport sse --port 8001
./venv_wrapper.sh --project mic-mcp server.py --transport sse --port 8002
./venv_wrapper.sh --project speaker-mcp server.py --transport sse --port 8003
```

### Development Mode

```bash
# Run with stdio transport (for MCP client development)
cd projects/camera-mcp
uv run python server.py --transport stdio

# Run with SSE transport (for web integration)
cd projects/camera-mcp
uv run python server.py --transport sse --host localhost --port 8001
```

## MCP Services

### Camera MCP (`projects/camera-mcp/`)

Provides camera control and image capture functionality.

**Tools:**
- `get_camera_snapshot()` - Capture and return base64-encoded JPEG image
- `get_camera_status()` - Check camera availability and configuration

**Dependencies:**
- `picamera2` - Raspberry Pi camera interface
- `pillow` - Image processing

### Microphone MCP (`projects/mic-mcp/`)

Provides audio recording and transcription using the Distiller CM5 SDK.

**Tools:**
- `record_for_seconds(duration)` - Record audio for specified duration
- `list_recordings()` - List all available recordings
- `get_recording(recording_id)` - Get recording details and file path
- `get_transcription(recording_id)` - Transcribe audio using Parakeet ASR
- `stop_current_recording()` - Stop active recording
- `get_system_status()` - Check microphone and transcription system status

**Dependencies:**
- `distiller-cm5-sdk.parakeet` - Parakeet ASR for transcription
- `sounddevice` - Audio recording
- `wave` - Audio file handling

**Hardware Mode vs Simulation Mode:**
- **Hardware Mode**: Uses Parakeet ASR for real transcription when SDK is available
- **Simulation Mode**: Generates mock audio and dummy transcriptions for testing

### Speaker MCP (`projects/speaker-mcp/`)

Provides text-to-speech functionality using the Distiller CM5 SDK.

**Tools:**
- `text_to_speech(text, volume)` - Convert text to speech with volume control
- `get_speaker_status()` - Check TTS system status and model information

**Dependencies:**
- `distiller-cm5-sdk.piper` - Piper TTS for text-to-speech
- `sounddevice` - Audio playback

**Hardware Mode vs Simulation Mode:**
- **Hardware Mode**: Uses Piper TTS for real speech synthesis when SDK is available
- **Simulation Mode**: Provides status information without actual audio output

## Dependency Management

### Virtual Environment Structure

The project uses a sophisticated virtual environment setup:

```bash
# Hub-level virtual environment
/opt/distiller-mcp-hub/.venv/             # Main hub dependencies

# Project-specific virtual environments (uv workspace)
/opt/distiller-mcp-hub/projects/camera-mcp/.venv/   # Camera-specific deps
/opt/distiller-mcp-hub/projects/mic-mcp/.venv/      # Microphone-specific deps
/opt/distiller-mcp-hub/projects/speaker-mcp/.venv/  # Speaker-specific deps
```

### SDK Integration

The MCP services integrate with the Distiller CM5 SDK through multiple layers:

1. **Path-based imports**: SDK installed at `/opt/distiller-cm5-sdk/`
2. **Environment variables**: Automatic setup of `PYTHONPATH` and `LD_LIBRARY_PATH`
3. **Import utilities**: Each project has `sdk_imports.py` for clean SDK integration
4. **Runtime detection**: Services gracefully fall back to simulation mode if SDK unavailable
5. **Activation script**: Sources `/opt/distiller-cm5-sdk/activate.sh` when available

### Package Management Commands

```bash
# Update all workspace dependencies
uv sync

# Add dependency to specific project
cd projects/camera-mcp
uv add new-package

# Update hub-level dependencies
uv add --workspace new-package

# Check dependency tree
uv tree
```

## Service Management

### Systemd Service

The MCP Hub runs as a systemd service with:
- **Automatic startup** after network is available
- **Process monitoring** with automatic restart of crashed services
- **Graceful shutdown** with proper cleanup
- **Centralized logging** via systemd journal
- **Environment variables** automatically configured for SDK access

### Management Commands

```bash
# Service lifecycle
./manage_mcp_service.sh install      # Install service
./manage_mcp_service.sh uninstall    # Remove service
./manage_mcp_service.sh start        # Start service
./manage_mcp_service.sh stop         # Stop service
./manage_mcp_service.sh restart      # Restart service
./manage_mcp_service.sh status       # Check status

# Configuration and monitoring
./manage_mcp_service.sh config       # Edit configuration
./manage_mcp_service.sh logs         # View logs (follow mode)
./manage_mcp_service.sh enable       # Enable at boot
./manage_mcp_service.sh disable      # Disable at boot
```

## Development

### Adding New MCP Services

1. **Create project structure:**
```bash
mkdir projects/my-mcp
cd projects/my-mcp
uv init
```

2. **Add to workspace:**
```toml
# Add to pyproject.toml [tool.uv.workspace]
members = [
    "projects/camera-mcp",
    "projects/mic-mcp", 
    "projects/speaker-mcp",
    "projects/my-mcp",  # Add your new project
]
```

3. **Implement MCP server:**
```python
#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My MCP Server")

@mcp.tool()
async def my_tool() -> str:
    """My custom MCP tool"""
    return "Hello from my MCP service!"

if __name__ == "__main__":
    mcp.run()
```

4. **Add to configuration:**
```json
{
  "my-mcp": {
    "enabled": true,
    "port": 8004,
    "host": "0.0.0.0",
    "project_dir": "my-mcp",
    "description": "My Custom MCP Service"
  }
}
```

### Testing

```bash
# Test SDK imports and environment
python test_sdk_imports.py

# Test individual MCP services
cd projects/camera-mcp && uv run python server.py --transport stdio
cd projects/mic-mcp && uv run python server.py --transport stdio
cd projects/speaker-mcp && uv run python server.py --transport stdio

# Full system sanity check
python sanity_check.py
```

## Troubleshooting

### Common Issues

**1. MCP Service Won't Start**
```bash
# Check service logs
./manage_mcp_service.sh logs

# Verify configuration
./manage_mcp_service.sh config

# Test individual service
./venv_wrapper.sh --project camera-mcp server.py --transport sse --port 8001
```

**2. SDK Import Errors**
```bash
# Verify SDK installation
ls -la /opt/distiller-cm5-sdk/
source /opt/distiller-cm5-sdk/activate.sh

# Test SDK imports and environment
python test_sdk_imports.py

# Check environment variables
echo "PYTHONPATH: $PYTHONPATH"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
```

**3. Hardware Functionality Issues**
```bash
# Check if services are in simulation mode
curl http://localhost:8002/health  # Mic MCP status
curl http://localhost:8003/health  # Speaker MCP status

# Verify SDK environment
./venv_wrapper.sh --project mic-mcp server.py --transport stdio
# Look for "simulation mode" warnings in output
```

**4. Virtual Environment Issues**
```bash
# Recreate virtual environments
rm -rf .venv projects/*/venv
uv sync

# Check wrapper script
./venv_wrapper.sh --help
```

**5. Port Conflicts**
```bash
# Check port usage
netstat -tlnp | grep 800[1-3]

# Modify ports in configuration
./manage_mcp_service.sh config
```

### Logs and Monitoring

```bash
# Service logs
sudo journalctl -u mcp.service -f

# Individual service logs
sudo journalctl -u mcp.service | grep "\[camera\]"
sudo journalctl -u mcp.service | grep "\[mic\]"
sudo journalctl -u mcp.service | grep "\[speaker\]"

# System resource usage
htop
ps aux | grep python
```

## License

[MIT License](LICENSE.MIT)

## Support

For issues and questions:
- **GitHub Issues**: [Repository Issues](https://github.com/Pamir-AI/distiller-mcp-hub/issues)
- **Documentation**: See individual project README files
- **SDK Support**: Refer to distiller-cm5-sdk documentation 
