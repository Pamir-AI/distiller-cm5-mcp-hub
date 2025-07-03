# Microphone MCP Server

An MCP (Model Context Protocol) server that provides audio recording and transcription tools using the distiller-cm5-sdk parakeet module.

## Features

- **Record Audio**: Record audio for a specified duration (1-300 seconds)
- **List Recordings**: View all available recordings with metadata
- **Get Recording Details**: Retrieve detailed information about specific recordings
- **Transcription**: Generate transcriptions of recorded audio using Parakeet ASR
- **Persistent Storage**: Recordings and metadata are saved to disk for persistence
- **Real-time Status**: Monitor recording status and system capabilities

## Installation

1. Ensure you have the distiller-cm5-sdk installed at `/opt/distiller-cm5-sdk`
2. Install the MCP server dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Run the MCP Server

```bash
python server.py
```

The server will start in stdio mode by default, suitable for integration with MCP clients.

### Alternative Transport Methods

```bash
# Run with SSE transport
python server.py --transport sse --host localhost --port 3000

# Run with HTTP transport
python server.py --transport streamable-http --host localhost --port 3000
```

## Available Tools

### 1. `record_for_seconds`
Record audio for a specified number of seconds.

**Parameters:**
- `duration` (int): Duration in seconds (default: 5, max: 300)

**Returns:** Status message with recording ID

**Example:**
```
record_for_seconds(10)  # Record for 10 seconds
```

### 2. `list_recordings`
List all available recordings with their metadata.

**Parameters:** None

**Returns:** Formatted list of recordings with details

### 3. `get_recording`
Get detailed information about a specific recording.

**Parameters:**
- `recording_id` (str): The ID of the recording to retrieve

**Returns:** Detailed information about the recording

### 4. `get_transcription`
Get transcription for a specific recording using Parakeet ASR.

**Parameters:**
- `recording_id` (str): The ID of the recording to transcribe

**Returns:** Transcribed text from the recording

### 5. `stop_current_recording`
Stop the current recording if one is active.

**Parameters:** None

**Returns:** Status message about stopping the recording

### 6. `get_system_status`
Get system status and audio capabilities.

**Parameters:** None

**Returns:** System information and audio device status

## Usage Examples

### Basic Recording Workflow

1. **Start a recording:**
   ```
   record_for_seconds(15)
   ```
   Response: `Recording started (ID: recording_1703123456789) for 15 seconds`

2. **List all recordings:**
   ```
   list_recordings()
   ```

3. **Get recording details:**
   ```
   get_recording("recording_1703123456789")
   ```

4. **Get transcription:**
   ```
   get_transcription("recording_1703123456789")
   ```

### Manual Recording Control

1. **Start recording:**
   ```
   record_for_seconds(60)  # Will auto-stop after 60 seconds
   ```

2. **Stop early if needed:**
   ```
   stop_current_recording()
   ```

## File Structure

The server creates the following structure:

```
mic-mcp/
├── server.py              # MCP server implementation
├── requirements.txt       # Dependencies
├── README.md             # This file
└── recordings/           # Created automatically
    ├── recording_*.wav   # Audio files
    └── recording_*_metadata.json  # Metadata files
```

## Audio Requirements

- **Sample Rate**: 16kHz (required by Parakeet)
- **Channels**: Mono (1 channel)
- **Format**: 16-bit PCM WAV
- **Device**: Uses default system microphone (configurable in parakeet)

## Troubleshooting

### Common Issues

1. **"Failed to import parakeet"**
   - Ensure distiller-cm5-sdk is properly installed
   - Check Python path includes the SDK

2. **"Failed to initialize audio system"**
   - Check microphone permissions
   - Verify audio device availability
   - Ensure no other applications are using the microphone

3. **"No audio recorded"**
   - Check microphone is working
   - Verify microphone is not muted
   - Check audio device selection

### Debug Information

Use the `get_system_status` tool to check:
- Audio device availability
- Parakeet initialization status
- Recording directory status
- Current recording state

## Integration with MCP Clients

This server follows the MCP protocol and can be integrated with any MCP-compatible client:

1. **Claude Desktop**: Add to your MCP configuration
2. **Custom Clients**: Use MCP client libraries to connect
3. **API Integration**: Use HTTP transport for web applications

## Dependencies

- **mcp**: Model Context Protocol server library
- **distiller-cm5-sdk**: Audio processing and transcription (installed at `/opt/distiller-cm5-sdk`)
- **Python 3.9+**: Required for the SDK

## License

This project follows the same license as the distiller-cm5-sdk. 