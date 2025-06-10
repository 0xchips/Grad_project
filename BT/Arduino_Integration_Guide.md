# Arduino Nano to Flask Integration Guide

## Overview
This guide explains how to integrate your Arduino Nano with nRF24L01 module to send 2.4GHz spectrum detection data to the CyberShield Flask application for live monitoring.

## Hardware Requirements

### Option 1: ESP32 (Recommended)
- ESP32 development board (has built-in WiFi)
- nRF24L01 wireless module
- 0.96" OLED display (SSD1306)
- Jumper wires and breadboard

### Option 2: Arduino Nano + WiFi Module
- Arduino Nano
- ESP8266 WiFi module (ESP-01)
- nRF24L01 wireless module
- 0.96" OLED display (SSD1306)
- Jumper wires and breadboard

## Wiring Connections

### ESP32 + nRF24L01 + OLED
```
ESP32    | nRF24L01 | OLED (SSD1306)
---------|----------|---------------
3.3V     | VCC      | VCC
GND      | GND      | GND
GPIO 18  | SCK      | -
GPIO 19  | MISO     | -
GPIO 23  | MOSI     | -
GPIO 5   | CSN      | -
GPIO 2   | CE       | -
GPIO 21  | -        | SDA
GPIO 22  | -        | SCL
```

### Arduino Nano + ESP8266 + nRF24L01 + OLED
```
Arduino  | nRF24L01 | OLED | ESP8266
---------|----------|------|--------
3.3V     | VCC      | VCC  | VCC
GND      | GND      | GND  | GND
D13      | SCK      | -    | -
D12      | MISO     | -    | -
D11      | MOSI     | -    | -
D10      | CSN      | -    | -
D9       | CE       | -    | -
A4       | -        | SDA  | -
A5       | -        | SCL  | -
D2       | -        | -    | TX
D3       | -        | -    | RX
```

## Software Setup

### 1. Arduino IDE Libraries
Install the following libraries through the Arduino IDE Library Manager:
- Adafruit SSD1306
- Adafruit GFX Library
- WiFi (ESP32) or SoftwareSerial (Arduino Nano)
- HTTPClient (ESP32) or WiFiEsp (Arduino Nano)
- ArduinoJson

### 2. Code Configuration
Edit the following lines in `Arduino_WiFi_Enhanced.ino`:

```cpp
// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";           // Replace with your WiFi name
const char* password = "YOUR_WIFI_PASSWORD";   // Replace with your WiFi password

// Server Configuration  
const char* serverURL = "http://192.168.1.100:5053/api/bluetooth_detections";  // Replace with your server IP
```

### 3. Find Your Server IP
On your Flask server machine, run:
```bash
ip addr show
# or
ifconfig
```
Look for your network interface IP address (usually starts with 192.168.x.x or 10.x.x.x)

### 4. Verify Flask Server
Make sure your Flask application is running on port 5053:
```bash
cd /home/kali/Grad_project-chipss/Grad_project-chipss/
python3 flaskkk.py
```

## Arduino Code Features

### Original Functionality Preserved
- 2.4GHz spectrum scanning using nRF24L01
- OLED display showing spectrum visualization
- Serial output of spectrum data

### New WiFi Features Added
- Automatic WiFi connection with retry logic
- HTTP POST requests to Flask API every 5 seconds
- JSON payload with detection metadata
- WiFi status display on OLED
- Transmission status indicators
- Automatic threat level assessment

### Data Transmitted
The Arduino sends the following data to the Flask API:
```json
{
  "device_id": "NANO-2.4GHz-Scanner-001",
  "device_name": "Arduino Nano 2.4GHz Scanner",
  "signal_strength": 150,
  "max_signal": 150,
  "channel": 0,
  "rssi_value": 150,
  "detection_type": "spectrum",
  "spectrum_data": "|.:-=+*aRW.:-=+*aRW| 150",
  "raw_data": {
    "scan_channels": 64,
    "scan_method": "nRF24L01",
    "device_type": "Arduino_Nano",
    "firmware_version": "1.0"
  }
}
```

## Testing the Integration

### 1. Upload Arduino Code
1. Open `Arduino_WiFi_Enhanced.ino` in Arduino IDE
2. Select your board (ESP32 Dev Module or Arduino Nano)
3. Configure WiFi credentials and server IP
4. Upload the code

### 2. Monitor Serial Output
Open Serial Monitor at 115200 baud to see:
- WiFi connection status
- Spectrum scanning data
- HTTP transmission results

### 3. Check Web Dashboard
1. Navigate to `http://your-server-ip:5053/bluetooth`
2. Click "Test Arduino" button to check connection
3. Monitor live data updates every 5 seconds

### 4. Verify Database
Check if data is being stored:
```sql
SELECT * FROM bluetooth_detections ORDER BY timestamp DESC LIMIT 10;
```

## Troubleshooting

### WiFi Connection Issues
- Verify SSID and password are correct
- Check WiFi signal strength
- Try moving Arduino closer to router
- Verify 2.4GHz WiFi is enabled (ESP32 doesn't support 5GHz)

### No Data Transmission
- Check server IP address is correct
- Verify Flask server is running on port 5053
- Check firewall settings
- Monitor Serial output for HTTP error codes

### Database Connection Issues
- Verify MySQL service is running
- Check database credentials in Flask app
- Ensure bluetooth_detections table exists

### Hardware Issues
- Check all wiring connections
- Verify power supply (3.3V for nRF24L01)
- Test OLED display functionality
- Check nRF24L01 module integrity

## API Endpoints

### Receive Detection Data
- **POST** `/api/bluetooth_detections`
- Accepts JSON data from Arduino
- Returns detection ID and threat level

### Get Detection Data
- **GET** `/api/bluetooth_detections?hours=1&limit=50`
- Returns recent detection data
- Supports filtering by device_id, threat_level

### Get Statistics
- **GET** `/api/bluetooth_detections/stats?hours=1`
- Returns detection statistics and threat distribution

### Clear All Data
- **DELETE** `/api/bluetooth_detections/clear`
- Clears all detection data from database

## Security Considerations

1. **Network Security**: Ensure your WiFi network is secure (WPA2/WPA3)
2. **API Security**: Consider adding authentication to API endpoints
3. **Data Privacy**: Spectrum data may reveal sensitive information
4. **Physical Security**: Secure Arduino device placement

## Next Steps

1. **Multiple Sensors**: Deploy multiple Arduino scanners for wider coverage
2. **Alert System**: Add email/SMS notifications for high threats
3. **Machine Learning**: Implement pattern recognition for attack detection
4. **Mobile App**: Create mobile monitoring application
5. **Geographic Mapping**: Add location tracking for mobile scanners

## Support

For issues or questions:
1. Check Serial Monitor output for error messages
2. Verify network connectivity
3. Test individual components (WiFi, nRF24L01, OLED)
4. Review Flask application logs
5. Check database connection and table structure
