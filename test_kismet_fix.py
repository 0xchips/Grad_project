#!/usr/bin/env python3
"""
Test script to validate the Kismet functionality fix
"""
import requests
import time
import json

def test_kismet_functionality():
    """Test the Kismet start/stop functionality"""
    
    print("🔄 Testing Kismet wireless monitoring functionality...")
    
    # Test 1: Start Kismet/airodump-ng
    print("\n1. Testing Kismet start...")
    try:
        response = requests.post('http://localhost:5053/api/kismet/start', 
                               json={'interface': 'wlx1cbfcece3103'}, 
                               timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Kismet/wireless monitoring started successfully!")
                tool_used = result.get('monitoring_tool', 'Unknown')
                print(f"   Tool used: {tool_used}")
                print(f"   Interface: {result.get('interface')}")
                print(f"   PID: {result.get('pid')}")
            else:
                print(f"❌ Failed to start: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error starting Kismet: {e}")
        return False
    
    # Wait a bit for process to stabilize
    print("\n⏳ Waiting 5 seconds for monitoring to stabilize...")
    time.sleep(5)
    
    # Test 2: Check status
    print("\n2. Testing Kismet status...")
    try:
        response = requests.get('http://localhost:5053/api/kismet/status', timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"⚠️ Error checking status: {e}")
    
    # Test 3: Stop Kismet
    print("\n3. Testing Kismet stop...")
    try:
        response = requests.post('http://localhost:5053/api/kismet/stop', timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Kismet/wireless monitoring stopped successfully!")
            else:
                print(f"⚠️ Stop message: {result.get('message')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error stopping Kismet: {e}")
    
    print("\n🎯 Test Summary:")
    print("- The Kismet functionality has been updated to use airodump-ng as fallback")
    print("- When Kismet is not installed, airodump-ng will be used instead")
    print("- Both tools provide wireless monitoring capabilities")
    print("- The web interface button should now work!")
    
    return True

if __name__ == "__main__":
    test_kismet_functionality()
