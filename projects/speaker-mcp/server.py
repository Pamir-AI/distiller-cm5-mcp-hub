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
async def text_to_speech(text: str, volume: int = 50, save_file: bool = False) -> str:
    """
    Convert text to speech using Piper TTS.
    
    Args:
        text: Text to convert to speech (required)
        volume: Volume level from 0-100 (default: 50)
        save_file: Whether to save audio file or just play (default: False)
        
    Returns:
        Path to generated WAV file if saved, or success message if played
    """
    try:
        if speaker is None:
            return "Speaker service not available: Piper library not loaded"
        
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        if save_file:
            file_path = speaker.text_to_speech(text, volume)
            return f"Text-to-speech completed. Audio saved to: {file_path}"
        else:
            result = speaker.speak_stream(text, volume, "snd_rpi_pamir_ai_soundcard")
            return result
            
    except ValueError as e:
        raise ValueError(f"Invalid input: {str(e)}")
    except Exception as e:
        raise ValueError(f"Text-to-speech failed: {str(e)}")

@mcp.tool()
async def play_text(text: str, volume: int = 50, sound_card: str = "snd_rpi_pamir_ai_soundcard") -> str:
    """
    Convert text to speech and play immediately without saving file.
    
    Args:
        text: Text to convert to speech and play
        volume: Volume level from 0-100 (default: 50)
        sound_card: Sound card name to use for playback
        
    Returns:
        Success message indicating text was played
    """
    try:
        if speaker is None:
            return "Speaker service not available: Piper library not loaded"
        
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        result = speaker.speak_stream(text, volume, sound_card)
        return result
        
    except ValueError as e:
        raise ValueError(f"Invalid input: {str(e)}")
    except Exception as e:
        raise ValueError(f"Speech playback failed: {str(e)}")

@mcp.tool()
async def list_tts_files() -> str:
    """
    List all generated TTS files with metadata.
    
    Returns:
        JSON formatted list of TTS files with details
    """
    try:
        if speaker is None:
            return "Speaker service not available: Piper library not loaded"
        
        files = speaker.list_tts_files()
        
        if not files:
            return "No TTS files found in output directory."
        
        # Format the file information
        formatted_files = []
        for file_info in files:
            created_time = datetime.fromtimestamp(file_info["created"]).strftime("%Y-%m-%d %H:%M:%S")
            size_mb = round(file_info["size_bytes"] / (1024 * 1024), 2)
            
            formatted_files.append({
                "filename": file_info["filename"],
                "path": file_info["path"],
                "size_mb": size_mb,
                "created": created_time
            })
        
        return json.dumps(formatted_files, indent=2)
        
    except Exception as e:
        raise ValueError(f"Failed to list TTS files: {str(e)}")

@mcp.tool()
async def get_available_models() -> str:
    """
    Get list of available TTS models.
    
    Returns:
        List of available Piper TTS models
    """
    try:
        if speaker is None:
            return "Speaker service not available: Piper library not loaded"
        
        models = speaker.get_available_models()
        
        return f"Available TTS Models:\n" + "\n".join(f"- {model}" for model in models)
        
    except Exception as e:
        return f"Failed to get models: {str(e)}"

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

@mcp.tool()
async def clean_old_files(max_files: int = 10) -> str:
    """
    Clean up old TTS files, keeping only the most recent ones.
    
    Args:
        max_files: Maximum number of files to keep (default: 10)
        
    Returns:
        Summary of cleanup operation
    """
    try:
        if speaker is None:
            return "Speaker service not available: Piper library not loaded"
        
        files = speaker.list_tts_files()
        
        if len(files) <= max_files:
            return f"No cleanup needed. Current files: {len(files)}, limit: {max_files}"
        
        # Remove oldest files
        files_to_remove = files[max_files:]
        removed_count = 0
        
        import os
        for file_info in files_to_remove:
            try:
                os.remove(file_info["path"])
                removed_count += 1
            except Exception as e:
                print(f"Warning: Could not remove {file_info['filename']}: {e}")
        
        return f"Cleanup completed. Removed {removed_count} old files. Kept {len(files) - removed_count} most recent files."
        
    except Exception as e:
        return f"Cleanup failed: {str(e)}"

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