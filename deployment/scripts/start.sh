#!/bin/bash

# DOI Application Start Script

set -e

SERVICE_NAME="doi-app"

echo "Starting DOI Application..."

# Start the systemd service
sudo systemctl start "$SERVICE_NAME"

# Check status
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✓ DOI Application started successfully"
    echo "Status:"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
else
    echo "✗ Failed to start DOI Application"
    echo "Error details:"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
    exit 1
fi

# Also start Nginx if not running
if ! sudo systemctl is-active --quiet nginx; then
    echo "Starting Nginx..."
    sudo systemctl start nginx
fi

echo ""
echo "Services status:"
echo "- DOI App: $(sudo systemctl is-active $SERVICE_NAME)"
echo "- Nginx: $(sudo systemctl is-active nginx)"
echo "- MySQL: $(sudo systemctl is-active mysql)"

echo ""
echo "Application should be available at: http://localhost/"
echo "Health check: http://localhost:5000/health"