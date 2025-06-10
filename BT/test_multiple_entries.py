#!/usr/bin/env python3
"""
Test script to verify the Bluetooth page is showing multiple entries
"""

import requests
import time
import json

API_URL = 'http://localhost:5053/api/bluetooth_detections'

def test_multiple_entries():
    print("=== Testing Multiple Bluetooth Entries ===")
    
    # Send 5 different detections
    devices = []
    for i in range(5):
        device_data = {
            'device_id': f'TEST-MULTI-{i+1:03d}',
            'device_name': f'Multi Test Device {i+1}',
            'signal_strength': 50 + (i * 20),
            'max_signal': 50 + (i * 20),
            'channel': i % 12,
            'rssi_value': 50 + (i * 20),
            'detection_type': 'spectrum',
            'spectrum_data': f'|.:-=+*aRW| {50 + (i * 20)}',
            'raw_data': {
                'scan_channels': 64,
                'scan_method': 'nRF24L01', 
                'device_type': 'Arduino_Nano',
                'firmware_version': '1.0'
            }
        }
        
        print(f"Sending device {i+1}: {device_data['device_id']} with signal {device_data['signal_strength']}")
        
        response = requests.post(API_URL, json=device_data)
        if response.status_code == 201:
            result = response.json()
            devices.append({
                'id': result['id'],
                'device_id': device_data['device_id'],
                'signal': device_data['signal_strength'],
                'threat': result['threat_level']
            })
            print(f"  ✓ Added: ID={result['id'][:8]}..., Threat={result['threat_level']}")
        else:
            print(f"  ❌ Failed: {response.status_code} - {response.text}")
        
        time.sleep(1)  # Small delay between requests
    
    print(f"\n=== Verification ===")
    print(f"Sent {len(devices)} devices")
    
    # Check API response
    response = requests.get(f"{API_URL}?hours=1&limit=20")
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            total_detections = data.get('count', 0)
            detections = data.get('detections', [])
            
            print(f"API shows {total_detections} total detections")
            print(f"Latest {len(detections)} detections:")
            
            # Show our test devices
            test_devices_found = []
            for detection in detections:
                if detection['device_id'].startswith('TEST-MULTI-'):
                    test_devices_found.append({
                        'device_id': detection['device_id'],
                        'signal': detection['signal_strength'],
                        'threat': detection['threat_level'],
                        'id': detection['id'][:8] + '...'
                    })
            
            print(f"Found {len(test_devices_found)} of our test devices:")
            for device in test_devices_found:
                print(f"  - {device['device_id']}: Signal={device['signal']}, Threat={device['threat']}, ID={device['id']}")
            
            if len(test_devices_found) == len(devices):
                print("\n✅ SUCCESS: All test devices found in API response")
                print("\nNow check the Bluetooth dashboard at: http://localhost:5053/bluetooth.html")
                print("The table should show all these entries.")
            else:
                print(f"\n⚠️  WARNING: Only found {len(test_devices_found)} out of {len(devices)} test devices")
        else:
            print("❌ API returned unsuccessful response")
    else:
        print(f"❌ Failed to get API data: {response.status_code}")

if __name__ == "__main__":
    test_multiple_entries()
