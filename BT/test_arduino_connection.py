#!/usr/bin/env python3
"""
Quick Arduino connection test
"""

import serial
import time

def test_arduino_connection():
    ports_to_try = ['/dev/ttyUSB0', '/dev/ttyACM0', '/dev/ttyUSB1', '/dev/ttyACM1']
    
    for port in ports_to_try:
        try:
            print(f"Testing port: {port}")
            ser = serial.Serial(port, 115200, timeout=2)
            time.sleep(2)  # Wait for Arduino to reset
            
            print(f"✓ Successfully connected to {port}")
            print("Listening for data (Ctrl+C to stop)...")
            
            # Read a few lines to see if Arduino is sending data
            for i in range(10):
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8').strip()
                    print(f"Arduino: {line}")
                time.sleep(1)
            
            ser.close()
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to {port}: {e}")
            continue
    
    print("❌ No Arduino found on any port")
    return False

if __name__ == "__main__":
    test_arduino_connection()
