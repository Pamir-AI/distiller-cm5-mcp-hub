#!/usr/bin/env python3
"""
Test script to verify SDK imports from the installed path.
"""

import sys
import os

def test_sdk_imports():
    """Test importing SDK modules from the installed path."""
    
    print("Testing SDK imports from /opt/distiller-cm5-sdk...")
    
    # Test mic-mcp imports
    print("\n1. Testing mic-mcp SDK imports:")
    try:
        sys.path.insert(0, '/opt/distiller-mcp-hub/projects/mic-mcp')
        from sdk_imports import import_parakeet
        
        Parakeet = import_parakeet()
        if Parakeet is not None:
            print("✓ Parakeet import successful")
        else:
            print("✗ Parakeet import failed")
    except Exception as e:
        print(f"✗ Mic-mcp import test failed: {e}")
    
    # Test speaker-mcp imports
    print("\n2. Testing speaker-mcp SDK imports:")
    try:
        sys.path.insert(0, '/opt/distiller-mcp-hub/projects/speaker-mcp')
        from sdk_imports import import_piper
        
        Piper = import_piper()
        if Piper is not None:
            print("✓ Piper import successful")
        else:
            print("✗ Piper import failed")
    except Exception as e:
        print(f"✗ Speaker-mcp import test failed: {e}")
    
    # Test direct SDK path
    print("\n3. Testing direct SDK path:")
    sdk_path = "/opt/distiller-cm5-sdk"
    if os.path.exists(sdk_path):
        print(f"✓ SDK path exists: {sdk_path}")
        
        # Check for common SDK files
        expected_files = [
            "distiller_cm5_sdk",
            "src",
            "pyproject.toml",
            "setup.py"
        ]
        
        for file in expected_files:
            file_path = os.path.join(sdk_path, file)
            if os.path.exists(file_path):
                print(f"✓ Found: {file}")
            else:
                print(f"✗ Missing: {file}")
    else:
        print(f"✗ SDK path does not exist: {sdk_path}")

if __name__ == "__main__":
    test_sdk_imports() 