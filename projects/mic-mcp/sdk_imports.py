"""
SDK Import utilities for distiller-cm5-sdk.
Handles imports from the installed SDK path at /opt/distiller-cm5-sdk.
"""

import sys
import os
from pathlib import Path

# Add the installed SDK path to Python path
SDK_PATH = "/opt/distiller-cm5-sdk"
if os.path.exists(SDK_PATH):
    # Add the SDK path to sys.path if it's not already there
    if SDK_PATH not in sys.path:
        sys.path.insert(0, SDK_PATH)
    
    # Also add the src directory if it exists
    src_path = os.path.join(SDK_PATH, "src")
    if os.path.exists(src_path) and src_path not in sys.path:
        sys.path.insert(0, src_path)

def import_parakeet():
    """
    Import the Parakeet module from the installed SDK.
    
    Returns:
        The Parakeet class or None if import fails
    """
    try:
        # Try importing from the installed SDK path
        from distiller_cm5_sdk.parakeet.parakeet import Parakeet
        return Parakeet
    except ImportError as e:
        print(f"Warning: Failed to import parakeet from installed SDK: {e}")
        return None

def import_piper():
    """
    Import the Piper module from the installed SDK.
    
    Returns:
        The Piper class or None if import fails
    """
    try:
        # Try importing from the installed SDK path
        from distiller_cm5_sdk.piper.piper import Piper
        return Piper
    except ImportError as e:
        print(f"Warning: Failed to import piper from installed SDK: {e}")
        return None 