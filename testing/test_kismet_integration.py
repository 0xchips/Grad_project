#!/usr/bin/env python3

import requests
import json
import time

# Test Kismet integration endpoints
BASE_URL = "http://localhost:5050"

def test_kismet_integration():
    print("Testing Kismet Integration...")
    print("=" * 50)
    
    # Test 1: Get initial status
    print("1. Testing Kismet status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/kismet/status")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "-" * 30 + "\n")
    
    # Test 2: Start Kismet
    print("2. Testing Kismet start endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/api/kismet/start", 
                               json={"interface": "wlan0"})
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {result}")
        
        if result.get('success'):
            print("Kismet started successfully!")
            
            # Wait a moment for startup
            print("Waiting 5 seconds for Kismet to initialize...")
            time.sleep(5)
            
            # Test 3: Get status after start
            print("\n3. Testing status after start...")
            response = requests.get(f"{BASE_URL}/api/kismet/status")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            
            # Test 4: Get devices
            print("\n4. Testing devices endpoint...")
            response = requests.get(f"{BASE_URL}/api/kismet/devices")
            print(f"Status: {response.status_code}")
            devices_result = response.json()
            print(f"Response: {devices_result}")
            
            if devices_result.get('success'):
                print(f"Found {devices_result.get('count', 0)} devices")
            
            # Test 5: Stop Kismet
            print("\n5. Testing Kismet stop endpoint...")
            response = requests.post(f"{BASE_URL}/api/kismet/stop")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            
        else:
            print("Failed to start Kismet")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("Kismet integration test completed!")

if __name__ == "__main__":
    test_kismet_integration()
