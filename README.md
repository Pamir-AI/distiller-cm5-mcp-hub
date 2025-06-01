 # Raspberry Pi 5 MCP-Server Development Platform

A comprehensive web application for rapid creation, debugging, and deployment of MCP-Server services on Raspberry Pi 5.

## Features

- **Project Management**: Create and manage MCP-Server projects using uv
- **Script Upload**: Upload and integrate MCP scripts
- **Dependency Management**: Automated Python dependency installation
- **Debug & Test**: Integrated MCP-Inspector functionality
- **One-Click Deploy**: Launch services with network access

## Tech Stack

- **Backend**: FastAPI + Uvicorn
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **Package Management**: uv toolkit
- **Process Management**: subprocess + asyncio
- **File Operations**: pathlib + async IO

## Quick Start

1. **Installation**:
   ```bash
   cd mcp_dev_platform
   pip install -r requirements.txt
   ```

2. **Run Development Server**:
   ```bash
   python main.py
   ```

3. **Access Web Interface**:
   Open `http://localhost:8000` in your browser

## Directory Structure

```
mcp_dev_platform/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── config/
│   ├── settings.py        # Application configuration
│   └── systemd/           # Service deployment configs
├── backend/
│   ├── __init__.py
│   ├── api/               # FastAPI routes
│   ├── services/          # Business logic
│   ├── models/            # Data models
│   └── utils/             # Utility functions
├── frontend/
│   ├── static/            # CSS, JS, images
│   └── templates/         # HTML templates
├── projects/              # MCP projects workspace
└── logs/                  # Application logs
```

## API Endpoints

- `POST /api/projects` - Create new project
- `POST /api/projects/{id}/upload` - Upload MCP script
- `POST /api/projects/{id}/install` - Install dependencies
- `POST /api/projects/{id}/debug` - Start debug session
- `POST /api/projects/{id}/deploy` - Deploy service
- `GET /api/projects/{id}/status` - Get project status
- `GET /api/projects/{id}/logs` - Get service logs

## Deployment

### Systemd Service
```bash
sudo cp config/systemd/mcp-dev-platform.service /etc/systemd/system/
sudo systemctl enable mcp-dev-platform
sudo systemctl start mcp-dev-platform
```

### Development Mode
```bash
python main.py --dev
```

## Usage Workflow

1. **Create Project**: Input service name and click "Create Project"
2. **Upload Script**: Upload your MCP script files
3. **Install Dependencies**: Automatically detect and install requirements
4. **Debug & Test**: Use integrated MCP-Inspector to test tools
5. **Deploy**: One-click deployment with network access

## License

MIT License