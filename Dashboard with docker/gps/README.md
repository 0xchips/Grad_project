# GPS Jamming Detection System

This directory contains the organized structure for the GPS jamming detection system that integrates with the security dashboard.

## Directory Structure

```
gps/
├── arduino/               # Arduino sketches for ESP32
│   └── ESP32_GPS_MySQL.ino
├── scripts/               # Python scripts for GPS functionality
│   ├── gps_api_adapter.py # API adapter for ESP32 communication
│   ├── gps_detector.py    # Script for reading GPS data from hardware
│   ├── gps_simulator.py   # Simulator for generating test data
│   ├── optimized_gps.js   # Reference optimized version of gps.js
│   └── update_gps_table.py # Database schema update script
├── GPS_README.md          # Original documentation
├── gps_instructions.md    # Detailed ESP32 setup instructions
├── install_gps_requirements.sh # Script to install Python requirements
├── optimize_frontend.sh   # Script to optimize the frontend code
├── start_gps_services.sh  # Script to start the GPS API service
└── test_gps_integration.sh # Test script for GPS integration
```

## Quick Start

1. **Start the GPS service**:
   ```bash
   cd /home/kali/Dashboard/Flask_server
   ./run_gps_service.sh
   ```

2. **Access the dashboard**:
   Open your web browser and navigate to:
   ```
   http://localhost:80/gps.html
   ```

3. **Test the API directly**:
   ```bash
   curl http://localhost:5050/api/gps/test
   ```

## System Overview

The GPS Jamming Detection system consists of:

1. **ESP32 GPS Device**: Hardware device with GPS module that connects via WiFi
2. **GPS API Adapter**: Fast API server that communicates with ESP32 and dashboard
3. **MySQL Database**: Stores GPS data and jamming alerts
4. **Web Dashboard**: Visualizes GPS data with fast updates

## Optimized Features

This organized structure includes several optimizations for faster data display:

1. **Memory Caching**: The API adapter caches recent data in memory
2. **Efficient Polling**: Frontend uses optimized API endpoints for faster updates
3. **Reduced Interval**: Data refresh rate increased from 10s to 3s
4. **Incremental Updates**: Only new data is transferred after initial load

## ESP32 Configuration

Connect your ESP32 with a GPS module and update these settings in the Arduino sketch:

```cpp
// WiFi credentials
const char* ssid = "YourWiFiName";
const char* password = "YourWiFiPassword";

// API configuration
const char* serverURL = "http://your-server-ip:5050/api/gps/fast";
const String deviceId = "ESP32-GPS-1"; 
```

## API Endpoints

The system provides these API endpoints:

- `GET /api/gps` - Get all GPS data (standard endpoint)
- `GET /api/gps/fast` - Get optimized GPS data (faster updates)
- `GET /api/gps/stats` - Get lightweight statistics
- `POST /api/gps` - Submit GPS data
- `GET /api/gps/test` - Generate test GPS data

## Troubleshooting

1. **No data on dashboard?**
   - Verify the GPS service is running: `ps aux | grep gps_api_adapter`
   - Test the API: `curl http://localhost:5050/api/gps/test`

2. **ESP32 not connecting?**
   - Check WiFi credentials
   - Verify the API server is running
   - Check the server URL in the ESP32 code

3. **Data not updating quickly?**
   - Run the optimize_frontend.sh script
   - Restart the GPS service
   - Check browser console for errors

## Further Documentation

For detailed ESP32 setup instructions, see `gps_instructions.md`.
