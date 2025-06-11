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
    
    def text_to_speech(self, text: str, volume: int = 50, sound_card_name: Optional[str] = None) -> str:
        """
        Convert text to speech and save as WAV file.
        
        Args:
            text: Text to convert to speech
            volume: Volume level (0-100)
            sound_card_name: Optional sound card name for playback
            
        Returns:
            Path to the generated WAV file
        """
        if not self.initialized:
            raise RuntimeError("Speaker service not initialized")
        
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        if volume < 0 or volume > 100:
            raise ValueError("Volume must be between 0 and 100")
        
        try:
            # Generate WAV file
            wav_path = self.piper.get_wav_file_path(text)
            
            # Move to our output directory with a better name
            import time
            timestamp = int(time.time())
            safe_text = "".join(c for c in text[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_text = safe_text.replace(' ', '_')
            new_filename = f"tts_{timestamp}_{safe_text}.wav"
            new_path = os.path.join(self.output_directory, new_filename)
            
            # Move the file
            import shutil
            shutil.move(wav_path, new_path)
            
            logger.info(f"Generated TTS file: {new_path}")
            return new_path
            
        except Exception as e:
            raise RuntimeError(f"Text-to-speech failed: {str(e)}")
    
    def speak_stream(self, text: str, volume: int = 50, sound_card_name: Optional[str] = None) -> str:
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
    
    def list_tts_files(self) -> List[dict]:
        """
        List all generated TTS files.
        
        Returns:
            List of dictionaries containing file information
        """
        try:
            files = []
            pattern = os.path.join(self.output_directory, "*.wav")
            
            for file_path in glob.glob(pattern):
                try:
                    stat = os.stat(file_path)
                    files.append({
                        "filename": os.path.basename(file_path),
                        "path": file_path,
                        "size_bytes": stat.st_size,
                        "created": stat.st_ctime,
                        "modified": stat.st_mtime
                    })
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {e}")
            
            # Sort by creation time, newest first
            files.sort(key=lambda x: x["created"], reverse=True)
            return files
            
        except Exception as e:
            logger.error(f"Error listing TTS files: {e}")
            return []
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available TTS models.
        
        Returns:
            List of model names
        """
        try:
            if not self.piper:
                return ["Service not initialized"]
            
            models = []
            model_path = self.piper.model_path
            
            # Look for .onnx files
            for file in os.listdir(model_path):
                if file.endswith('.onnx'):
                    models.append(file)
            
            return models if models else ["en_US-amy-medium.onnx (default)"]
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return [f"Error listing models: {str(e)}"]
    
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