#!/usr/bin/env python3
"""
Test script for real-time monitoring system
Tests the integration between the dashboard and real-time monitoring
"""

import requests
import time
import json

# Configuration
DASHBOARD_URL = "http://127.0.0.1:5053"

def test_monitoring_api():
    """Test the monitoring API endpoints"""
    print("🧪 Testing Real-time Monitoring Integration")
    print("=" * 50)
    
    # Test 1: Check monitoring status
    print("\n1. Testing monitoring status...")
    try:
        response = requests.get(f"{DASHBOARD_URL}/api/monitoring/status", timeout=5)
        if response.status_code == 200:
            status_data = response.json()
            print(f"   ✓ Status: {status_data['status']}")
            print(f"   ✓ Message: {status_data['message']}")
        else:
            print(f"   ✗ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error checking status: {e}")
    
    # Test 2: Test deauth logs endpoint
    print("\n2. Testing deauth logs endpoint...")
    try:
        response = requests.get(f"{DASHBOARD_URL}/api/deauth_logs", timeout=5)
        if response.status_code == 200:
            logs = response.json()
            print(f"   ✓ Found {len(logs)} existing logs")
        else:
            print(f"   ✗ Deauth logs fetch failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error fetching deauth logs: {e}")
    
    # Test 3: Test evil twin logs endpoint
    print("\n3. Testing evil twin logs endpoint...")
    try:
        test_data = {
            "ssid": "TestNetwork",
            "bssid": "11:22:33:44:55:66",
            "victim_mac": "N/A",
            "reason": "Test evil twin detection",
            "type": "evil-twin"
        }
        response = requests.post(f"{DASHBOARD_URL}/api/evil_twin_logs", json=test_data, timeout=5)
        if response.status_code == 200:
            print("   ✓ Evil twin log endpoint working")
        else:
            print(f"   ✗ Evil twin log failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error testing evil twin endpoint: {e}")
    
    # Test 4: Test dashboard accessibility
    print("\n4. Testing dashboard page...")
    try:
        response = requests.get(f"{DASHBOARD_URL}/deauth.html", timeout=5)
        if response.status_code == 200:
            print("   ✓ Dashboard page accessible")
        else:
            print(f"   ✗ Dashboard page failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error accessing dashboard: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Monitoring integration test completed!")
    print("\nNext steps:")
    print("1. Ensure you have a wireless interface in monitor mode (e.g., wlan0mon)")
    print("2. Run: sudo airmon-ng start wlan0")
    print("3. Use the dashboard to start real-time monitoring")
    print("4. Monitor the console output for WiFi packet detection")

def test_monitoring_script():
    """Test if the monitoring script exists and is executable"""
    print("\n🔧 Testing monitoring script...")
    
    import os
    script_path = "/home/kali/latest/dashboard/real_time_monitor.py"
    
    if os.path.exists(script_path):
        print(f"   ✓ Script exists: {script_path}")
        
        if os.access(script_path, os.X_OK):
            print("   ✓ Script is executable")
        else:
            print("   ⚠ Script is not executable (this is OK, will run with python3)")
        
        # Check if script has proper imports
        with open(script_path, 'r') as f:
            content = f.read()
            required_imports = ['scapy', 'requests', 'termcolor']
            missing_imports = []
            
            for imp in required_imports:
                if imp not in content:
                    missing_imports.append(imp)
            
            if not missing_imports:
                print("   ✓ Required imports found")
            else:
                print(f"   ⚠ Missing imports: {missing_imports}")
    else:
        print(f"   ✗ Script not found: {script_path}")

if __name__ == "__main__":
    print("🚀 Real-time Monitoring System Test")
    print("This test verifies the integration between the dashboard and monitoring script")
    print()
    
    test_monitoring_script()
    test_monitoring_api()
    
    print("\n📋 Manual Testing Instructions:")
    print("1. Open http://127.0.0.1:5053/deauth.html in a browser")
    print("2. Click 'Start Real-time Monitoring' button")
    print("3. Check if the monitoring status indicator turns green")
    print("4. Generate some WiFi traffic to test detection")
    print("5. Check the dashboard for new deauth/evil-twin logs")
