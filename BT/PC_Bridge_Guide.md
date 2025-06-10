# Arduino Nano PC Bridge Integration Guide

## Overview
This setup uses your PC as a bridge between the Arduino Nano (which doesn't have WiFi) and the Flask database. The Arduino sends spectrum data via USB serial to the PC, which then forwards it to the database.

## Architecture
```
Arduino Nano → USB Serial → PC Bridge Script → Flask API → MySQL Database → Web Dashboard
```

## Files Created
- `Arduino_Nano_Bridge.ino` - Modified Arduino code for PC bridge communication
- `arduino_bridge.py` - Python bridge script that runs on your PC
- `test_bridge.py` - Test script to verify the system works
- `setup_bridge.sh` - Setup and installation script

## Hardware Setup

### 1. Arduino Nano Wiring
```
Arduino Nano   nRF24L01+
D13       →    SCK
D12       →    MISO
D11       →    MOSI
D10       →    CSN
D9        →    CE
3.3V      →    VCC
GND       →    GND

Arduino Nano   OLED (SSD1306)
A4        →    SDA
A5        →    SCL
5V        →    VCC
GND       →    GND
```

### 2. USB Connection
- Connect Arduino Nano to PC via USB cable
- Arduino will appear as `/dev/ttyUSB0`, `/dev/ttyACM0` (Linux) or `COM3`, `COM4` (Windows)

## Software Setup

### 1. Install Dependencies
```bash
cd /home/kali/Grad_project-chipss/Grad_project-chipss/BT
chmod +x setup_bridge.sh
./setup_bridge.sh
```

### 2. Upload Arduino Code
1. Open Arduino IDE
2. Load `Arduino_Nano_Bridge.ino`
3. Select board: "Arduino Nano"
4. Select correct port (usually `/dev/ttyUSB0` or `/dev/ttyACM0`)
5. Upload the code

### 3. Verify Arduino Connection
Open Serial Monitor (115200 baud) to see:
```
Starting 2.4GHz Scanner with PC Bridge...
Channel Layout
>      1 2  3 4  5  6 7 8  9 10 11 12 13  14                     <
Scanner initialized. Sending data to PC bridge...
|.:-=+*aRW| 75
===SPECTRUM_DATA_START===
{"device_id":"NANO-2.4GHz-Scanner-001",...}
===SPECTRUM_DATA_END===
```

## Running the Bridge

### 1. Start Flask API
```bash
cd /home/kali/Grad_project-chipss/Grad_project-chipss
python3 flaskkk.py
```

### 2. Start Bridge Script
```bash
cd /home/kali/Grad_project-chipss/Grad_project-chipss/BT
python3 arduino_bridge.py
```

The bridge will:
- Auto-detect Arduino port
- Connect to Arduino via serial
- Parse spectrum data
- Forward data to Flask API
- Display status and statistics

### 3. Test the System
```bash
python3 test_bridge.py
```

## Expected Output

### Arduino Serial Monitor
```
Starting 2.4GHz Scanner with PC Bridge...
Channel Layout
Scanner initialized. Sending data to PC bridge...
|.:-=+*aRW| 75
===SPECTRUM_DATA_START===
{"device_id":"NANO-2.4GHz-Scanner-001","signal_strength":75,...}
===SPECTRUM_DATA_END===
```

### Bridge Script Output
```
INFO - Starting Arduino to Flask API Bridge...
INFO - ✓ API connection test successful
INFO - Connected to Arduino on /dev/ttyUSB0
INFO - Bridge started successfully!
Arduino: |.:-=+*aRW| 75
INFO - ✓ Data sent successfully: Signal=75
```

### Web Dashboard
- Open `http://localhost:5053/bluetooth.html`
- Should show real-time data from Arduino
- Click "Test Arduino" to verify connection

## Troubleshooting

### Arduino Not Detected
```bash
# List all serial devices
ls /dev/tty*

# Check USB devices
lsusb

# Try different ports
python3 arduino_bridge.py --port /dev/ttyACM0
```

### Permission Issues (Linux)
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Set port permissions
sudo chmod 666 /dev/ttyUSB0
```

### Bridge Connection Issues
1. Verify Flask API is running on port 5053
2. Check Arduino is sending data (Serial Monitor)
3. Verify port in bridge script matches Arduino port
4. Check firewall settings

### No Data in Dashboard
1. Test API directly: `curl http://localhost:5053/api/bluetooth_detections`
2. Check bridge logs: `tail -f arduino_bridge.log`
3. Verify database connection
4. Refresh browser page

## Advanced Configuration

### Custom Serial Port
```bash
python3 arduino_bridge.py --port /dev/ttyACM0
```

### Bridge Script Settings
Edit `arduino_bridge.py`:
```python
SERIAL_PORT = '/dev/ttyUSB0'  # Your Arduino port
SERIAL_BAUD = 115200          # Match Arduino baud rate
FLASK_API_URL = 'http://localhost:5053/api/bluetooth_detections'
RETRY_DELAY = 5               # Seconds between retries
MAX_RETRIES = 3               # Max API retry attempts
```

### Arduino Settings
Edit `Arduino_Nano_Bridge.ino`:
```cpp
const unsigned long sendInterval = 5000; // Data transmission interval (ms)
const String deviceId = "NANO-2.4GHz-Scanner-001"; // Unique device ID
```

## Data Format

### Arduino → PC (Serial JSON)
```json
{
  "device_id": "NANO-2.4GHz-Scanner-001",
  "device_name": "Arduino Nano 2.4GHz Scanner",
  "signal_strength": 75,
  "max_signal": 75,
  "channel": 0,
  "rssi_value": 75,
  "detection_type": "spectrum",
  "spectrum_data": "|.:-=+*aRW| 75",
  "raw_data": {
    "scan_channels": 64,
    "scan_method": "nRF24L01",
    "device_type": "Arduino_Nano",
    "firmware_version": "1.0"
  }
}
```

### PC → Flask API (HTTP POST)
Same JSON format sent to `/api/bluetooth_detections`

## Monitoring and Logs

### Bridge Statistics
The bridge prints statistics every 30 seconds:
```
=== BRIDGE STATISTICS ===
Uptime: 0:05:30
Packets received: 65
Packets sent: 65
API errors: 0
Serial errors: 0
Last signal: 75
========================
```

### Log Files
- `arduino_bridge.log` - Bridge activity log
- `app.log` - Flask API log

## Running as Service (Optional)

### Create systemd service
```bash
sudo nano /etc/systemd/system/arduino-bridge.service
```

```ini
[Unit]
Description=Arduino Bluetooth Bridge
After=network.target

[Service]
Type=simple
User=kali
WorkingDirectory=/home/kali/Grad_project-chipss/Grad_project-chipss/BT
ExecStart=/usr/bin/python3 arduino_bridge.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable arduino-bridge
sudo systemctl start arduino-bridge
```

## Security Considerations

1. **USB Security**: Only connect trusted Arduino devices
2. **API Security**: Consider adding authentication to Flask API
3. **Network Security**: Use localhost for development, secure network for production
4. **Data Validation**: Bridge validates all incoming data

## Performance Optimization

### Arduino Side
- Adjust scan parameters for different sensitivity
- Modify transmission interval for more/less frequent updates
- Optimize JSON payload size

### PC Bridge
- Increase buffer sizes for high-frequency data
- Implement data compression if needed
- Add data filtering/aggregation

### Database
- Regular cleanup of old detection data
- Index optimization for time-based queries
- Consider data retention policies

---

## Quick Start Checklist

1. ☐ Upload `Arduino_Nano_Bridge.ino` to Arduino Nano
2. ☐ Connect Arduino to PC via USB
3. ☐ Run `./setup_bridge.sh` to install dependencies
4. ☐ Start Flask API: `python3 flaskkk.py`
5. ☐ Start bridge: `python3 arduino_bridge.py`
6. ☐ Test with: `python3 test_bridge.py`
7. ☐ Open dashboard: `http://localhost:5053/bluetooth.html`

The system should now be forwarding real-time 2.4GHz spectrum data from your Arduino Nano to the web dashboard through your PC!
