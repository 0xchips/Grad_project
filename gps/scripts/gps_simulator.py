#!/usr/bin/env python3
"""
GPS Data Simulator for testing the GPS jamming detection system.
This script simulates GPS readings and sends them to the MySQL database.
"""
import MySQLdb
import time
import random
import uuid
from datetime import datetime
import sys
import argparse

# MySQL database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'dashboard',
    'passwd': 'securepass',
    'db': 'security_dashboard',
}
DEFAULT_DEVICE_ID = 'GPS-SIM-1'
DEFAULT_LATITUDE = 31.833360
DEFAULT_LONGITUDE = 35.890387

def simulate_gps_reading(base_lat, base_lon, device_id, simulate_jamming=False):
    """Generate a simulated GPS reading"""
    
    # Create some variation in the position
    if simulate_jamming:
        # Larger variations and poor accuracy during jamming
        lat_variation = random.uniform(-0.05, 0.05)
        lon_variation = random.uniform(-0.05, 0.05)
        satellites = random.randint(0, 3)  # Few or no satellites during jamming
        hdop = random.uniform(2.0, 10.0)   # Poor accuracy (high HDOP)
        jamming = True
    else:
        # Normal variations
        lat_variation = random.uniform(-0.001, 0.001)
        lon_variation = random.uniform(-0.001, 0.001)
        satellites = random.randint(6, 12)  # Normal number of satellites
        hdop = random.uniform(0.8, 1.5)    # Good accuracy (low HDOP)
        jamming = False
    
    # Generate the reading
    reading = {
        'id': str(uuid.uuid4()),
        'latitude': base_lat + lat_variation,
        'longitude': base_lon + lon_variation,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'device_id': device_id,
        'satellites': satellites,
        'hdop': hdop,
        'jamming_detected': 1 if jamming else 0
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
                                 device_id, satellites, hdop, jamming_detected)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                reading['id'],
                reading['latitude'],
                reading['longitude'],
                reading['timestamp'],
                reading['device_id'],
                reading['satellites'],
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
    """Generate and save multiple GPS readings"""
    jamming_counter = 0
    normal_counter = 0
    
    print(f"Simulating {count} GPS readings (interval: {interval}s)")
    
    for i in range(count):
        # Decide if this reading will simulate jamming
        simulate_jamming = random.random() < jamming_probability
        
        # Generate and save the reading
        reading = simulate_gps_reading(base_lat, base_lon, device_id, simulate_jamming)
        if save_to_database(reading):
            status = "JAMMING" if simulate_jamming else "NORMAL"
            
            if simulate_jamming:
                jamming_counter += 1
            else:
                normal_counter += 1
                
            print(f"[{i+1}/{count}] {status} - Lat: {reading['latitude']:.6f}, Lon: {reading['longitude']:.6f}, "
                  f"Sats: {reading['satellites']}, HDOP: {reading['hdop']:.2f}")
            
            # Wait for the specified interval
            if i < count - 1:
                time.sleep(interval)
        else:
            print(f"[{i+1}/{count}] Failed to save reading to database")
    
    print(f"\nSimulation complete: {normal_counter} normal readings, {jamming_counter} jamming events")

def main():
    parser = argparse.ArgumentParser(description='GPS Jamming Simulator')
    parser.add_argument('--count', type=int, default=10, help='Number of readings to simulate')
    parser.add_argument('--interval', type=float, default=2, help='Interval between readings (seconds)')
    parser.add_argument('--jamming', type=float, default=0.2, help='Probability of jamming (0-1)')
    parser.add_argument('--latitude', type=float, default=DEFAULT_LATITUDE, help='Base latitude')
    parser.add_argument('--longitude', type=float, default=DEFAULT_LONGITUDE, help='Base longitude')
    parser.add_argument('--device', type=str, default=DEFAULT_DEVICE_ID, help='Device identifier')
    
    args = parser.parse_args()
    
    generate_dataset(args.latitude, args.longitude, args.device, 
                     args.count, args.interval, args.jamming)

if __name__ == "__main__":
    main()
