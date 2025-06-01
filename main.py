#!/usr/bin/env python3
"""
MCP-Server Development Platform
Main application entry point for Raspberry Pi 5
"""

import os
import sys
import argparse
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# Add backend to Python path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.api import projects, debug, deploy
from config.settings import Settings

# Initialize settings
settings = Settings()

# Create FastAPI app
app = FastAPI(
    title="MCP-Server Development Platform",
    description="Rapid MCP-Server development and deployment for Raspberry Pi 5",
    version="1.0.0"
)

# Setup static files and templates
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# Include API routes
app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(debug.router, prefix="/api", tags=["debug"])
app.include_router(deploy.router, prefix="/api", tags=["deploy"])

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main application interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "platform": "raspberry-pi-5"}

def create_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        Path("projects"),
        Path("logs"),
        Path("frontend/static"),
        Path("frontend/templates")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✓ Directory created: {directory}")

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="MCP-Server Development Platform")
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    
    # Create necessary directories
    create_directories()
    
    print("🚀 Starting MCP-Server Development Platform...")
    print(f"📡 Access the web interface at: http://{args.host}:{args.port}")
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.dev,
        log_level="info" if not args.dev else "debug"
    )

if __name__ == "__main__":
    main() 