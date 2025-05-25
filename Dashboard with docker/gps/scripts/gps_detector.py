#!/usr/bin/env python3
"""
GPS Jamming Detector - Python version
This script reads data from a GPS module, detects possible jamming,
and saves the data to the MySQL security_dashboard database.
"""
import serial
import time
import MySQLdb  # Using MySQL instead of SQLite
import uuid
from datetime import datetime
import pynmea2  # For parsing NMEA GPS data
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("GPS_Detector")

# Configuration
SERIAL_PORT = '/dev/ttyUSB0'  # Change this to match your GPS module's port
BAUD_RATE = 9600
# MySQL database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'dashboard',
    'passwd': 'securepass',
    'db': 'security_dashboard',
}
DEVICE_ID = "GPS-Module-1"
CHECK_INTERVAL = 5  # Check GPS data every 5 seconds

class GPSJammingDetector:
    def __init__(self, port=SERIAL_PORT, baud=BAUD_RATE, db_config=DB_CONFIG):
        self.port = port
        self.baud = baud
        self.db_config = db_config
        self.serial = None
        self.last_valid_lat = None
        self.last_valid_lon = None
        self.satellites = 0
        self.hdop = 99.9  # Start with worst possible value
        
    def connect_gps(self):
        """Establish connection to the GPS serial port"""
        try:
            self.serial = serial.Serial(self.port, self.baud, timeout=5)
            logger.info(f"Connected to GPS on {self.port}")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to GPS: {e}")
            return False
    
    def read_gps_data(self):
        """Read and parse GPS NMEA data"""
        if not self.serial:
            logger.error("Serial connection not established")
            return False
        
        try:
            # Read several lines to make sure we get complete GPS data
            for _ in range(10):  
                if self.serial.in_waiting:
                    line = self.serial.readline().decode('ascii', errors='replace').strip()
                    
                    # Process the NMEA sentence
                    if line.startswith('$'):
                        try:
                            msg = pynmea2.parse(line)
                            
                            # GGA message contains satellites and HDOP
                            if isinstance(msg, pynmea2.GGA):
                                self.satellites = int(msg.num_sats) if msg.num_sats else 0
                                self.hdop = float(msg.horizontal_dil) if msg.horizontal_dil else 99.9
                                
                                if msg.latitude and msg.longitude:
                                    self.last_valid_lat = msg.latitude
                                    self.last_valid_lon = msg.longitude
                                    logger.debug(f"Position: {msg.latitude}, {msg.longitude}")
                                    
                            # RMC message contains the basic gps data
                            elif isinstance(msg, pynmea2.RMC) and msg.status == 'A':
                                self.last_valid_lat = msg.latitude
                                self.last_valid_lon = msg.longitude
                                logger.debug(f"RMC Position: {msg.latitude}, {msg.longitude}")
                                
                        except pynmea2.ParseError:
                            pass
            
            return self.has_valid_position()
            
        except Exception as e:
            logger.error(f"Error reading GPS data: {e}")
            return False
    
    def has_valid_position(self):
        """Check if we have valid position data"""
        return self.last_valid_lat is not None and self.last_valid_lon is not None
    
    def detect_jamming(self):
        """Detect possible GPS jamming based on satellite count and HDOP"""
        if self.satellites < 3 or self.hdop > 2.0:
            return True
        return False
    
    def save_to_database(self):
        """Save GPS data to the MySQL security_dashboard database"""
        if not self.has_valid_position():
            logger.warning("No valid position to save")
            return False
        
        try:
            conn = MySQLdb.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Generate a unique ID
            gps_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            jamming_detected = self.detect_jamming()
            
            # Insert the data - MySQL uses %s placeholders regardless of data type
            cursor.execute(
                """
                INSERT INTO gps_data (id, latitude, longitude, timestamp, 
                                     device_id, satellites, hdop, jamming_detected)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    gps_id,
                    self.last_valid_lat,
                    self.last_valid_lon,
                    timestamp,
                    DEVICE_ID,
                    self.satellites,
                    self.hdop,
                    jamming_detected
                )
            )
            
            conn.commit()
            conn.close()
            
            # Log status
            if jamming_detected:
                logger.warning("🚨 GPS Jamming Detected!")
            else:
                logger.info("GPS Signal OK.")
                
            logger.info(f"Saved GPS data: Lat={self.last_valid_lat}, Lon={self.last_valid_lon}, "
                        f"Satellites={self.satellites}, HDOP={self.hdop}")
            return True
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            return False
    
    def run(self):
        """Main loop to continuously check GPS data"""
        if not self.connect_gps():
            logger.error("Could not connect to GPS. Exiting.")
            return
        
        logger.info("GPS Jamming Detector started")
        
        try:
            while True:
                if self.read_gps_data():
                    self.save_to_database()
                else:
                    logger.warning("Waiting for valid GPS data...")
                
                time.sleep(CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("Detector stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            if self.serial:
                self.serial.close()

if __name__ == "__main__":
    # Check for command line arguments to override defaults
    if len(sys.argv) > 1:
        SERIAL_PORT = sys.argv[1]
    
    detector = GPSJammingDetector(port=SERIAL_PORT)
    detector.run()
