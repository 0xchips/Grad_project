#!/bin/bash
# GPS System Setup Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GPS_DIR="${SCRIPT_DIR}"
SCRIPTS_DIR="${GPS_DIR}/scripts"

echo "===================================================="
echo "GPS Jamming Detection System - Setup"
echo "===================================================="
echo ""

# Check if Python requirements are installed
echo "Installing Python requirements..."
${GPS_DIR}/install_gps_requirements.sh
echo ""

# Update database schema
echo "Setting up database schema..."
python3 ${SCRIPTS_DIR}/update_gps_table.py
echo ""

# Generate some test data
echo "Generating test GPS data..."
python3 ${SCRIPTS_DIR}/gps_simulator.py --count 10 --interval 0.5 --jamming 0.3
echo ""

# Optimize the frontend
echo "Optimizing frontend for faster updates..."
${GPS_DIR}/optimize_frontend.sh
echo ""

echo "===================================================="
echo "Setup completed successfully!"
echo ""
echo "To start the GPS service:"
echo "  ./start_gps_services.sh"
echo ""
echo "To access the dashboard:"
echo "  http://localhost:80/gps.html"
echo "===================================================="
