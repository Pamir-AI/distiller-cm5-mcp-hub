#!/bin/bash
# Virtual Environment Wrapper for Distiller MCP Hub
# This script ensures all Python scripts use the virtual environment

set -e

# Path to the virtual environment
VENV_PATH="/opt/distiller-mcp-hub/.venv"
SCRIPT_DIR="/opt/distiller-mcp-hub"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please reinstall the distiller-mcp-hub package"
    exit 1
fi

# Check if Python script exists
if [ $# -eq 0 ]; then
    echo "Usage: $0 <python_script> [args...]"
    echo "Example: $0 run_all_mcps.py"
    exit 1
fi

PYTHON_SCRIPT="$1"
shift

# Check if script exists
if [ ! -f "$SCRIPT_DIR/$PYTHON_SCRIPT" ]; then
    echo "Error: Python script not found: $SCRIPT_DIR/$PYTHON_SCRIPT"
    exit 1
fi

# Change to script directory and run with virtual environment
cd "$SCRIPT_DIR"
exec "$VENV_PATH/bin/python" "$PYTHON_SCRIPT" "$@" 