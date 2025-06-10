#!/usr/bin/env python3
"""
Test script to simulate Arduino data and test the bridge functionality
"""

import requests
import json
import time
import random

API_URL = 'http://localhost:5053/api/bluetooth_detections'

def generate_test_data():
    """Generate simulated Arduino spectrum data"""
    
    # Simulate varying signal strength
    signal_strength = random.randint(20, 180)
    
    # Generate spectrum visualization
    spectrum_chars = " .:-=+*aRW"
    spectrum_data = "|"
    
    for i in range(64):  # 64 channels
        intensity = random.randint(0, min(9, signal_strength // 20))
        spectrum_data += spectrum_chars[intensity]
    
    spectrum_data += f"| {signal_strength}"
    
    data = {
        "device_id": "NANO-2.4GHz-Scanner-001",
        "device_name": "Arduino Nano 2.4GHz Scanner (Simulated)",
        "signal_strength": signal_strength,
        "max_signal": signal_strength,
        "channel": 0,
        "rssi_value": signal_strength,
        "detection_type": "spectrum",
        "spectrum_data": spectrum_data,
        "raw_data": {
            "scan_channels": 64,
            "scan_method": "nRF24L01",
            "device_type": "Arduino_Nano",
            "firmware_version": "1.0"
        }
    }
    
    return data

def test_api_connection():
    """Test if Flask API is accessible"""
    try:
        # Test stats endpoint
        response = requests.get(f"{API_URL.replace('/bluetooth_detections', '/bluetooth_detections/stats')}")
        if response.status_code == 200:
            print("✓ Flask API is accessible")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Flask API: {e}")
        return False

def send_test_data():
    """Send simulated data to API"""
    data = generate_test_data()
    
    try:
        response = requests.post(API_URL, json=data, timeout=10)
        if response.status_code == 201:
            result = response.json()
            print(f"✓ Data sent successfully: Signal={data['signal_strength']}, Threat={result.get('threat_level', 'unknown')}")
            return True
        else:
            print(f"❌ API returned status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to send data: {e}")
        return False

def main():
    print("=== Arduino Bridge Test Script ===")
    print(f"Testing API endpoint: {API_URL}")
    
    # Test API connection
    if not test_api_connection():
        print("\n❌ Please make sure Flask API is running:")
        print("   cd /home/kali/Grad_project-chipss/Grad_project-chipss")
        print("   python3 flaskkk.py")
        return
    
    print("\n=== Sending Test Data ===")
    
    # Send test data every 5 seconds
    for i in range(10):  # Send 10 test packets
        print(f"\nSending packet {i+1}/10...")
        if send_test_data():
            print("  Waiting 5 seconds...")
            time.sleep(5)
        else:
            print("  Failed to send data, stopping test")
            break
    
    print("\n=== Test Complete ===")
    print("Check your dashboard at: http://localhost:5053/bluetooth.html")

if __name__ == "__main__":
    main()
