#!/bin/bash
# GPS System Management Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GPS_DIR="${SCRIPT_DIR}/gps"

# Display help menu
show_help() {
  echo "GPS System Management"
  echo "Usage: $0 [command]"
  echo ""
  echo "Available commands:"
  echo "  setup       Set up the GPS system (install requirements, update DB schema)"
  echo "  start       Start the GPS API service"
  echo "  stop        Stop the GPS API service"
  echo "  status      Check if the GPS API service is running"
  echo "  test        Generate test GPS data"
  echo "  optimize    Optimize frontend for faster updates"
  echo "  help        Show this help menu"
  echo ""
}

# Process commands
case "$1" in
  setup)
    ${GPS_DIR}/setup.sh
    ;;
  start)
    ${GPS_DIR}/start_gps_services.sh
    ;;
  stop)
    echo "Stopping GPS API service..."
    pkill -f "python3 .*/gps_api_adapter.py" || echo "No GPS service was running."
    ;;
  status)
    if pgrep -f "python3 .*/gps_api_adapter.py" > /dev/null; then
      echo "GPS API service is running."
      ps aux | grep "[p]ython3 .*/gps_api_adapter.py"
    else
      echo "GPS API service is not running."
    fi
    ;;
  test)
    echo "Generating test GPS data..."
    python3 ${GPS_DIR}/scripts/gps_simulator.py --count 5 --interval 0.5 --jamming 0.2
    ;;
  optimize)
    ${GPS_DIR}/optimize_frontend.sh
    ;;
  *)
    show_help
    ;;
esac
