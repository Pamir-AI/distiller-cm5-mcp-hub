#!/bin/bash

# MCP-Server Development Platform Installation Script
# For Raspberry Pi 5 (Debian-based)

set -e

echo "🚀 Installing MCP-Server Development Platform..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running on Raspberry Pi
check_platform() {
    print_step "Checking platform..."
    if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        print_warning "This script is designed for Raspberry Pi. Continuing anyway..."
    else
        print_status "Running on Raspberry Pi ✓"
    fi
}

# Update system packages
update_system() {
    print_step "Updating system packages..."
    sudo apt update
    sudo apt upgrade -y
    print_status "System updated ✓"
}

# Install dependencies
install_dependencies() {
    print_step "Installing system dependencies..."
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        git \
        curl \
        wget \
        systemd \
        build-essential \
        pkg-config \
        libffi-dev \
        libssl-dev
    print_status "System dependencies installed ✓"
}

# Install uv package manager
install_uv() {
    print_step "Installing uv package manager..."
    if ! command -v uv &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source ~/.bashrc
        export PATH="$HOME/.cargo/bin:$PATH"
        print_status "uv installed ✓"
    else
        print_status "uv already installed ✓"
    fi
}

# Install Python dependencies
install_python_deps() {
    print_step "Installing Python dependencies..."
    pip3 install -r requirements.txt
    print_status "Python dependencies installed ✓"
}

# Create necessary directories
create_directories() {
    print_step "Creating directories..."
    mkdir -p projects
    mkdir -p logs
    mkdir -p frontend/static
    mkdir -p frontend/templates
    
    # Set proper permissions
    chmod 755 projects logs
    print_status "Directories created ✓"
}

# Install systemd service
install_service() {
    print_step "Installing systemd service..."
    
    # Get the current directory
    INSTALL_DIR=$(pwd)
    
    # Update service file with correct paths
    sed "s|/home/pi/mcp-dev-platform|$INSTALL_DIR|g" config/systemd/mcp-dev-platform.service > /tmp/mcp-dev-platform.service
    
    # Install service
    sudo cp /tmp/mcp-dev-platform.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable mcp-dev-platform
    
    print_status "Service installed ✓"
}

# Create environment file
create_env_file() {
    print_step "Creating environment configuration..."
    
    if [ ! -f .env ]; then
        cat > .env << EOF
# MCP Development Platform Configuration
DEBUG=false
HOST=0.0.0.0
PORT=8000

# MCP Settings
MCP_INSPECTOR_ENABLED=true
MCP_DEFAULT_PORT=3000

# System Settings
UV_COMMAND=uv
PYTHON_COMMAND=python3
MAX_CONCURRENT_PROJECTS=10

# Security Settings
MAX_FILE_SIZE_MB=10

# Service Settings
SERVICE_USER=pi
SERVICE_GROUP=pi
EOF
        print_status "Environment file created ✓"
    else
        print_status "Environment file already exists ✓"
    fi
}

# Set up firewall (optional)
setup_firewall() {
    print_step "Setting up firewall (optional)..."
    
    if command -v ufw &> /dev/null; then
        sudo ufw allow 8000/tcp comment "MCP Dev Platform"
        sudo ufw allow 3000:3999/tcp comment "MCP Services"
        print_status "Firewall rules added ✓"
    else
        print_warning "UFW not found. Please manually configure firewall if needed."
    fi
}

# Test installation
test_installation() {
    print_step "Testing installation..."
    
    if python3 -c "import fastapi, uvicorn, pydantic, aiofiles" 2>/dev/null; then
        print_status "Python dependencies test passed ✓"
    else
        print_error "Python dependencies test failed ✗"
        exit 1
    fi
    
    if [ -f main.py ]; then
        print_status "Main application file found ✓"
    else
        print_error "Main application file not found ✗"
        exit 1
    fi
}

# Start service
start_service() {
    print_step "Starting service..."
    
    read -p "Start the service now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl start mcp-dev-platform
        sleep 3
        
        if sudo systemctl is-active --quiet mcp-dev-platform; then
            print_status "Service started successfully ✓"
            print_status "Platform available at: http://$(hostname -I | awk '{print $1}'):8000"
        else
            print_error "Service failed to start ✗"
            print_error "Check logs with: sudo journalctl -u mcp-dev-platform -f"
            exit 1
        fi
    else
        print_status "Service not started. Start manually with: sudo systemctl start mcp-dev-platform"
    fi
}

# Display final information
show_completion_info() {
    echo
    echo "🎉 Installation completed successfully!"
    echo
    echo "📋 Next steps:"
    echo "  1. Access the platform at: http://$(hostname -I | awk '{print $1}'):8000"
    echo "  2. Create your first MCP project"
    echo "  3. Upload your MCP scripts"
    echo "  4. Debug and deploy your services"
    echo
    echo "🔧 Useful commands:"
    echo "  Start service:    sudo systemctl start mcp-dev-platform"
    echo "  Stop service:     sudo systemctl stop mcp-dev-platform"
    echo "  Restart service:  sudo systemctl restart mcp-dev-platform"
    echo "  View logs:        sudo journalctl -u mcp-dev-platform -f"
    echo "  Service status:   sudo systemctl status mcp-dev-platform"
    echo
    echo "📁 Important directories:"
    echo "  Projects:         $(pwd)/projects/"
    echo "  Logs:            $(pwd)/logs/"
    echo "  Configuration:   $(pwd)/.env"
    echo
}

# Main installation process
main() {
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              MCP-Server Development Platform                 ║"
    echo "║                   Installation Script                       ║"
    echo "║                 for Raspberry Pi 5                         ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        print_error "Please do not run this script as root!"
        exit 1
    fi
    
    # Confirmation
    read -p "Continue with installation? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Installation cancelled."
        exit 0
    fi
    
    # Run installation steps
    check_platform
    update_system
    install_dependencies
    install_uv
    install_python_deps
    create_directories
    create_env_file
    install_service
    setup_firewall
    test_installation
    start_service
    show_completion_info
}

# Run main function
main "$@" 