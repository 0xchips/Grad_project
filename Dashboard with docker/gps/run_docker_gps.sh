#!/bin/bash

# Enhanced GPS Launcher for Docker environments
# This script starts both the GPS simulator and API adapter with Docker-aware settings

# Define paths
GPS_DIR="/home/kali/Grad/Grad_project/Dashboard with docker/gps"
SIMULATOR="${GPS_DIR}/gps_simulator.py"
API_ADAPTER="${GPS_DIR}/gps_api_adapter.py"
DB_WRITER="${GPS_DIR}/gps_db_writer.py"

# Make sure scripts are executable
chmod +x "$SIMULATOR" "$API_ADAPTER" "$DB_WRITER"

# Default ports
SIMULATOR_PORT=5052
API_PORT=5050

# Get Docker host IP if available
DOCKER_HOST_IP=$(ip route | grep 'default' | awk '{print $3}')
if [ -z "$DOCKER_HOST_IP" ]; then
    DOCKER_HOST_IP="172.17.0.1"  # Common Docker bridge IP
fi

# Print banner
echo "================================================="
echo "  Enhanced GPS Simulator System for Docker       "
echo "================================================="
echo "Docker host IP: $DOCKER_HOST_IP"
echo "Database connection: 127.0.0.1:3306"

# Start API adapter in background with Docker-specific settings
echo "[+] Starting GPS API adapter on port $API_PORT..."
python3 "$API_ADAPTER" > "${GPS_DIR}/api_adapter.log" 2>&1 &
API_PID=$!
echo "[+] API Adapter started with PID: $API_PID"

# Wait a moment for API to initialize
sleep 2

# Start GPS simulator in foreground with Docker-specific settings
echo "[+] Starting GPS Simulator on port $SIMULATOR_PORT..."
echo "[+] Using Docker-compatible settings for API and database connectivity"
echo "[+] Access the web interface at: http://localhost:$SIMULATOR_PORT"
echo "[+] Press Ctrl+C to stop both services"

# Run the simulator with improved settings for Docker
python3 "$SIMULATOR" \
    --port $SIMULATOR_PORT \
    --api "http://localhost:$API_PORT/api/gps" \
    --alt-api "http://127.0.0.1:$API_PORT/api/gps" \
    --db-host "127.0.0.1" \
    --db-port 3306

# When simulator stops, also stop API adapter
echo "[+] Stopping API Adapter (PID: $API_PID)..."
kill $API_PID

echo "[+] All services stopped"
