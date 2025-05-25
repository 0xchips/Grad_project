#!/usr/bin/env python3
"""
Direct Database Writer for GPS Simulator

This script serves as a fallback to write GPS data directly to the database
when the API adapter is unavailable.
"""
import argparse
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("GPS_DB_Writer")

# Check if we can import MySQL
try:
    import MySQLdb
    import MySQLdb.cursors
    MYSQL_AVAILABLE = True
except ImportError:
    logger.warning("MySQLdb not available. Direct database writing disabled.")
    MYSQL_AVAILABLE = False

# MySQL Database configuration
# Try multiple database connection options
DB_CONFIGS = [
    {
        'host': 'localhost',  # Try localhost first (for direct connections)
        'port': 3306,
        'user': 'dashboard',
        'passwd': 'securepass',
        'db': 'security_dashboard',
    },
    {
        'host': '127.0.0.1',  # Try explicit IP next
        'port': 3306,
        'user': 'dashboard',
        'passwd': 'securepass',
        'db': 'security_dashboard',
    },
    {
        'host': 'security_dashboard_db',  # Try Docker container name
        'port': 3306,
        'user': 'dashboard',
        'passwd': 'securepass',
        'db': 'security_dashboard',
    },
    {
        'host': 'db',  # Try Docker service name
        'port': 3306,
        'user': 'dashboard',
        'passwd': 'securepass',
        'db': 'security_dashboard',
    },
]

# The old static config is kept for backward compatibility
DB_CONFIG = DB_CONFIGS[0]

def write_to_database(gps_data):
    """Write GPS data directly to the database"""
    if not MYSQL_AVAILABLE:
        logger.error("MySQLdb not available. Cannot write to database.")
        return False
    
    # Try each database configuration
    last_error = None
    for config_index, db_config in enumerate(DB_CONFIGS):
        try:
            logger.info(f"Trying database connection to {db_config['host']}:{db_config.get('port', 3306)}")
            conn = MySQLdb.connect(**db_config)
            c = conn.cursor()
            
            # Generate unique ID if not provided
            if 'id' not in gps_data:
                gps_data['id'] = str(uuid.uuid4())
            
            # Use current timestamp if not provided
            if 'timestamp' not in gps_data:
                gps_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Set default values for optional fields
            satellites = gps_data.get('satellites', 0)
            hdop = gps_data.get('hdop', 99.9)
            device_id = gps_data.get('device_id', 'GPS-SIM-1')
            
            # Determine if jamming is detected (if not explicitly provided)
            if 'jamming_detected' not in gps_data:
                jamming_detected = 1 if (satellites < 3 or hdop > 2.0) else 0
            else:
                jamming_detected = gps_data['jamming_detected']
            
            # Insert into database
            c.execute(
                """
                INSERT INTO gps_data (id, latitude, longitude, timestamp, 
                                    device_id, satellites, hdop, jamming_detected)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    gps_data['id'],
                    gps_data['latitude'],
                    gps_data['longitude'],
                    gps_data['timestamp'],
                    device_id,
                    satellites,
                    hdop,
                    jamming_detected
                )
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"GPS data saved directly to database with ID: {gps_data['id']} using config {config_index+1}")
            return True
        except Exception as e:
            last_error = e
            logger.warning(f"Database connection failed for config {config_index+1} ({db_config['host']}): {e}")
    
    # If we got here, all configurations failed
    logger.error(f"All database connections failed. Last error: {last_error}")
    return False

def main():
    """Main entry point for direct database writer"""
    parser = argparse.ArgumentParser(description='GPS Direct Database Writer')
    parser.add_argument('--data', type=str, help='GPS data as JSON string')
    parser.add_argument('--file', type=str, help='File containing GPS data in JSON format')
    
    args = parser.parse_args()
    
    if args.data:
        # Parse JSON data from command line
        try:
            gps_data = json.loads(args.data)
            if write_to_database(gps_data):
                print("GPS data successfully written to database")
                return 0
            else:
                print("Failed to write GPS data to database")
                return 1
        except json.JSONDecodeError:
            logger.error("Invalid JSON data")
            return 1
    elif args.file:
        # Read JSON data from file
        try:
            with open(args.file, 'r') as f:
                gps_data = json.load(f)
                if write_to_database(gps_data):
                    print("GPS data successfully written to database")
                    return 0
                else:
                    print("Failed to write GPS data to database")
                    return 1
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error reading file: {e}")
            return 1
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
