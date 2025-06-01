#!/usr/bin/env python3
"""
Quick test script to verify the Kismet integration frontend functionality
"""
import requests
import time
import json

BASE_URL = "http://localhost:5050"

def test_kismet_endpoints():
    print("Testing Kismet integration endpoints...")
    
    # Test status
    print("\n1. Testing status endpoint:")
    response = requests.get(f"{BASE_URL}/api/kismet/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test devices
    print("\n2. Testing devices endpoint:")
    response = requests.get(f"{BASE_URL}/api/kismet/devices")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    print("\n3. Testing stop endpoint:")
    response = requests.post(f"{BASE_URL}/api/kismet/stop", 
                           headers={'Content-Type': 'application/json'})
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Wait a moment
    time.sleep(2)
    
    print("\n4. Testing status after stop:")
    response = requests.get(f"{BASE_URL}/api/kismet/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    print("\n5. Testing start endpoint:")
    response = requests.post(f"{BASE_URL}/api/kismet/start", 
                           headers={'Content-Type': 'application/json'},
                           json={'interface': 'wlan0'})
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    test_kismet_endpoints()
