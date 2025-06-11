# Speaker MCP Server

Text-to-Speech functionality using the Piper library for the Distiller CM5 platform.

## Features

- **Text-to-Speech Generation**: Convert text to high-quality speech using Piper TTS
- **Audio File Management**: Save generated speech as WAV files with automatic naming
- **Direct Playback**: Stream speech directly to speakers without saving files
- **File Management**: List, track, and clean up generated TTS files
- **Model Information**: Check available TTS models and service status
- **Volume Control**: Adjust playback volume levels
- **Sound Card Selection**: Choose specific audio output devices

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
# Using UV with entry point
uv run distiller-cm5-speaker-mcp

# Or directly
uv run python server.py
```

### Alternative Transport Methods

```bash
# SSE transport
uv run python server.py --transport sse --host localhost --port 3000

# HTTP transport  
uv run python server.py --transport streamable-http --host localhost --port 3000
```

## Available Tools

### 1. `text_to_speech`
Convert text to speech and optionally save as WAV file.

**Parameters:**
- `text` (str): Text to convert to speech (required)
- `volume` (int): Volume level from 0-100 (default: 50)
- `save_file` (bool): Whether to save audio file (default: True)

**Returns:** Path to saved WAV file or success message

**Example:**
```json
{
  "text": "Hello, welcome to the Distiller CM5!",
  "volume": 75,
  "save_file": true
}
```

### 2. `play_text`
Convert text to speech and play immediately without saving.

**Parameters:**
- `text` (str): Text to convert to speech and play
- `volume` (int): Volume level from 0-100 (default: 50)
- `sound_card` (str): Sound card name (default: "snd_rpi_pamir_ai_soundcard")

**Returns:** Success message indicating text was played

### 3. `list_tts_files`
List all generated TTS files with metadata.

**Parameters:** None

**Returns:** JSON formatted list of TTS files with details (filename, path, size, creation date)

### 4. `get_available_models`
Get list of available Piper TTS models.

**Parameters:** None

**Returns:** List of available TTS models

### 5. `get_speaker_status`
Get speaker service status and health information.

**Parameters:** None

**Returns:** Service status including model details, file counts, and configuration

### 6. `clean_old_files`
Clean up old TTS files, keeping only the most recent ones.

**Parameters:**
- `max_files` (int): Maximum number of files to keep (default: 10)

**Returns:** Summary of cleanup operation

## Configuration

### Audio Output
The server uses the default sound card `snd_rpi_pamir_ai_soundcard` for the Distiller CM5. You can specify different sound cards using the `sound_card` parameter in the `play_text` tool.

### File Storage
Generated TTS files are stored in `/tmp/tts_output/` with automatic timestamped naming:
- Format: `tts_{timestamp}_{text_preview}.wav`
- Files are sorted by creation time (newest first)

### TTS Model
Currently uses the `en_US-amy-medium.onnx` model from the Piper library. The model provides:
- High-quality English speech synthesis
- Natural-sounding voice (Amy)
- Optimized for real-time generation

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv sync --dev

# Run tests (if any)
uv run pytest

# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy .
```

### Project Structure

```
speaker-mcp/
├── server.py          # MCP server implementation
├── speaker.py         # Speaker domain logic (Piper integration)
├── pyproject.toml     # UV project configuration
└── README.md         # This file
```

## Troubleshooting

### Common Issues

1. **Speaker service not available**
   - Check that distiller-cm5-sdk is properly installed
   - Verify Piper models are available in the SDK
   - Check system permissions for audio devices

2. **Audio playback failures**
   - Use `get_speaker_status` to check service health
   - Verify sound card name with `aplay -l`
   - Check audio system permissions and configuration

3. **File generation errors**
   - Ensure `/tmp/tts_output/` directory is writable
   - Check available disk space
   - Verify text input is valid (non-empty)

4. **Volume or quality issues**
   - Adjust volume parameter (0-100 range)
   - Check system audio mixer settings
   - Test with different text samples

### Debugging

Use the `get_speaker_status` tool to get detailed information about:
- Service initialization status
- Available models and paths
- File counts and storage location
- Piper executable status

## Dependencies

- Python 3.11+
- MCP library (mcp[cli]>=1.1.2)
- distiller-cm5-sdk (contains Piper integration)
- Piper TTS models and executable

## Audio Formats

- **Output Format**: WAV files (16-bit, 22050 Hz)
- **Real-time Streaming**: Raw PCM audio to ALSA
- **Compression**: Uncompressed audio for best quality
- **Compatibility**: Standard WAV format playable on any audio system 