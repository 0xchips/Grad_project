#!/bin/bash
# Start GPS services for the security dashboard

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GPS_DIR=${SCRIPT_DIR}
SCRIPTS_DIR="${GPS_DIR}/scripts"

# Kill any existing GPS API instances
echo "Stopping any running GPS API instances..."
pkill -f "python3 .*/gps_api_adapter.py" || true
sleep 2

# Update database schema if needed
echo "Checking database schema..."
python3 ${SCRIPTS_DIR}/update_gps_table.py
echo ""

# Start the GPS API adapter with optimized settings
echo "Starting GPS API adapter (port 5050)..."
python3 ${SCRIPTS_DIR}/gps_api_adapter.py > /tmp/gps_adapter.log 2>&1 &
ADAPTER_PID=$!
echo "GPS API adapter started with PID: $ADAPTER_PID"

echo ""
echo "GPS API server is now running:"
echo "- GPS API adapter: http://localhost:5050"
echo ""
echo "To test the GPS API, navigate to: http://localhost:5050/api/gps/test"
echo "To view GPS data on the dashboard, navigate to: http://localhost:80/gps.html"
echo ""
echo "Log file: /tmp/gps_adapter.log"
echo ""
echo "Press CTRL+C to stop the server"

# Setup trap to kill the server when the script is terminated
trap "echo 'Stopping GPS API server...'; kill $ADAPTER_PID 2>/dev/null || true; exit 0" INT TERM

# Wait for key press
wait $ADAPTER_PID
