#!/bin/bash
# Virtual Environment Wrapper for Distiller MCP Hub
# This script ensures all Python scripts use the appropriate virtual environment

set -e

# Base paths
BASE_DIR="/opt/distiller-mcp-hub"
HUB_VENV_PATH="$BASE_DIR/.venv"

# SDK integration - source activation script if available
SDK_ACTIVATE_SCRIPT="/opt/distiller-cm5-sdk/activate.sh"
if [ -f "$SDK_ACTIVATE_SCRIPT" ]; then
    echo "Sourcing SDK activation script..."
    source "$SDK_ACTIVATE_SCRIPT"
else
    # Fallback: set environment variables manually if SDK is available
    if [ -d "/opt/distiller-cm5-sdk" ]; then
        echo "Setting SDK environment variables..."
        export PYTHONPATH="/opt/distiller-cm5-sdk:/opt/distiller-cm5-sdk/src:${PYTHONPATH:-}"
        export LD_LIBRARY_PATH="/opt/distiller-cm5-sdk/lib:${LD_LIBRARY_PATH:-}"
    fi
fi

# Function to display usage
usage() {
    echo "Usage: $0 <python_script> [args...]"
    echo "       $0 --project <project_name> <python_script> [args...]"
    echo ""
    echo "Examples:"
    echo "  $0 run_all_mcps.py                           # Uses hub venv"
    echo "  $0 --project camera-mcp server.py            # Uses camera-mcp venv"
    echo "  $0 --project mic-mcp server.py               # Uses mic-mcp venv"
    echo "  $0 --project speaker-mcp server.py           # Uses speaker-mcp venv"
    echo ""
    echo "Available projects: camera-mcp, mic-mcp, speaker-mcp"
    exit 1
}

# Function to check if virtual environment exists
check_venv() {
    local venv_path="$1"
    local context="$2"
    
    if [ ! -d "$venv_path" ]; then
        echo "Error: Virtual environment not found at $venv_path"
        echo "Context: $context"
        echo "Please reinstall the distiller-mcp-hub package"
        exit 1
    fi
    
    if [ ! -f "$venv_path/bin/python" ]; then
        echo "Error: Python executable not found in virtual environment: $venv_path"
        echo "Context: $context"
        echo "Please reinstall the distiller-mcp-hub package"
        exit 1
    fi
}

# Function to run script with appropriate virtual environment
run_script() {
    local venv_path="$1"
    local script_dir="$2"
    local script_name="$3"
    shift 3
    local script_args="$@"
    
    # Check if script exists
    if [ ! -f "$script_dir/$script_name" ]; then
        echo "Error: Python script not found: $script_dir/$script_name"
        exit 1
    fi
    
    # Change to script directory and run with virtual environment
    cd "$script_dir"
    echo "Running $script_name with virtual environment: $venv_path"
    echo "Working directory: $script_dir"
    echo "Python version: $($venv_path/bin/python --version)"
    echo "SDK environment: PYTHONPATH=${PYTHONPATH:-}, LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-}"
    echo ""
    
    exec "$venv_path/bin/python" "$script_name" $script_args
}

# Check if we have any arguments
if [ $# -eq 0 ]; then
    usage
fi

# Parse arguments
if [ "$1" = "--project" ]; then
    # Project-specific execution
    if [ $# -lt 3 ]; then
        echo "Error: --project requires project name and script name"
        usage
    fi
    
    PROJECT_NAME="$2"
    SCRIPT_NAME="$3"
    shift 3
    SCRIPT_ARGS="$@"
    
    # Validate project name
    case "$PROJECT_NAME" in
        camera-mcp|mic-mcp|speaker-mcp)
            PROJECT_DIR="$BASE_DIR/projects/$PROJECT_NAME"
            PROJECT_VENV_PATH="$PROJECT_DIR/.venv"
            ;;
        *)
            echo "Error: Invalid project name: $PROJECT_NAME"
            echo "Available projects: camera-mcp, mic-mcp, speaker-mcp"
            exit 1
            ;;
    esac
    
    # Check if project directory exists
    if [ ! -d "$PROJECT_DIR" ]; then
        echo "Error: Project directory not found: $PROJECT_DIR"
        exit 1
    fi
    
    # Check virtual environment
    check_venv "$PROJECT_VENV_PATH" "project $PROJECT_NAME"
    
    # Run the script
    run_script "$PROJECT_VENV_PATH" "$PROJECT_DIR" "$SCRIPT_NAME" $SCRIPT_ARGS
    
else
    # Hub-level execution
    SCRIPT_NAME="$1"
    shift
    SCRIPT_ARGS="$@"
    
    # Check hub virtual environment
    check_venv "$HUB_VENV_PATH" "hub"
    
    # Run the script
    run_script "$HUB_VENV_PATH" "$BASE_DIR" "$SCRIPT_NAME" $SCRIPT_ARGS
fi 