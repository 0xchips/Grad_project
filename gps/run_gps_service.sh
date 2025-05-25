#!/bin/bash
# GPS Service Adapter - Redirects to organized folder structure

echo "Running GPS service from organized directory structure..."
exec /home/kali/Dashboard/Flask_server/gps/start_gps_services.sh "$@"
