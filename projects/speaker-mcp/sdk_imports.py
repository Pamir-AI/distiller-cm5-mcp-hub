"""
SDK Import utilities for distiller-cm5-sdk.
Handles imports from the installed SDK path at /opt/distiller-cm5-sdk.
"""

import sys
import os
from pathlib import Path

# Add the installed SDK path to Python path
SDK_PATH = "/opt/distiller-cm5-sdk"
SDK_LIB_PATH = "/opt/distiller-cm5-sdk/lib"

if os.path.exists(SDK_PATH):
    # Add the SDK path to sys.path if it's not already there
    if SDK_PATH not in sys.path:
        sys.path.insert(0, SDK_PATH)
    
    # Also add the src directory if it exists
    src_path = os.path.join(SDK_PATH, "src")
    if os.path.exists(src_path) and src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    # Set LD_LIBRARY_PATH for native library access
    if os.path.exists(SDK_LIB_PATH):
        current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
        if SDK_LIB_PATH not in current_ld_path:
            if current_ld_path:
                os.environ['LD_LIBRARY_PATH'] = f"{SDK_LIB_PATH}:{current_ld_path}"
            else:
                os.environ['LD_LIBRARY_PATH'] = SDK_LIB_PATH

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