"""
MCP Hub - Simplified
A streamlined MCP (Model Context Protocol) server management and testing interface
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.api import mcp as mcp_api
from backend.services.mcp_discovery import mcp_discovery
from backend.services.mcp_server_manager import mcp_server_manager
from backend.services.tool_discovery import tool_discovery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    logger.info("🔌 MCP Hub starting up...")
    
    # Initialize services
    try:
        # Discover MCPs on startup
        mcps = await mcp_discovery.discover_mcps(force_refresh=True)
        logger.info(f"Discovered {len(mcps)} MCPs")
        
        for mcp in mcps:
            logger.info(f"  - {mcp.name} ({mcp.status.value})")
    
    except Exception as e:
        logger.error(f"Error during startup: {e}")
    
    yield
    
    # Shutdown
    logger.info("🔌 MCP Hub shutting down...")
    try:
        await mcp_server_manager.cleanup()
        logger.info("✅ Cleanup completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="MCP Hub",
    description="Simplified MCP Management and Testing Hub",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(mcp_api.router)

# Setup templates
templates = Jinja2Templates(directory="frontend/templates")

# Serve static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main page - simplified MCP Hub interface"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Quick service checks
        mcps = await mcp_discovery.discover_mcps(force_refresh=False)
        servers = await mcp_server_manager.list_servers()
        
        return {
            "status": "healthy",
            "services": {
                "mcp_discovery": "ok",
                "server_manager": "ok",
                "tool_discovery": "ok"
            },
            "stats": {
                "discovered_mcps": len(mcps),
                "running_servers": len([s for s in servers if s["state"] == "running"])
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    try:
        mcps = await mcp_discovery.discover_mcps(force_refresh=False)
        servers = await mcp_server_manager.list_servers()
        
        mcp_stats = {
            "ready": len([m for m in mcps if m.status.value == "ready"]),
            "missing_deps": len([m for m in mcps if m.status.value == "missing_deps"]),
            "error": len([m for m in mcps if m.status.value == "error"]),
            "total": len(mcps)
        }
        
        server_stats = {
            "running": len([s for s in servers if s["state"] == "running"]),
            "stopped": len([s for s in servers if s["state"] == "stopped"]),
            "error": len([s for s in servers if s["state"] == "error"]),
            "total": len(servers)
        }
        
        return {
            "status": "ok",
            "mcps": mcp_stats,
            "servers": server_stats,
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        logger.error(f"API status check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }


if __name__ == "__main__":
    import uvicorn
    
    # Ensure directories exist
    Path("frontend/static").mkdir(parents=True, exist_ok=True)
    Path("frontend/templates").mkdir(parents=True, exist_ok=True)
    
    logger.info("🚀 Starting MCP Hub...")
    uvicorn.run(
        "backend.main_simplified:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 