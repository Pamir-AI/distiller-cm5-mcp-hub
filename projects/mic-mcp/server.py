#!/usr/bin/env python3
"""
Microphone MCP Server
Provides audio recording and transcription tools using distiller-cm5-sdk parakeet.
"""

import argparse
import asyncio
import json
import os
import time
import threading
import random
import io
import wave
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Import the parakeet module from distiller-cm5-sdk
try:
    from distiller_cm5_sdk.parakeet.parakeet import Parakeet
    PARAKEET_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Failed to import parakeet: {e}")
    print("Running in simulation mode")
    PARAKEET_AVAILABLE = False

# Create MCP server instance
mcp = FastMCP("Microphone MCP Server")

# Global state for recordings and parakeet instance
recordings_dir = Path("recordings")
recordings_dir.mkdir(exist_ok=True)
recordings_db: Dict[str, Dict] = {}
parakeet_instance: Optional = None
recording_timer: Optional[threading.Timer] = None
current_recording_id: Optional[str] = None
simulation_mode = False

def initialize_parakeet():
    """Initialize the Parakeet instance for audio processing."""
    global parakeet_instance, simulation_mode
    
    if not PARAKEET_AVAILABLE:
        simulation_mode = True
        print("Parakeet not available, enabling simulation mode")
        return True
        
    try:
        parakeet_instance = Parakeet(vad_silence_duration=1.0)
        simulation_mode = False
        return True
    except Exception as e:
        print(f"Failed to initialize Parakeet (using simulation mode): {e}")
        simulation_mode = True
        return True

def generate_recording_id() -> str:
    """Generate a unique recording ID based on timestamp."""
    return f"recording_{int(time.time() * 1000)}"

def generate_mock_audio(duration: int) -> bytes:
    """Generate mock audio data for simulation mode."""
    sample_rate = 16000
    samples = duration * sample_rate
    
    # Generate some simple sine wave audio
    import math
    frequency = 440  # A4 note
    audio_data = []
    
    for i in range(samples):
        # Add some variation to make it more realistic
        noise = random.uniform(-0.1, 0.1)
        sample = math.sin(2 * math.pi * frequency * i / sample_rate) * 0.3 + noise
        # Convert to 16-bit PCM
        sample_int = int(sample * 32767)
        sample_int = max(-32768, min(32767, sample_int))
        audio_data.append(sample_int)
    
    # Create WAV format bytes
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        # Convert to bytes
        import struct
        wav_data = struct.pack(f'<{len(audio_data)}h', *audio_data)
        wf.writeframes(wav_data)
    
    return buffer.getvalue()

def save_recording_metadata(recording_id: str, metadata: Dict):
    """Save recording metadata to the database."""
    recordings_db[recording_id] = metadata
    
    # Also save to disk for persistence
    metadata_file = recordings_dir / f"{recording_id}_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

def load_existing_recordings():
    """Load existing recordings from disk on startup."""
    global recordings_db
    for metadata_file in recordings_dir.glob("*_metadata.json"):
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                recording_id = metadata_file.stem.replace("_metadata", "")
                recordings_db[recording_id] = metadata
        except Exception as e:
            print(f"Failed to load metadata from {metadata_file}: {e}")

def stop_recording_timer():
    """Stop the current recording after timer expires."""
    global current_recording_id, parakeet_instance, simulation_mode
    if current_recording_id:
        try:
            if simulation_mode:
                # Generate mock audio
                if current_recording_id in recordings_db:
                    duration = recordings_db[current_recording_id].get('duration', 5)
                    audio_data = generate_mock_audio(duration)
                else:
                    audio_data = generate_mock_audio(5)
            else:
                audio_data = parakeet_instance.stop_recording()
                
            if audio_data:
                # Save the recording
                audio_file = recordings_dir / f"{current_recording_id}.wav"
                with open(audio_file, 'wb') as f:
                    f.write(audio_data)
                
                # Update metadata
                if current_recording_id in recordings_db:
                    recordings_db[current_recording_id]['status'] = 'completed'
                    recordings_db[current_recording_id]['file_size'] = len(audio_data)
                    recordings_db[current_recording_id]['end_time'] = datetime.now().isoformat()
                    recordings_db[current_recording_id]['simulation_mode'] = simulation_mode
                    save_recording_metadata(current_recording_id, recordings_db[current_recording_id])
                    
            current_recording_id = None
        except Exception as e:
            print(f"Error stopping recording: {e}")

@mcp.tool()
async def record_for_seconds(duration: int = 5) -> str:
    """
    Record audio for a specified number of seconds.
    
    Args:
        duration: Duration in seconds to record (default: 5, max: 300)
        
    Returns:
        Status message with recording ID and details
    """
    global parakeet_instance, recording_timer, current_recording_id, simulation_mode
    
    try:
        # Validate duration
        if duration <= 0 or duration > 300:
            return "Error: Duration must be between 1 and 300 seconds"
            
        # Initialize parakeet if needed
        if parakeet_instance is None and not simulation_mode:
            if not initialize_parakeet():
                return "Error: Failed to initialize audio system"
        
        # Check if already recording
        if current_recording_id:
            return f"Error: Already recording (ID: {current_recording_id}). Stop current recording first."
            
        # Generate recording ID and start recording
        recording_id = generate_recording_id()
        current_recording_id = recording_id
        
        if simulation_mode:
            # In simulation mode, we just start the timer
            recording_started = True
        else:
            recording_started = parakeet_instance.start_recording()
            
        if not recording_started:
            current_recording_id = None
            return "Error: Failed to start recording"
            
        # Set up timer to stop recording
        recording_timer = threading.Timer(duration, stop_recording_timer)
        recording_timer.start()
        
        # Save initial metadata
        metadata = {
            'id': recording_id,
            'start_time': datetime.now().isoformat(),
            'duration': duration,
            'status': 'recording',
            'file_size': None,
            'end_time': None,
            'simulation_mode': simulation_mode
        }
        save_recording_metadata(recording_id, metadata)
        
        mode_info = " (simulation mode)" if simulation_mode else ""
        return f"Recording started{mode_info} (ID: {recording_id}) for {duration} seconds"
        
    except Exception as e:
        current_recording_id = None
        return f"Error starting recording: {str(e)}"

@mcp.tool()
async def list_recordings() -> str:
    """
    List all available recordings with their metadata.
    
    Returns:
        Formatted list of recordings with details
    """
    try:
        if not recordings_db:
            return "No recordings found"
            
        result = "Available Recordings:\n\n"
        for recording_id, metadata in recordings_db.items():
            result += f"ID: {recording_id}\n"
            result += f"  Start Time: {metadata.get('start_time', 'Unknown')}\n"
            result += f"  Duration: {metadata.get('duration', 'Unknown')} seconds\n"
            result += f"  Status: {metadata.get('status', 'Unknown')}\n"
            result += f"  File Size: {metadata.get('file_size', 'Unknown')} bytes\n"
            result += f"  End Time: {metadata.get('end_time', 'Unknown')}\n"
            result += f"  Simulation Mode: {metadata.get('simulation_mode', 'Unknown')}\n"
            result += "\n"
            
        return result
        
    except Exception as e:
        return f"Error listing recordings: {str(e)}"

@mcp.tool()
async def get_recording(recording_id: str) -> str:
    """
    Get detailed information about a specific recording.
    
    Args:
        recording_id: The ID of the recording to retrieve
        
    Returns:
        Detailed information about the recording
    """
    try:
        if recording_id not in recordings_db:
            return f"Recording {recording_id} not found"
            
        metadata = recordings_db[recording_id]
        audio_file = recordings_dir / f"{recording_id}.wav"
        
        result = f"Recording Details for {recording_id}:\n\n"
        result += f"Start Time: {metadata.get('start_time', 'Unknown')}\n"
        result += f"Duration: {metadata.get('duration', 'Unknown')} seconds\n"
        result += f"Status: {metadata.get('status', 'Unknown')}\n"
        result += f"File Size: {metadata.get('file_size', 'Unknown')} bytes\n"
        result += f"End Time: {metadata.get('end_time', 'Unknown')}\n"
        result += f"Simulation Mode: {metadata.get('simulation_mode', False)}\n"
        result += f"Audio File: {audio_file}\n"
        result += f"File Exists: {audio_file.exists()}\n"
        
        return result
        
    except Exception as e:
        return f"Error getting recording: {str(e)}"

@mcp.tool()
async def get_transcription(recording_id: str) -> str:
    """
    Get transcription for a specific recording.
    
    Args:
        recording_id: The ID of the recording to transcribe
        
    Returns:
        Transcribed text from the recording
    """
    global parakeet_instance, simulation_mode
    
    try:
        if recording_id not in recordings_db:
            return f"Recording {recording_id} not found"
            
        audio_file = recordings_dir / f"{recording_id}.wav"
        if not audio_file.exists():
            return f"Audio file for recording {recording_id} not found"
            
        # Check if this recording was made in simulation mode
        recording_metadata = recordings_db[recording_id]
        was_simulated = recording_metadata.get('simulation_mode', False)
        
        if was_simulated or simulation_mode:
            # Generate mock transcription for simulation
            mock_transcriptions = [
                "This is a test recording from the microphone MCP server.",
                "Hello, this is a sample audio transcription.",
                "Testing the audio recording and transcription functionality.",
                "This recording was generated in simulation mode.",
                f"Mock transcription for recording {recording_id}."
            ]
            transcription_text = random.choice(mock_transcriptions)
        else:
            # Initialize parakeet if needed
            if parakeet_instance is None:
                if not initialize_parakeet():
                    return "Error: Failed to initialize audio system for transcription"
            
            # Read audio file and transcribe
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
                
            transcription_results = []
            for text in parakeet_instance.transcribe_buffer(audio_data):
                transcription_results.append(text)
                
            if not transcription_results:
                return f"No transcription generated for recording {recording_id}"
                
            transcription_text = " ".join(transcription_results)
        
        # Save transcription to metadata
        recordings_db[recording_id]['transcription'] = transcription_text
        recordings_db[recording_id]['transcription_time'] = datetime.now().isoformat()
        save_recording_metadata(recording_id, recordings_db[recording_id])
        
        return f"Transcription for {recording_id}:\n\n{transcription_text}"
        
    except Exception as e:
        return f"Error transcribing recording: {str(e)}"

@mcp.tool()
async def stop_current_recording() -> str:
    """
    Stop the current recording if one is active.
    
    Returns:
        Status message about stopping the recording
    """
    global current_recording_id, recording_timer, parakeet_instance, simulation_mode
    
    try:
        if not current_recording_id:
            return "No active recording to stop"
            
        # Cancel the timer
        if recording_timer:
            recording_timer.cancel()
            recording_timer = None
            
        recording_id = current_recording_id
        current_recording_id = None
        
        if simulation_mode:
            # Generate mock audio
            duration = recordings_db[recording_id].get('duration', 5)
            audio_data = generate_mock_audio(duration)
        else:
            # Stop recording
            audio_data = parakeet_instance.stop_recording()
        
        if audio_data:
            # Save the recording
            audio_file = recordings_dir / f"{recording_id}.wav"
            with open(audio_file, 'wb') as f:
                f.write(audio_data)
            
            # Update metadata
            recordings_db[recording_id]['status'] = 'completed'
            recordings_db[recording_id]['file_size'] = len(audio_data)
            recordings_db[recording_id]['end_time'] = datetime.now().isoformat()
            recordings_db[recording_id]['simulation_mode'] = simulation_mode
            save_recording_metadata(recording_id, recordings_db[recording_id])
            
            mode_info = " (simulation mode)" if simulation_mode else ""
            return f"Recording {recording_id} stopped{mode_info} and saved ({len(audio_data)} bytes)"
        else:
            return f"Recording {recording_id} stopped but no audio data captured"
            
    except Exception as e:
        return f"Error stopping recording: {str(e)}"

@mcp.tool()
async def get_system_status() -> str:
    """
    Get system status and audio capabilities.
    
    Returns:
        System information and audio device status
    """
    global simulation_mode
    
    try:
        status_info = []
        status_info.append(f"Recordings Directory: {recordings_dir.absolute()}")
        status_info.append(f"Total Recordings: {len(recordings_db)}")
        status_info.append(f"Current Recording: {current_recording_id or 'None'}")
        status_info.append(f"Parakeet Available: {PARAKEET_AVAILABLE}")
        status_info.append(f"Simulation Mode: {simulation_mode}")
        status_info.append(f"Parakeet Initialized: {parakeet_instance is not None}")
        
        # Audio device info
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            default_input = sd.default.device[0]
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            
            status_info.append(f"Available Input Devices: {len(input_devices)}")
            if input_devices:
                status_info.append(f"Default Input Device: {devices[default_input]['name']}")
            else:
                status_info.append("Default Input Device: None available")
        except Exception as e:
            status_info.append(f"Audio Device Info Error: {e}")
            
        return "\n".join(status_info)
        
    except Exception as e:
        return f"Error getting system status: {str(e)}"

def main():
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description='Microphone MCP Server')
    parser.add_argument('--transport', default='stdio',
                       choices=['stdio', 'sse', 'streamable-http'])
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=3000)
    
    args = parser.parse_args()
    
    # Load existing recordings on startup
    load_existing_recordings()
    
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

if __name__ == "__main__":
    main() 