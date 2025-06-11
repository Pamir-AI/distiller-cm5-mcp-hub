#!/usr/bin/env python3
"""
Pi Camera MCP Server

Provides MCP tools for capturing camera snapshots and checking camera status.
Uses FastMCP for proper MCP implementation.
"""

import sys
import argparse
import asyncio
import base64
from mcp.server.fastmcp import FastMCP, Image

# Import camera module
import camera

# Create MCP server using FastMCP (recommended approach)
mcp = FastMCP("Pi Camera MCP Server")

@mcp.tool()
async def get_camera_snapshot() -> Image:
    """
    Capture a snapshot from the Pi Camera and return it as base64-encoded JPEG.
    
    Returns:
        An Image object containing the captured snapshot.
    """
    try:
        # Capture the image bytes
        img_bytes = camera.capture_snapshot()
        
        # Return using FastMCP's Image class which handles base64 encoding automatically
        return Image(data=img_bytes, format="jpeg")
        
    except Exception as e:
        # For errors, we need to return a string since Image expects valid image data
        raise ValueError(f"Failed to capture camera snapshot: {str(e)}")

@mcp.tool()
async def get_camera_status() -> str:
    """
    Check the status and availability of the Pi Camera.
    
    Returns:
        A detailed status report of the camera system.
    """
    try:
        # Try to import Picamera2 to check if camera module is available
        from picamera2 import Picamera2
        
        # Check for available cameras
        available_cameras = Picamera2.global_camera_info()
        
        if available_cameras:
            camera_info = []
            for i, camera in enumerate(available_cameras):
                camera_info.append(f"Camera {i}: {camera}")
            
            status_text = f"""Camera Status: AVAILABLE
Number of cameras detected: {len(available_cameras)}

Camera Details:
{chr(10).join(camera_info)}

Camera module is properly installed and functional."""
            
        else:
            status_text = """Camera Status: NO CAMERAS DETECTED
No cameras were found on this system.
This could mean:
- No camera is connected
- Camera is in use by another process  
- Camera permissions are not properly configured

Test images will be generated instead of real camera captures."""
            
    except ImportError:
        status_text = """Camera Status: MODULE NOT AVAILABLE
Picamera2 module is not installed.
Install with: pip install picamera2

Test images will be generated instead of real camera captures."""
        
    except Exception as e:
        status_text = f"""Camera Status: ERROR
An error occurred while checking camera status: {str(e)}

Test images will be generated instead of real camera captures."""
    
    return status_text

def main():
    """Main entry point with command line argument parsing"""
    parser = argparse.ArgumentParser(description='Pi Camera MCP Server')
    parser.add_argument('--transport', choices=['stdio', 'sse', 'streamable-http'], 
                       default='stdio', help='Transport protocol (default: stdio)')
    parser.add_argument('--host', default='localhost', 
                       help='Host to bind to for HTTP transports (default: localhost)')
    parser.add_argument('--port', type=int, default=3000,
                       help='Port to bind to for HTTP transports (default: 3000)')
    
    args = parser.parse_args()
    
    if args.transport == 'stdio':
        print("🚀 Starting on STDIO transport (ready for MCP clients)")
        mcp.run()
    elif args.transport == 'sse':
        print(f"🚀 Starting on SSE transport at http://{args.host}:{args.port}")
        print(f"🔧 MCP endpoint: http://{args.host}:{args.port}/sse")
        print(f"❤️ Health check: http://{args.host}:{args.port}/health")
        
        # For FastMCP with custom host/port, we need to configure settings
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="sse")
    elif args.transport == 'streamable-http':
        print(f"🚀 Starting on streamable HTTP transport at http://{args.host}:{args.port}")
        print(f"🔧 MCP endpoint: http://{args.host}:{args.port}/mcp")
        print(f"❤️ Health check: http://{args.host}:{args.port}/health")
        
        # For FastMCP with custom host/port, we need to configure settings  
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main() 