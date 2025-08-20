#!/bin/bash

# DOI Application Stop Script

set -e

SERVICE_NAME="doi-app"

echo "Stopping DOI Application..."

# Stop the systemd service
sudo systemctl stop "$SERVICE_NAME"

# Check status
if ! sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✓ DOI Application stopped successfully"
else
    echo "✗ DOI Application may still be running"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
fi

echo ""
echo "Services status:"
echo "- DOI App: $(sudo systemctl is-active $SERVICE_NAME)"
echo "- Nginx: $(sudo systemctl is-active nginx)"
echo "- MySQL: $(sudo systemctl is-active mysql)"

echo ""
echo "DOI Application has been stopped."
echo "Note: Nginx and MySQL are still running."