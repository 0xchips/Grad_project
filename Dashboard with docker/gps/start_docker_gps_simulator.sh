#!/bin/bash
# Docker-aware GPS Simulator launcher

# Directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Default port for the simulator web interface
PORT=5053

# Get Docker host IP if available
DOCKER_HOST_IP=$(ip route | grep 'default' | awk '{print $3}')
if [ -z "$DOCKER_HOST_IP" ]; then
    DOCKER_HOST_IP="172.17.0.1"  # Common Docker bridge IP
fi

echo "Starting GPS Simulator with Docker-compatible settings..."
echo "Docker host IP: $DOCKER_HOST_IP"
echo "Database connection: 127.0.0.1:3306"

# Start GPS simulator with Docker-aware settings
python3 "$DIR/gps_simulator.py" \
    --port $PORT \
    --api "http://localhost:5050/api/gps" \
    --alt-api "http://127.0.0.1:5050/api/gps" \
    --db-host "127.0.0.1" \
    --db-port 3306
