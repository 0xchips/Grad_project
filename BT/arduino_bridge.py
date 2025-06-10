#!/usr/bin/env python3
"""
Arduino Nano to Flask API Bridge
This script reads spectrum data from Arduino Nano via serial and forwards it to the Flask API.
"""

import serial
import json
import requests
import time
import threading
import logging
import sys
import signal
from datetime import datetime

# Configuration
SERIAL_PORT = '/dev/ttyUSB0'  # Change this to your Arduino's serial port (Windows: COM3, COM4, etc.)
SERIAL_BAUD = 115200
FLASK_API_URL = 'http://localhost:5053/api/bluetooth_detections'
RETRY_DELAY = 5  # seconds
MAX_RETRIES = 3

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arduino_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ArduinoBridge:
    def __init__(self):
        self.serial_conn = None
        self.running = False
        self.stats = {
            'packets_received': 0,
            'packets_sent': 0,
            'api_errors': 0,
            'serial_errors': 0,
            'last_signal': 0,
            'start_time': datetime.now()
        }
    
    def find_arduino_port(self):
        """Auto-detect Arduino serial port"""
        import serial.tools.list_ports
        
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if 'Arduino' in port.description or 'USB' in port.description:
                logger.info(f"Found potential Arduino port: {port.device} - {port.description}")
                return port.device
        
        # Common Arduino ports
        common_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', '/dev/ttyACM1', 
                       'COM3', 'COM4', 'COM5', 'COM6']
        
        for port in common_ports:
            try:
                test_serial = serial.Serial(port, SERIAL_BAUD, timeout=1)
                test_serial.close()
                logger.info(f"Found working port: {port}")
                return port
            except:
                continue
        
        return None
    
    def connect_serial(self):
        """Connect to Arduino via serial"""
        try:
            # Try configured port first
            port = SERIAL_PORT
            
            # If that fails, try to auto-detect
            if not self.test_serial_port(port):
                logger.warning(f"Configured port {port} not available, trying auto-detection...")
                port = self.find_arduino_port()
                if not port:
                    raise Exception("No Arduino found on any port")
            
            self.serial_conn = serial.Serial(port, SERIAL_BAUD, timeout=2)
            time.sleep(2)  # Wait for Arduino to reset
            
            logger.info(f"Connected to Arduino on {port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Arduino: {e}")
            return False
    
    def test_serial_port(self, port):
        """Test if a serial port is available"""
        try:
            test_serial = serial.Serial(port, SERIAL_BAUD, timeout=1)
            test_serial.close()
            return True
        except:
            return False
    
    def parse_spectrum_data(self, line):
        """Parse JSON data from Arduino"""
        try:
            # Look for data between markers
            if "===SPECTRUM_DATA_START===" in line:
                return "START"
            elif "===SPECTRUM_DATA_END===" in line:
                return "END"
            elif line.startswith('{') and line.endswith('}'):
                data = json.loads(line)
                return data
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {line[:100]}... Error: {e}")
            return None
    
    def send_to_api(self, data):
        """Send data to Flask API"""
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    FLASK_API_URL,
                    json=data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 201:
                    self.stats['packets_sent'] += 1
                    self.stats['last_signal'] = data.get('signal_strength', 0)
                    logger.info(f"✓ Data sent successfully: Signal={data.get('signal_strength', 0)}")
                    return True
                else:
                    logger.warning(f"API returned status {response.status_code}: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
        
        self.stats['api_errors'] += 1
        return False
    
    def read_serial_data(self):
        """Read and process serial data from Arduino"""
        buffer = ""
        in_data_block = False
        
        while self.running:
            try:
                if self.serial_conn and self.serial_conn.in_waiting:
                    line = self.serial_conn.readline().decode('utf-8').strip()
                    
                    if not line:
                        continue
                    
                    # Print regular serial output (spectrum display)
                    if not line.startswith('===') and not line.startswith('{'):
                        print(f"Arduino: {line}")
                        continue
                    
                    # Handle structured data
                    parsed = self.parse_spectrum_data(line)
                    
                    if parsed == "START":
                        in_data_block = True
                        buffer = ""
                    elif parsed == "END":
                        in_data_block = False
                        if buffer:
                            try:
                                data = json.loads(buffer)
                                self.stats['packets_received'] += 1
                                self.send_to_api(data)
                            except:
                                logger.error(f"Failed to parse buffered data: {buffer}")
                        buffer = ""
                    elif in_data_block and isinstance(parsed, dict):
                        # Direct JSON data
                        self.stats['packets_received'] += 1
                        self.send_to_api(parsed)
                    elif in_data_block and line.startswith('{'):
                        buffer += line
                
                time.sleep(0.1)
                
            except serial.SerialException as e:
                logger.error(f"Serial error: {e}")
                self.stats['serial_errors'] += 1
                time.sleep(1)
                
                # Try to reconnect
                if not self.connect_serial():
                    logger.error("Failed to reconnect to Arduino")
                    time.sleep(5)
            
            except Exception as e:
                logger.error(f"Unexpected error in serial reading: {e}")
                time.sleep(1)
    
    def print_stats(self):
        """Print statistics periodically"""
        while self.running:
            time.sleep(30)  # Print stats every 30 seconds
            uptime = datetime.now() - self.stats['start_time']
            
            logger.info("=== BRIDGE STATISTICS ===")
            logger.info(f"Uptime: {uptime}")
            logger.info(f"Packets received: {self.stats['packets_received']}")
            logger.info(f"Packets sent: {self.stats['packets_sent']}")
            logger.info(f"API errors: {self.stats['api_errors']}")
            logger.info(f"Serial errors: {self.stats['serial_errors']}")
            logger.info(f"Last signal: {self.stats['last_signal']}")
            logger.info("========================")
    
    def test_api_connection(self):
        """Test API connection"""
        try:
            response = requests.get(f"{FLASK_API_URL.replace('/bluetooth_detections', '/bluetooth_detections/stats')}")
            if response.status_code == 200:
                logger.info("✓ API connection test successful")
                return True
            else:
                logger.warning(f"API test returned {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False
    
    def start(self):
        """Start the bridge"""
        logger.info("Starting Arduino to Flask API Bridge...")
        logger.info(f"Serial port: {SERIAL_PORT}")
        logger.info(f"API URL: {FLASK_API_URL}")
        
        # Test API connection
        if not self.test_api_connection():
            logger.warning("API connection test failed, but continuing anyway...")
        
        # Connect to Arduino
        if not self.connect_serial():
            logger.error("Failed to connect to Arduino. Exiting.")
            return False
        
        self.running = True
        
        # Start threads
        serial_thread = threading.Thread(target=self.read_serial_data, daemon=True)
        stats_thread = threading.Thread(target=self.print_stats, daemon=True)
        
        serial_thread.start()
        stats_thread.start()
        
        logger.info("Bridge started successfully!")
        logger.info("Press Ctrl+C to stop...")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down bridge...")
            self.running = False
            
        if self.serial_conn:
            self.serial_conn.close()
        
        return True

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("Received shutdown signal")
    bridge.running = False
    sys.exit(0)

def main():
    global bridge
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    bridge = ArduinoBridge()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("""
Arduino Bridge Usage:
    python3 arduino_bridge.py                    # Run with default settings
    python3 arduino_bridge.py --port /dev/ttyUSB0  # Specify serial port
    python3 arduino_bridge.py --help              # Show this help
            """)
            return
        elif sys.argv[1] == '--port' and len(sys.argv) > 2:
            global SERIAL_PORT
            SERIAL_PORT = sys.argv[2]
            logger.info(f"Using specified port: {SERIAL_PORT}")
    
    bridge.start()

if __name__ == "__main__":
    main()
