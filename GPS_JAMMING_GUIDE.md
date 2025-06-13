# GPS Jamming Detection System for WiGuard

## Overview
The GPS Jamming Detection System is an integrated component of the WiGuard security dashboard that simulates GPS readings, detects potential jamming attacks, and provides real-time monitoring through a web interface.

## Features
- **GPS Jamming Detection**: Detects jamming based on HDOP (Horizontal Dilution of Precision) and satellite count thresholds
- **Real-time Dashboard**: View GPS data and jamming alerts in real-time on the gps.html page
- **Database Integration**: Stores GPS readings and jamming events in MySQL database
- **Flask API Integration**: Sends data to Flask server for dashboard updates
- **Configurable Simulation**: Adjustable jamming probability, intervals, and location parameters
- **Color-coded Output**: Visual indicators for normal vs. jamming conditions

## Components

### 1. GPS Simulator (`gps/gps_simulator.py`)
Main script that simulates GPS readings and detects jamming attacks.

**Key Functions:**
- `simulate_gps_reading()`: Generates GPS readings with configurable jamming conditions
- `detect_jamming()`: Analyzes GPS parameters to identify potential jamming
- `send_gps_data_to_flask()`: Sends readings to Flask server for dashboard updates
- `save_to_database()`: Stores readings in MySQL database

**Jamming Detection Criteria:**
- HDOP > 2.0 (poor signal accuracy)
- Satellite count < 4 (insufficient satellites)

### 2. Flask API Integration (`flaskkk.py`)
Enhanced Flask server with `/api/gps` endpoint to receive GPS data.

**Endpoints:**
- `POST /api/gps`: Accepts GPS readings and jamming alerts
- `GET /api/gps`: Returns GPS data for dashboard display

### 3. Dashboard Interface (`templates/gps.html`)
Web interface displaying GPS data with jamming detection status.

**Features:**
- Interactive map showing GPS locations
- Real-time table with jamming status indicators
- Automatic updates every 10 seconds
- Search and filtering capabilities

## Usage

### Quick Start Scripts

Use the convenient start script:
```bash
# Quick test (5 readings)
./start_gps_simulator.sh test

# Standard monitoring (20 readings)
./start_gps_simulator.sh monitor

# Continuous monitoring
./start_gps_simulator.sh continuous

# Background mode
./start_gps_simulator.sh background
```

### Manual Usage

Basic usage:
```bash
cd gps/
python3 gps_simulator.py
```

With custom parameters:
```bash
python3 gps_simulator.py --count 10 --interval 2 --jamming 0.3
```

Continuous monitoring:
```bash
python3 gps_simulator.py --continuous --interval 5 --jamming 0.2
```

### Command Line Options

- `--count`: Number of readings to simulate (default: 20)
- `--interval`: Seconds between readings (default: 3)
- `--jamming`: Probability of jamming conditions 0-1 (default: 0.3)
- `--latitude`: Base latitude (default: 31.833360)
- `--longitude`: Base longitude (default: 35.890387)
- `--device`: Device identifier (default: GPS-SIM-1)
- `--continuous`: Run continuously until stopped

## Dashboard Access

1. Ensure Flask server is running:
   ```bash
   python3 flaskkk.py
   ```

2. Open the GPS dashboard:
   ```
   http://localhost:5053/gps.html
   ```

3. Start GPS simulator to see real-time data

## Database Schema

The `gps_data` table includes:
- `id`: Unique identifier
- `latitude`: GPS latitude
- `longitude`: GPS longitude
- `timestamp`: Reading timestamp
- `device_id`: Device identifier
- `satellites`: Number of satellites
- `hdop`: Horizontal dilution of precision
- `jamming_detected`: Boolean flag for jamming detection

## Configuration

### Jamming Detection Thresholds
Edit `gps_simulator.py` to adjust:
```python
JAMMING_THRESHOLD_HDOP = 2.0      # HDOP threshold
JAMMING_THRESHOLD_SATELLITES = 4  # Minimum satellites
```

### Flask Server URL
```python
FLASK_SERVER_URL = "http://localhost:5053"
```

### Database Configuration
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'dashboard',
    'passwd': 'securepass',
    'db': 'security_dashboard',
}
```

## Output Examples

### Normal GPS Reading
```
[1/5] NORMAL - Lat: 31.833131, Lon: 35.891002, Sats: 9, HDOP: 1.11
```

### Jamming Detection
```
[!] GPS JAMMING DETECTED: High HDOP: 11.87, Low satellite count: 2
[2/5] JAMMING - Lat: 31.828362, Lon: 35.868318, Sats: 2, HDOP: 11.87 - ALERT SENT
```

### Summary Statistics
```
[*] Simulation complete:
    Normal readings: 4
    Jamming events detected: 6
    Alerts sent to dashboard: 6
```

## Troubleshooting

### Common Issues

1. **Flask Server Connection Failed**
   - Ensure Flask server is running on port 5053
   - Check firewall settings

2. **Database Connection Error**
   - Verify MySQL service is running
   - Check database credentials in DB_CONFIG

3. **No Data in Dashboard**
   - Refresh the gps.html page
   - Check browser console for JavaScript errors
   - Verify API endpoints are responding

### Dependencies

Install required Python packages:
```bash
pip install MySQLdb termcolor requests
```

## Integration with WiGuard

The GPS jamming detection system integrates seamlessly with the WiGuard dashboard:
- Shares database with other security tools
- Uses consistent API patterns
- Follows dashboard UI/UX conventions
- Provides real-time alerts alongside other security events

## Future Enhancements

- GPS spoofing detection (coordinate jump analysis)
- Historical trend analysis
- Automated alerting (email/SMS)
- Integration with physical GPS hardware
- Machine learning-based anomaly detection
