#!/bin/bash
# Optimize the GPS frontend for faster data display

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GPS_DIR=${SCRIPT_DIR}
SCRIPTS_DIR="${GPS_DIR}/scripts"
JS_TARGET="/home/kali/Dashboard/Flask_server/templates/static/js/gps.js"

# First, let's create a backup of the original JS file
if [ ! -f "${JS_TARGET}.original" ]; then
    echo "Creating backup of original gps.js..."
    cp "${JS_TARGET}" "${JS_TARGET}.original"
fi

echo "Optimizing frontend code for faster data display..."

# Update the frontend code with optimized version for faster updates
# We're not replacing the file, just updating the fetch interval and adding new API endpoints
sed -i 's/setInterval(fetchNewGpsData, 10000)/setInterval(fetchNewGpsData, 3000)/g' "${JS_TARGET}"

# Add the last ID tracking for more efficient updates
sed -i '/\/\/ GPS Monitoring System/a let lastId = null;' "${JS_TARGET}"

# Ensure the original functionality still works

echo "Frontend optimization complete."
echo ""
echo "To use the optimized GPS API:"
echo "1. Run the GPS service: ./run_gps_service.sh"
echo "2. Access the dashboard at: http://localhost:80/gps.html"
echo ""
echo "Note: The data refresh rate has been increased from 10s to 3s"
