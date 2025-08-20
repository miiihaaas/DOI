#!/bin/bash

# DOI Application Restart Script

set -e

SERVICE_NAME="doi-app"

echo "Restarting DOI Application..."

# Restart the systemd service
sudo systemctl restart "$SERVICE_NAME"

# Wait a moment for service to start
sleep 2

# Check status
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✓ DOI Application restarted successfully"
    echo "Status:"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
else
    echo "✗ Failed to restart DOI Application"
    echo "Error details:"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
    exit 1
fi

echo ""
echo "Services status:"
echo "- DOI App: $(sudo systemctl is-active $SERVICE_NAME)"
echo "- Nginx: $(sudo systemctl is-active nginx)" 
echo "- MySQL: $(sudo systemctl is-active mysql)"

echo ""
echo "Application should be available at: http://localhost/"
echo "Health check: http://localhost:5000/health"