"""
Text-to-Speech domain logic using Piper.

Keep all TTS-specific code here, separate from MCP logic.
"""

import logging
import os
import glob
from typing import List, Optional

logger = logging.getLogger(__name__)

class Speaker:
    """Domain logic for text-to-speech using Piper."""
    
    def __init__(self):
        """Initialize the speaker service."""
        self.initialized = False
        self.piper = None
        self.output_directory = "/tmp/tts_output"
        
        try:
            self._initialize()
            self.initialized = True
            logger.info("Speaker service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize speaker service: {e}")
            # Don't raise - allow graceful degradation
    
    def _initialize(self):
        """Initialize Piper TTS."""
        try:
            from distiller_cm5_sdk.piper.piper import Piper
            self.piper = Piper()
            
            # Create output directory if it doesn't exist
            os.makedirs(self.output_directory, exist_ok=True)
            
        except ImportError as e:
            raise RuntimeError(f"Failed to import Piper library: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Piper: {e}")
    
    def speak_stream(self, text: str, volume: int = 50, sound_card_name: Optional[str] = "snd_rpi_pamir_ai_soundcard") -> str:
        """
        Convert text to speech and play directly (streaming).
        
        Args:
            text: Text to convert to speech
            volume: Volume level (0-100)
            sound_card_name: Optional sound card name for playback
            
        Returns:
            Success message
        """
        if not self.initialized:
            raise RuntimeError("Speaker service not initialized")
        
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        if volume < 0 or volume > 100:
            raise ValueError("Volume must be between 0 and 100")
        
        try:
            self.piper.speak_stream(text, volume, sound_card_name)
            return f"Successfully played text: '{text[:50]}{'...' if len(text) > 50 else ''}'"
            
        except Exception as e:
            raise RuntimeError(f"Speech streaming failed: {str(e)}")
    
    def get_status(self) -> str:
        """Get current speaker service status."""
        if not self.initialized:
            return "Not initialized - Piper library not available"
        
        try:
            model_info = f"Model: {os.path.basename(self.piper.voice_onnx)}"
            file_count = len(glob.glob(os.path.join(self.output_directory, "*.wav")))
            
            return f"""Speaker Service Status:
- Service: Running normally
- {model_info}
- Output directory: {self.output_directory}
- Generated files: {file_count}
- Piper executable: {self.piper.piper}"""
        except Exception as e:
            return f"Service error: {str(e)}"
    
    def cleanup(self):
        """Clean up resources."""
        try:
            # Piper doesn't need explicit cleanup, but we could clean old files
            logger.info("Speaker service cleaned up")
        except Exception as e:
            logger.error(f"Cleanup error: {e}") 