#!/bin/bash

# GPS Jamming Simulator Quick Start Script
# Usage: ./start_gps_simulator.sh [mode]
# Modes: test, monitor, continuous

GPS_DIR="/home/ubuntu/latest/Grad_project/gps"
SIMULATOR="gps_simulator.py"

case "$1" in
    "test")
        echo "Starting GPS jamming simulator in test mode (5 readings)..."
        cd "$GPS_DIR" && python3 "$SIMULATOR" --count 5 --interval 2 --jamming 0.4
        ;;
    "monitor")
        echo "Starting GPS jamming simulator in monitoring mode (20 readings)..."
        cd "$GPS_DIR" && python3 "$SIMULATOR" --count 20 --interval 3 --jamming 0.25
        ;;
    "continuous")
        echo "Starting GPS jamming simulator in continuous mode..."
        echo "Press Ctrl+C to stop"
        cd "$GPS_DIR" && python3 "$SIMULATOR" --continuous --count 10 --interval 5 --jamming 0.2
        ;;
    "background")
        echo "Starting GPS jamming simulator in background mode..."
        cd "$GPS_DIR" && python3 "$SIMULATOR" --continuous --count 15 --interval 10 --jamming 0.15 &
        echo "Background GPS simulator started. Use 'pkill -f gps_simulator' to stop."
        ;;
    *)
        echo "GPS Jamming Simulator Quick Start"
        echo "Usage: $0 [mode]"
        echo ""
        echo "Available modes:"
        echo "  test       - Quick test with 5 readings (40% jamming probability)"
        echo "  monitor    - Standard monitoring with 20 readings (25% jamming probability)"
        echo "  continuous - Continuous monitoring until stopped (20% jamming probability)"
        echo "  background - Run continuously in background (15% jamming probability)"
        echo ""
        echo "Examples:"
        echo "  $0 test        # Quick test"
        echo "  $0 monitor     # Standard monitoring"
        echo "  $0 continuous  # Continuous mode"
        echo "  $0 background  # Background mode"
        ;;
esac
