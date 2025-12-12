#!/bin/bash
# Script to run the Dash dashboard application

echo "Starting Multi-Tabbed Dash Dashboard..."
echo "========================================"
echo ""
echo "Dashboard will be available at:"
echo "  - Local: http://127.0.0.1:8050"
echo "  - Network: http://$(hostname -I | awk '{print $1}'):8050"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")"
python3 app.py
