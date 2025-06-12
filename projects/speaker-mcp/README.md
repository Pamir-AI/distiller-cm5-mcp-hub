# Speaker MCP Server

Text-to-Speech functionality using the Piper library for the Distiller CM5 platform. This MCP (Model Context Protocol) server provides real-time speech synthesis capabilities through streaming audio playback.

## Features

- **Real-time Text-to-Speech**: Convert text to speech with immediate streaming playback
- **Volume Control**: Adjustable playback volume levels (0-100)
- **Service Health Monitoring**: Check TTS service status and configuration
- **Multiple Transport Protocols**: Support for stdio, SSE, and HTTP transports
- **Graceful Error Handling**: Robust error handling with detailed feedback

## Installation

1. Ensure you have the distiller-cm5-sdk wheel available
2. Install dependencies using UV:
   ```bash
   cd /home/distiller/distiller-cm5-mcp-hub/projects/speaker-mcp
   uv sync
   ```

## Usage

### Run the MCP Server

```bash
# Using UV with entry point (default stdio transport)
uv run distiller-cm5-speaker-mcp

# Or directly with Python
uv run python server.py
```

### Alternative Transport Methods

```bash
# SSE transport for web applications
uv run python server.py --transport sse --host localhost --port 3000

# HTTP transport for REST-like interfaces
uv run python server.py --transport streamable-http --host localhost --port 3000
```

## Available Tools

### 1. `text_to_speech`
Convert text to speech using Piper TTS with streaming playback.

**Parameters:**
- `text` (str, required): Text to convert to speech
- `volume` (int, optional): Volume level from 0-100 (default: 50)

**Returns:** Success message with truncated text preview

**Example:**
```json
{
  "text": "Hello, welcome to the Distiller CM5 platform!",
  "volume": 75
}
```

**Response:**
```
"Successfully played text: 'Hello, welcome to the Distiller CM5 platform!'"
```

### 2. `get_speaker_status`
Get comprehensive speaker service status and health information.

**Parameters:** None

**Returns:** Detailed service status including:
- Service initialization status
- Current voice model information
- Output directory and file counts
- Piper executable path

**Example Response:**
```
Speaker Service Status:
- Service: Running normally
- Model: en_US-amy-medium.onnx
- Output directory: /tmp/tts_output
- Generated files: 5
- Piper executable: /path/to/piper
```

## Architecture

### Server Components

**server.py** - MCP Server Implementation
- FastMCP-based server with async tool handlers
- Transport protocol management (stdio/SSE/HTTP)
- Error handling and validation
- CLI argument parsing

**speaker.py** - Domain Logic
- Piper TTS integration via distiller-cm5-sdk
- Audio streaming and playback management
- Service initialization and health monitoring
- Resource cleanup and error recovery

### Audio Configuration

- **Sound Card**: `snd_rpi_pamir_ai_soundcard` (Distiller CM5 default)
- **Output Directory**: `/tmp/tts_output/` for temporary files
- **Audio Format**: Streamed PCM audio via Piper
- **Playback Method**: Direct streaming to ALSA sound system

## Development

### Setup Development Environment

```bash
# Install with development dependencies
uv sync --dev

# Run type checking
uv run mypy .

# Format code
uv run black .
uv run isort .

# Run linting
uv run flake8 .
```

### Project Structure

```
speaker-mcp/
├── server.py          # MCP server with FastMCP integration
├── speaker.py         # Piper TTS domain logic and service management
├── pyproject.toml     # UV project configuration and dependencies
├── uv.lock           # Dependency lock file
└── README.md         # Project documentation
```

### Error Handling

The implementation includes comprehensive error handling:

- **Import Errors**: Graceful degradation when Piper SDK unavailable
- **Validation Errors**: Input validation with clear error messages
- **Runtime Errors**: Service failures handled with detailed error reporting
- **Cleanup**: Proper resource cleanup on server shutdown

## Troubleshooting

### Common Issues

**1. "Speaker service not available: Piper library not loaded"**
- Verify `distiller-cm5-sdk` is properly installed
- Check that the Piper library is accessible from the SDK
- Ensure all dependencies are installed with `uv sync`

**2. "Speech streaming failed" errors**
- Use `get_speaker_status` to check service health
- Verify sound card availability with `aplay -l`
- Check audio system permissions and ALSA configuration
- Ensure `/tmp/tts_output/` directory is writable

**3. Empty or invalid text input**
- Text parameter cannot be empty or whitespace-only
- Verify text encoding (UTF-8 recommended)
- Check for special characters that might cause issues

**4. Volume or audio quality issues**
- Volume parameter must be between 0-100
- Test with different volume levels
- Check system audio mixer settings (`alsamixer`)
- Verify sound card is not muted or at zero volume

### Debugging Commands

```bash
# Check service status
echo '{"method": "tools/call", "params": {"name": "get_speaker_status"}}' | uv run python server.py

# Test basic TTS functionality
echo '{"method": "tools/call", "params": {"name": "text_to_speech", "arguments": {"text": "test", "volume": 50}}}' | uv run python server.py

# Check available sound cards
aplay -l

# Test audio system
speaker-test -c 2 -r 48000 -D snd_rpi_pamir_ai_soundcard
```

## Dependencies

**Runtime:**
- Python 3.11+
- mcp[cli] >= 1.1.2 (Model Context Protocol library)
- distiller-cm5-sdk (Piper TTS integration)

**Development:**
- pytest, pytest-asyncio (testing)
- black, isort (code formatting)
- flake8 (linting)
- mypy (type checking)

## Technical Details

**Audio Processing:**
- Real-time PCM audio streaming via Piper
- No intermediate file generation for playback
- ALSA-based audio output for low latency
- Support for standard audio formats and sample rates

**MCP Integration:**
- FastMCP framework for rapid development
- Async tool handlers for non-blocking operations
- JSON-RPC based communication protocol
- Multi-transport support (stdio/SSE/HTTP) 