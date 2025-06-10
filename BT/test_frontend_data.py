#!/usr/bin/env python3
"""
Test script to verify frontend data display
"""
import requests
import json
import time
from datetime import datetime

def test_api_data():
    """Test that the API returns data in the expected format"""
    try:
        # Test the API endpoint
        url = "http://127.0.0.1:5053/api/bluetooth_detections"
        params = {"hours": 1, "limit": 10}
        
        print("Testing API endpoint...")
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API Response Status: 200")
            print(f"✓ Success: {data.get('success')}")
            print(f"✓ Count: {data.get('count', 0)}")
            
            if data.get('detections'):
                print(f"✓ Detections found: {len(data['detections'])}")
                
                # Show first detection details
                detection = data['detections'][0]
                print("\nFirst detection details:")
                for key, value in detection.items():
                    print(f"  {key}: {value}")
                
                # Verify required fields for frontend
                required_fields = ['device_id', 'signal_strength', 'threat_level', 'timestamp']
                missing_fields = []
                for field in required_fields:
                    if field not in detection:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"⚠️  Missing required fields: {missing_fields}")
                else:
                    print("✓ All required fields present")
                
                return True
            else:
                print("❌ No detections in response")
                return False
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def send_test_detection():
    """Send a test detection to ensure fresh data"""
    try:
        url = "http://127.0.0.1:5053/api/bluetooth_detections"
        
        test_data = {
            "device_id": "TEST-DEVICE-001",
            "device_name": "Test Bluetooth Device",
            "signal_strength": -55,
            "threat_level": "medium",
            "detection_type": "test",
            "channel": 1,
            "max_signal": -55,
            "rssi_value": -55,
            "spectrum_data": "test_spectrum",
            "raw_data": json.dumps({"test": True, "timestamp": datetime.now().isoformat()})
        }
        
        print("Sending test detection...")
        response = requests.post(url, json=test_data)
        
        if response.status_code == 201:
            result = response.json()
            print(f"✓ Test detection sent successfully")
            print(f"  Detection ID: {result.get('detection_id')}")
            return True
        else:
            print(f"❌ Failed to send test detection: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception sending test detection: {e}")
        return False

if __name__ == "__main__":
    print("=== Frontend Data Test ===")
    print(f"Time: {datetime.now()}")
    print()
    
    # Send a test detection first
    send_test_detection()
    time.sleep(1)
    
    # Test API data
    test_api_data()
    
    print("\n=== Test Complete ===")
    print("If API test passes but table is empty, check browser console for JavaScript errors.")
