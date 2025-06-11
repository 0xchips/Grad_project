#!/usr/bin/env python3
"""
Test Kismet API authentication methods
"""
import requests
import json

def test_kismet_auth():
    base_url = "http://localhost:2501"
    
    print("=== Testing Kismet API Authentication ===")
    
    # Test 1: No authentication
    print("\n1. Testing without authentication...")
    try:
        response = requests.get(f"{base_url}/system/status.json", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Basic auth
    print("\n2. Testing with basic auth (kali:kali)...")
    try:
        response = requests.get(f"{base_url}/system/status.json", 
                              auth=('kali', 'kali'), timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Basic auth successful!")
            data = response.json()
            print(f"Kismet version: {data.get('kismet.system.version', 'Unknown')}")
        else:
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Session login
    print("\n3. Testing session login...")
    try:
        session = requests.Session()
        login_data = {
            'user': 'kali',
            'password': 'kali'
        }
        login_response = session.post(f"{base_url}/session/check_login", 
                                    data=login_data, timeout=5)
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            # Try to access API with session
            api_response = session.get(f"{base_url}/system/status.json", timeout=5)
            print(f"API access status: {api_response.status_code}")
            if api_response.status_code == 200:
                print("✓ Session login successful!")
            else:
                print(f"API Response: {api_response.text[:200]}")
        else:
            print(f"Login Response: {login_response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Check available endpoints
    print("\n4. Testing endpoints...")
    endpoints = [
        "/system/status.json",
        "/devices/last-time/0/devices.json",
        "/devices/summary/devices.json"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", 
                                  auth=('kali', 'kali'), timeout=5)
            print(f"{endpoint}: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if endpoint.endswith('devices.json'):
                    print(f"  Devices found: {len(data) if isinstance(data, list) else 'Unknown'}")
        except Exception as e:
            print(f"{endpoint}: Error - {e}")

if __name__ == "__main__":
    test_kismet_auth()
