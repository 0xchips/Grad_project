# GPS Jamming Detection Integration

This directory contains scripts for GPS jamming detection and integration with the security dashboard.

## System Architecture

The GPS Jamming Detection system consists of the following components:

1. **ESP32 GPS Device**: Hardware device with GPS module that detects jamming and sends data to the server
2. **GPS API Adapter**: Bridge between ESP32 devices and the MySQL database
3. **MySQL Database**: Stores all GPS readings and jamming detection events
4. **Flask Dashboard**: Web interface to visualize GPS data and jamming events
5. **Simulation Tools**: For testing without real GPS hardware

## Components

1. **gps_detector.py**: Python script that reads data from a GPS module, detects possible jamming, and saves to MySQL.
2. **gps_simulator.py**: Simulator for generating fake GPS data to test the dashboard without real GPS hardware.
3. **update_gps_table.py**: Script to update the MySQL database schema with columns needed for GPS jamming detection.
4. **gps_api_adapter.py**: Flask API adapter that receives data from ESP32 devices and saves to MySQL.
5. **ESP32_GPS_MySQL.ino**: Arduino sketch for ESP32 with GPS module that sends data to the server.
6. **start_servers.sh**: Script to start both the main Flask app and the GPS API adapter.

## Setup Instructions

### Hardware Setup

Connect your GPS module (NEO-6M or similar) to your ESP32:
- Connect GPS TX → ESP32 RX (GPIO 16)
- Connect GPS RX → ESP32 TX (GPIO 17)
- Connect GPS VCC → 3.3V
- Connect GPS GND → GND

### Software Setup

1. Install required Python packages:
   ```
   ./install_gps_requirements.sh
   ```

2. Update the MySQL database schema:
   ```
   python3 update_gps_table.py
   ```

3. Start both the main Flask app and the GPS API adapter:
   ```
   ./start_servers.sh
   ```

4. Choose one of these options:

   a. Flash the ESP32 with the GPS sketch:
   - Open ESP32_GPS_MySQL.ino in Arduino IDE
   - Update WiFi credentials and server IP address
   - Upload to your ESP32 device
   
   b. Run the GPS detector script (with real GPS hardware):
   ```
   python3 gps_detector.py
   ```
   
   c. Simulate GPS data for testing:
   ```
   python3 gps_simulator.py --count 20 --interval 3 --jamming 0.3
   ```
   
   d. Use the test endpoint to generate a single GPS reading:
   ```
   curl http://localhost:5050/api/gps/test
   ```

5. Access the dashboard at:
   ```
   http://localhost:80/gps.html
   ```

## Dashboard Features

The GPS dashboard displays:
- Map with GPS coordinates and jamming events
- Accuracy over time chart
- Total satellite count
- Jamming detection status
- Complete location history table

## API Endpoints

- `GET /api/gps` - Get GPS data (parameters: hours, device_id)
- `POST /api/gps` - Submit GPS data
- `POST /api/esp32/gps` - Special endpoint for ESP32 devices (same as POST /api/gps)
- `GET /api/gps/test` - Generate and save test GPS data

## Simulator Parameters

For the GPS simulator, you can adjust:
- `--count`: Number of readings to simulate
- `--interval`: Time between readings in seconds
- `--jamming`: Probability of simulating a jamming event (0-1)
- `--latitude`, `--longitude`: Base coordinates
- `--device`: Device identifier

Example:
```
python3 gps_simulator.py --count 30 --interval 1 --jamming 0.4
```

## ESP32 Code Configuration

Update these variables in the ESP32_GPS_MySQL.ino sketch:
```cpp
// WiFi credentials
const char* ssid = "ZainFiber-2.4G-kP9f";
const char* password = "MkN30062000";

// API configuration
const char* serverURL = "http://your-server-ip:5050/api/esp32/gps";
const String deviceId = "ESP32-GPS-1"; 
```

## Port Configuration

- Main Flask app: Port 80
- GPS API adapter: Port 5050
- Serial port: By default, `/dev/ttyUSB0` (override with parameter)

Example with custom serial port:
```
python3 gps_detector.py /dev/ttyUSB1
```

## Troubleshooting

1. **No data showing on dashboard?**
   - Check that both servers are running (`./start_servers.sh`)
   - Ensure data is being added to the database (use `gps_simulator.py` to test)
   - Check API response: `curl http://localhost:5050/api/gps?hours=24`

2. **ESP32 not connecting?**
   - Verify WiFi credentials
   - Check if API adapter is running on port 5050
   - Test the API with: `curl http://localhost:5050/api/gps/test`

3. **Database issues?**
   - Ensure MySQL is running: `systemctl status mysql`
   - Check credentials in DB_CONFIG
   - Run: `python3 update_gps_table.py` to update schema
