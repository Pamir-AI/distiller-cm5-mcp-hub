#!/bin/bash
# MCP Hub Service Management Script

SERVICE_NAME="mcp.service"
SERVICE_FILE="/home/distiller/distiller-cm5-mcp-hub/mcp.service"
SYSTEMD_DIR="/etc/systemd/system"
CONFIG_FILE="/home/distiller/distiller-cm5-mcp-hub/mcp_config.json"

show_usage() {
    echo "Usage: $0 {install|uninstall|start|stop|restart|status|logs|config|enable|disable}"
    echo ""
    echo "Commands:"
    echo "  install   - Install the service to systemd"
    echo "  uninstall - Remove the service from systemd"
    echo "  start     - Start the MCP service"
    echo "  stop      - Stop the MCP service"
    echo "  restart   - Restart the MCP service"
    echo "  status    - Show service status"
    echo "  logs      - Show service logs (follow mode)"
    echo "  config    - Edit the MCP configuration"
    echo "  enable    - Enable service to start at boot"
    echo "  disable   - Disable service from starting at boot"
}

install_service() {
    echo "Installing MCP Hub service..."
    
    if [ ! -f "$SERVICE_FILE" ]; then
        echo "Error: Service file not found at $SERVICE_FILE"
        exit 1
    fi
    
    sudo cp "$SERVICE_FILE" "$SYSTEMD_DIR/"
    sudo systemctl daemon-reload
    
    echo "Service installed successfully!"
    echo "Run '$0 enable' to enable it at boot"
    echo "Run '$0 start' to start it now"
}

uninstall_service() {
    echo "Uninstalling MCP Hub service..."
    
    sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    sudo systemctl disable "$SERVICE_NAME" 2>/dev/null || true
    sudo rm -f "$SYSTEMD_DIR/$SERVICE_NAME"
    sudo systemctl daemon-reload
    
    echo "Service uninstalled successfully!"
}

case "$1" in
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    start)
        echo "Starting MCP Hub service..."
        sudo systemctl start "$SERVICE_NAME"
        ;;
    stop)
        echo "Stopping MCP Hub service..."
        sudo systemctl stop "$SERVICE_NAME"
        ;;
    restart)
        echo "Restarting MCP Hub service..."
        sudo systemctl restart "$SERVICE_NAME"
        ;;
    status)
        sudo systemctl status "$SERVICE_NAME"
        ;;
    logs)
        echo "Showing MCP Hub logs (Ctrl+C to exit)..."
        sudo journalctl -u "$SERVICE_NAME" -f
        ;;
    config)
        if command -v nano >/dev/null 2>&1; then
            nano "$CONFIG_FILE"
        elif command -v vim >/dev/null 2>&1; then
            vim "$CONFIG_FILE"
        else
            echo "Please edit $CONFIG_FILE manually"
        fi
        echo "After editing config, restart the service with: $0 restart"
        ;;
    enable)
        echo "Enabling MCP Hub service at boot..."
        sudo systemctl enable "$SERVICE_NAME"
        ;;
    disable)
        echo "Disabling MCP Hub service at boot..."
        sudo systemctl disable "$SERVICE_NAME"
        ;;
    *)
        show_usage
        exit 1
        ;;
esac 