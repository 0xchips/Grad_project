#!/usr/bin/env python3
"""
GPS Jamming Detection Simulator for WiGuard Dashboard.
This script simulates GPS readings, detects jamming attacks, and sends alerts to the Flask server.
"""
import MySQLdb
import time
import random
import uuid
from datetime import datetime
import sys
import argparse
import requests
import json
from termcolor import colored

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'dashboard',
    'passwd': 'securepass',
    'db': 'security_dashboard',
}
DEFAULT_DEVICE_ID = 'GPS-SIM-1'
DEFAULT_LATITUDE = 31.833360
DEFAULT_LONGITUDE = 35.890387
FLASK_SERVER_URL = "http://localhost:5053"

# GPS jamming detection thresholds
JAMMING_THRESHOLD_HDOP = 2.0      # HDOP above this indicates poor signal
JAMMING_THRESHOLD_SATELLITES = 4  # Satellites below this indicates jamming
NORMAL_GPS_ACCURACY = 1.5         # Normal HDOP value

def send_gps_data_to_flask(reading):
    """Send GPS reading to Flask server for real-time dashboard updates"""
    try:
        # Send complete GPS data to the endpoint
        gps_payload = {
            'latitude': reading['latitude'],
            'longitude': reading['longitude'],
            'device_id': reading['device_id'],
            'satellites': reading['satellites'],
            'hdop': reading['hdop'],
            'jamming_detected': reading['jamming_detected']
        }
        
        gps_response = requests.post(
            f"{FLASK_SERVER_URL}/api/gps",
            json=gps_payload,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if gps_response.status_code == 201:
            status = "jamming alert" if reading['jamming_detected'] else "GPS data"
            print(colored(f"[+] {status.title()} sent to Flask server successfully", "green"))
            return True
        else:
            print(colored(f"[WARNING] Flask GPS endpoint responded with status: {gps_response.status_code}", "yellow"))
            print(colored(f"[DEBUG] Response: {gps_response.text}", "yellow"))
            return False
            
    except requests.exceptions.RequestException as e:
        print(colored(f"[WARNING] Failed to send GPS data to Flask server: {e}", "yellow"))
        return False

def send_jamming_alert_to_flask(reading):
    """Send GPS jamming alert to Flask server for real-time dashboard updates"""
    # This is now just an alias for the generic function
    return send_gps_data_to_flask(reading)

def detect_jamming(reading):
    """Analyze GPS reading to detect potential jamming"""
    jamming_indicators = []
    
    # Check HDOP (Horizontal Dilution of Precision) - higher values indicate poor accuracy
    if reading['hdop'] > JAMMING_THRESHOLD_HDOP:
        jamming_indicators.append(f"High HDOP: {reading['hdop']:.2f}")
    
    # Check satellite count - fewer satellites can indicate jamming
    if reading['satellites'] < JAMMING_THRESHOLD_SATELLITES:
        jamming_indicators.append(f"Low satellite count: {reading['satellites']}")
    
    # Check for extreme position variations (could indicate spoofing/jamming)
    # This would require storing previous readings for comparison
    
    is_jamming = len(jamming_indicators) > 0
    
    if is_jamming:
        print(colored(f"[!] GPS JAMMING DETECTED: {', '.join(jamming_indicators)}", "red"))
        reading['jamming_detected'] = 1
        reading['jamming_reasons'] = jamming_indicators
    else:
        reading['jamming_detected'] = 0
        reading['jamming_reasons'] = []
    
    return is_jamming
def simulate_gps_reading(base_lat, base_lon, device_id, simulate_jamming=False):
    """Generate a simulated GPS reading with potential jamming conditions"""
    
    # Create some variation in the position
    if simulate_jamming:
        # Larger variations and poor accuracy during jamming
        lat_variation = random.uniform(-0.05, 0.05)
        lon_variation = random.uniform(-0.05, 0.05)
        satellites = random.randint(0, 3)  # Few or no satellites during jamming
        hdop = random.uniform(3.0, 15.0)   # Poor accuracy (high HDOP)
        signal_strength = random.uniform(-50, -30)  # Weak signal
    else:
        # Normal variations
        lat_variation = random.uniform(-0.001, 0.001)
        lon_variation = random.uniform(-0.001, 0.001)
        satellites = random.randint(6, 12)  # Normal number of satellites
        hdop = random.uniform(0.8, 1.5)    # Good accuracy (low HDOP)
        signal_strength = random.uniform(-25, -10)  # Strong signal
    
    # Generate the reading
    reading = {
        'id': str(uuid.uuid4()),
        'latitude': base_lat + lat_variation,
        'longitude': base_lon + lon_variation,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'device_id': device_id,
        'satellites': satellites,
        'hdop': hdop,
        'signal_strength': signal_strength,
        'jamming_detected': 0  # Will be set by detect_jamming()
    }
    
    return reading

def save_to_database(reading):
    """Save the simulated GPS reading to the MySQL database"""
    try:
        conn = MySQLdb.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO gps_data (id, latitude, longitude, timestamp, 
                                 device_id, hdop, jamming_detected)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                reading['id'],
                reading['latitude'],
                reading['longitude'],
                reading['timestamp'],
                reading['device_id'],
                # reading['satellites'],
                reading['hdop'],
                reading['jamming_detected']
            )
        )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False

def generate_dataset(base_lat, base_lon, device_id, count=10, interval=2, jamming_probability=0.2):
    """Generate and save multiple GPS readings with jamming detection"""
    jamming_counter = 0
    normal_counter = 0
    alerts_sent = 0
    
    print(colored(f"[*] Starting GPS Jamming Detection Simulator", "cyan"))
    print(colored(f"[*] Flask server: {FLASK_SERVER_URL}", "cyan"))
    print(colored(f"[*] Simulating {count} GPS readings (interval: {interval}s)", "cyan"))
    print(colored(f"[*] Jamming probability: {jamming_probability:.0%}", "cyan"))
    
    # Test Flask server connection
    try:
        response = requests.get(f"{FLASK_SERVER_URL}/", timeout=3)
        if response.status_code == 200:
            print(colored("[+] Flask server is accessible", "green"))
        else:
            print(colored(f"[WARNING] Flask server returned status: {response.status_code}", "yellow"))
    except Exception as e:
        print(colored(f"[WARNING] Flask server not accessible: {e}", "yellow"))
    
    for i in range(count):
        # Decide if this reading will simulate jamming conditions
        simulate_jamming = random.random() < jamming_probability
        
        # Generate the reading
        reading = simulate_gps_reading(base_lat, base_lon, device_id, simulate_jamming)
        
        # Detect jamming based on GPS parameters (independent of simulation flag)
        is_jamming_detected = detect_jamming(reading)
        
        # Save to database
        if save_to_database(reading):
            # Send all readings to Flask server for real-time dashboard updates
            flask_success = send_gps_data_to_flask(reading)
            
            status = "JAMMING" if is_jamming_detected else "NORMAL"
            
            if is_jamming_detected:
                jamming_counter += 1
                if flask_success:
                    alerts_sent += 1
                
                print(colored(f"[{i+1}/{count}] {status} - Lat: {reading['latitude']:.6f}, Lon: {reading['longitude']:.6f}, "
                             f"Sats: {reading['satellites']}, HDOP: {reading['hdop']:.2f} - ALERT SENT", "red"))
            else:
                normal_counter += 1
                print(colored(f"[{i+1}/{count}] {status} - Lat: {reading['latitude']:.6f}, Lon: {reading['longitude']:.6f}, "
                             f"Sats: {reading['satellites']}, HDOP: {reading['hdop']:.2f}", "green"))
            
            # Wait for the specified interval
            if i < count - 1:
                time.sleep(interval)
        else:
            print(colored(f"[{i+1}/{count}] Failed to save reading to database", "red"))
    
    print(colored(f"\n[*] Simulation complete:", "cyan"))
    print(colored(f"    Normal readings: {normal_counter}", "green"))
    print(colored(f"    Jamming events detected: {jamming_counter}", "red"))
    print(colored(f"    Alerts sent to dashboard: {alerts_sent}", "yellow"))

def main():
    parser = argparse.ArgumentParser(description='GPS Jamming Detection Simulator for WiGuard Dashboard')
    parser.add_argument('--count', type=int, default=20, help='Number of readings to simulate')
    parser.add_argument('--interval', type=float, default=3, help='Interval between readings (seconds)')
    parser.add_argument('--jamming', type=float, default=0.3, help='Probability of jamming conditions (0-1)')
    parser.add_argument('--latitude', type=float, default=DEFAULT_LATITUDE, help='Base latitude')
    parser.add_argument('--longitude', type=float, default=DEFAULT_LONGITUDE, help='Base longitude')
    parser.add_argument('--device', type=str, default=DEFAULT_DEVICE_ID, help='Device identifier')
    parser.add_argument('--continuous', action='store_true', help='Run continuously (use Ctrl+C to stop)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not (0 <= args.jamming <= 1):
        print(colored("[ERROR] Jamming probability must be between 0 and 1", "red"))
        sys.exit(1)
    
    if args.count <= 0:
        print(colored("[ERROR] Count must be positive", "red"))
        sys.exit(1)
    
    try:
        if args.continuous:
            print(colored("[*] Starting continuous GPS jamming monitoring (Ctrl+C to stop)", "cyan"))
            while True:
                generate_dataset(args.latitude, args.longitude, args.device, 
                               args.count, args.interval, args.jamming)
                print(colored(f"\n[*] Batch complete. Starting next batch in {args.interval} seconds...", "cyan"))
                time.sleep(args.interval)
        else:
            generate_dataset(args.latitude, args.longitude, args.device, 
                            args.count, args.interval, args.jamming)
    except KeyboardInterrupt:
        print(colored("\n[*] Simulation interrupted by user", "yellow"))
    except Exception as e:
        print(colored(f"[ERROR] Simulation failed: {e}", "red"))
        sys.exit(1)

if __name__ == "__main__":
    main()
