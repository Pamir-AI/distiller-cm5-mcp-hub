# MCP Hub Service

This service manages multiple MCP (Model Context Protocol) services automatically at boot time. It runs Camera, Microphone, and Speaker MCPs based on configuration.

## Files Created

- `mcp_config.json` - Configuration file (which MCPs to run and their settings)
- `run_all_mcps.py` - Main service manager script
- `mcp.service` - systemd service definition
- `manage_mcp_service.sh` - Helper script for service management

## Quick Start

### 1. Install the Service

```bash
cd /opt/distiller-mcp-hub
./manage_mcp_service.sh install
```

### 2. Enable at Boot

```bash
./manage_mcp_service.sh enable
```

### 3. Start the Service

```bash
./manage_mcp_service.sh start
```

## Configuration

Edit `mcp_config.json` to control which MCPs run:

```json
{
  "camera": {
    "enabled": true,
    "port": 8001,
    "project_dir": "camera-mcp",
    "description": "Camera MCP Service"
  },
  "mic": {
    "enabled": true,
    "port": 8002,
    "project_dir": "mic-mcp",
    "description": "Microphone MCP Service"
  },
  "speaker": {
    "enabled": false,
    "port": 8003,
    "project_dir": "speaker-mcp",
    "description": "Speaker MCP Service"
  }
}
```

**To disable an MCP:** Set `"enabled": false`  
**To change port:** Modify the `"port"` value  
**After changes:** Run `./manage_mcp_service.sh restart`

## Service Management

Use the helper script for all operations:

```bash
# Install/uninstall
./manage_mcp_service.sh install
./manage_mcp_service.sh uninstall

# Start/stop/restart
./manage_mcp_service.sh start
./manage_mcp_service.sh stop
./manage_mcp_service.sh restart

# Enable/disable at boot
./manage_mcp_service.sh enable
./manage_mcp_service.sh disable

# Monitor
./manage_mcp_service.sh status
./manage_mcp_service.sh logs

# Edit config
./manage_mcp_service.sh config
```

## Manual systemd Commands

If you prefer using systemd directly:

```bash
# Status and logs
sudo systemctl status mcp.service
sudo journalctl -u mcp.service -f

# Start/stop/restart
sudo systemctl start mcp.service
sudo systemctl stop mcp.service
sudo systemctl restart mcp.service

# Enable/disable at boot
sudo systemctl enable mcp.service
sudo systemctl disable mcp.service
```

## How It Works

1. **Boot Process:**
   - systemd starts `mcp.service` after network is online
   - Service runs `run_all_mcps.py`

2. **Manager Script:**
   - Reads `mcp_config.json`
   - Starts enabled MCPs in their project directories
   - Monitors processes and restarts them if they crash
   - Handles graceful shutdown

3. **Each MCP runs:**
   ```bash
   cd /opt/distiller-mcp-hub/projects/{project_dir}
   uv run python server.py --transport sse --port {port}
   ```

## Ports Used

- **Camera MCP:** Port 8001
- **Mic MCP:** Port 8002  
- **Speaker MCP:** Port 8003

## Logs

All logs go to systemd journal with identifier `mcp-hub`:

```bash
# Follow all logs
sudo journalctl -u mcp.service -f

# Show recent logs
sudo journalctl -u mcp.service -n 50

# Filter by MCP
sudo journalctl -u mcp.service | grep "\[camera\]"
```

## Troubleshooting

### Service won't start
```bash
# Check status
./manage_mcp_service.sh status

# Check logs
./manage_mcp_service.sh logs
```

### MCP not starting
1. Check if `server.py` exists in the project directory
2. Verify `uv` is installed and in PATH
3. Check port conflicts
4. Review configuration syntax

### Change configuration
1. Edit config: `./manage_mcp_service.sh config`
2. Restart service: `./manage_mcp_service.sh restart`

### Remove service completely
```bash
./manage_mcp_service.sh uninstall
```

## Features

- ✅ **Auto-start at boot** (after network is ready)
- ✅ **Config-driven** (single JSON file controls everything)
- ✅ **Process monitoring** (auto-restart crashed MCPs)
- ✅ **Graceful shutdown** (proper cleanup on stop)
- ✅ **Centralized logging** (all logs in systemd journal)
- ✅ **Easy management** (helper script for common tasks)
- ✅ **Individual MCP control** (enable/disable per MCP)
- ✅ **Production ready** (proper systemd integration) 