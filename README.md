# MCP Hub - Simplified

A streamlined **Model Context Protocol (MCP)** server management and testing interface.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
uv pip install -r requirements.txt
```

### 2. Start MCP Hub
```bash
python start_mcp_hub.py
```

### 3. Open in Browser
- **Frontend UI**: http://localhost:3000/templates/
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 💡 How to Use

1. **Discover MCPs**: The system automatically scans the `projects/` folder for MCP servers
2. **Select MCP**: Click on an MCP in the left panel to start its server
3. **Browse Tools**: View available tools in the right panel
4. **Test Tools**: Use the form interface to test tools with parameters

## 📁 Project Structure

```
├── projects/                    # MCP servers auto-discovered here
│   ├── google_workspace_mcp/   # Example: Google Workspace MCP
│   └── playwright-plus-python-mcp/  # Example: Playwright MCP
├── backend/                    # Backend API services
│   ├── api/                   # API endpoints
│   ├── services/             # Core services (discovery, server management)
│   └── main_simplified.py   # Main backend application
├── frontend/                  # Static frontend files
│   └── templates/            # HTML templates
├── main.py                   # Backend entry point
└── start_mcp_hub.py         # Complete startup script
```

## 🔧 Manual Startup (Alternative)

If you prefer to start services manually:

```bash
# Start backend only
python main.py

# Start frontend only (in another terminal)
cd frontend && python -m http.server 3000
```

## 🛠️ Development

### Adding New MCPs
1. Place MCP project in `projects/` folder
2. Ensure it has proper `pyproject.toml` or `requirements.txt`
3. MCP Hub will auto-discover it on next startup

### API Endpoints
- `GET /api/mcp/list` - List all discovered MCPs
- `POST /api/mcp/{id}/start` - Start an MCP server
- `GET /api/mcp/{id}/tools` - Get available tools
- `POST /api/mcp/{id}/tools/{tool}/call` - Execute a tool

## 🔍 Troubleshooting

**MCP not discovered?**
- Check `projects/` folder structure
- Ensure MCP has `pyproject.toml` or entry point file
- Look for virtual environment in `.venv/`

**Server won't start?**
- Check if ports 8000/3000 are available
- Verify dependencies are installed
- Check console output for specific errors

**Tools not loading?**
- Ensure MCP server started successfully
- Check MCP server logs in terminal
- Verify MCP implements tool discovery properly

## 🎯 Features

- ✅ **Auto-discovery** of MCP servers in projects/ folder
- ✅ **Automatic server management** (start/stop/restart)
- ✅ **Tool discovery** from running MCP servers
- ✅ **Interactive testing** interface with form generation
- ✅ **Real-time status** updates and error handling
- ✅ **Support for both** stdio and HTTP MCP protocols