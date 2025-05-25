# GPS Jamming Detection System

This directory contains the organized structure for the GPS jamming detection system that integrates with the security dashboard.

## Directory Structure

```
gps/
├── arduino/               # Arduino sketches for ESP32
│   └── ESP32_GPS_MySQL.ino
├── gps_api_adapter.py     # API adapter for ESP32 communication
├── gps_simulator.py       # Simulator for generating test data
├── gps_db_writer.py       # Direct database writer for fallback connectivity
├── start_gps_simulator.sh # Script to start both simulator and API adapter
├── start_docker_gps_simulator.sh # Docker-compatible simulator launcher
├── GPS_README.md          # Original documentation
├── gps_instructions.md    # Detailed ESP32 setup instructions
└── README.md              # This file
```

## Quick Start

1. **Start the complete GPS system (API adapter + simulator)**:
   ```bash
   ./start_gps_simulator.sh
   ```

2. **Start the simulator in Docker-compatible mode**:
   ```bash
   ./start_docker_gps_simulator.sh
   ```

3. **Access the simulator web interface**:
   ```
   http://localhost:5051
   ```

4. **Test the API directly**:
   ```bash
   curl http://localhost:5050/api/gps/test
   ```

## System Overview

The GPS Jamming Detection system consists of:

1. **ESP32 GPS Device**: Hardware device with GPS module that connects via WiFi
2. **GPS API Adapter**: Fast API server that communicates with ESP32 and dashboard
3. **GPS Simulator**: Web-based tool to generate test data
4. **MySQL Database**: Stores GPS data and jamming alerts
5. **Web Dashboard**: Visualizes GPS data with fast updates

## Resilient Architecture

The system is designed to be resilient to connectivity issues:

1. **Multiple API Endpoints**: The simulator tries several API endpoints in sequence
2. **Retry Logic**: Each endpoint is tried multiple times with exponential backoff
3. **Direct Database Fallback**: If all API endpoints fail, data is written directly to the database
4. **Multiple Database Configurations**: The DB writer tries multiple connection parameters

## Docker Compatibility

The system is now fully compatible with Docker deployments:

1. **Docker Network Detection**: Automatically detects Docker network settings
2. **Multiple Connection Methods**: Tries various network paths to reach services
3. **Fallback Mechanisms**: Multiple layers of fallback for reliable operation

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
- `POST /api/gps` - Submit GPS data
- `POST /api/esp32/gps` - Submit GPS data from ESP32 devices
- `GET /api/gps/test` - Generate test GPS data

## Troubleshooting

1. **No data on dashboard?**
   - Check Docker connectivity: `docker ps` to verify containers are running
   - Run the Docker-compatible launcher: `./start_docker_gps_simulator.sh`
   - Test the API: `curl http://localhost:5050/api/gps/test`

2. **ESP32 not connecting?**
   - Ensure ESP32 is on the same network as the host
   - Try using the Docker host IP in the ESP32 configuration
   - Verify the API adapter is running

3. **Database connection issues?**
   - Check Docker container status: `docker ps`
   - Verify MySQL port is exposed: `docker-compose ps`
   - Use direct IP address instead of `localhost`
