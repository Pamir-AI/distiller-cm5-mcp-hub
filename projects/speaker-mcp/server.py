#!/usr/bin/env python3
"""
Speaker MCP Server

Text-to-Speech functionality using Piper library.
Provides tools for converting text to speech and managing generated audio files.
"""

import argparse
import sys
import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Import domain logic
try:
    from speaker import Speaker
    speaker = Speaker()
except ImportError as e:
    print(f"Warning: Failed to import speaker logic: {e}")
    speaker = None

# Create MCP server
mcp = FastMCP("Speaker MCP Server")

@mcp.tool()
async def text_to_speech(text: str, volume: int = 50) -> str:
    """
    Convert text to speech using Piper TTS.
    
    Args:
        text: Text to convert to speech (required)
        volume: Volume level from 0-100 (default: 50)
        
    Returns:
        Success message if played
    """
    try:
        if speaker is None:
            return "Speaker service not available: Piper library not loaded"
        
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        result = speaker.speak_stream(text, volume, "snd_rpi_pamir_ai_soundcard")
        return result
            
    except ValueError as e:
        raise ValueError(f"Invalid input: {str(e)}")
    except Exception as e:
        raise ValueError(f"Text-to-speech failed: {str(e)}")

@mcp.tool()
async def get_speaker_status() -> str:
    """
    Get speaker service status and health information.
    
    Returns:
        Service status information including model details and file counts
    """
    try:
        if speaker is None:
            return "Speaker service not available: Piper library not loaded"
        
        status = speaker.get_status()
        return status
        
    except Exception as e:
        return f"Status check failed: {str(e)}"

def main():
    """Main entry point with transport configuration."""
    parser = argparse.ArgumentParser(description='Speaker MCP Server')
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
        if speaker:
            speaker.cleanup()
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 