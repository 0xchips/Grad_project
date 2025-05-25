#!/bin/bash
# Start both Flask servers for the security dashboard

# Kill any existing Flask instances
echo "Stopping any running Flask servers..."
pkill -f "flask --app flaskkk.py" || true
pkill -f "python3 gps_api_adapter.py" || true
sleep 2

# Start the main Flask application
echo "Starting main Flask application (port 80)..."
flask --app flaskkk.py run --host=0.0.0.0 --port=80 --debug > /tmp/flask_main.log 2>&1 &
MAIN_PID=$!
echo "Main Flask app started with PID: $MAIN_PID"

# Wait a moment to ensure the first app has started
sleep 3

# Start the GPS API adapter from the organized folder
echo "Starting GPS API adapter (port 5050)..."
python3 gps/scripts/gps_api_adapter.py > /tmp/gps_adapter.log 2>&1 &
ADAPTER_PID=$!
echo "GPS API adapter started with PID: $ADAPTER_PID"

echo ""
echo "Both servers are now running:"
echo "- Main Flask app: http://localhost:80"
echo "- GPS API adapter: http://localhost:5050"
echo ""
echo "To test the GPS API, navigate to: http://localhost:5050/api/gps/test"
echo "To view GPS data on the dashboard, navigate to: http://localhost:80/gps.html"
echo ""
echo "Log files:"
echo "- Main app: /tmp/flask_main.log"
echo "- GPS adapter: /tmp/gps_adapter.log"
echo ""
echo "Press CTRL+C to stop both servers"

# Setup trap to kill both servers when the script is terminated
trap "echo 'Stopping servers...'; kill $MAIN_PID $ADAPTER_PID 2>/dev/null || true; exit 0" INT TERM

# Wait for key press
wait $MAIN_PID
