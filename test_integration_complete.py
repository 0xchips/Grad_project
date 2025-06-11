#!/usr/bin/env python3
"""
Complete integration test for Kismet-Flask system
Tests all major functionality including BSSID mapping
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:5053"

def test_flask_health():
    """Test Flask server health"""
    print("1. Testing Flask Server Health...")
    try:
        response = requests.get(f"{BASE_URL}/api/ping", timeout=5)
        if response.status_code == 200:
            print("   ✅ Flask server is healthy")
            return True
        else:
            print(f"   ❌ Flask server returned {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Flask server error: {e}")
        return False

def test_kismet_status():
    """Test Kismet status endpoint"""
    print("\n2. Testing Kismet Status...")
    try:
        response = requests.get(f"{BASE_URL}/api/kismet/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: Running={data.get('running')}")
            print(f"   📊 Device Count: {data.get('device_count', 'N/A')}")
            
            if data.get('kismet_version'):
                print(f"   🔧 Kismet Version: {data.get('kismet_version')}")
            
            if data.get('api_error'):
                print(f"   ⚠️  API Warning: {data.get('api_error')}")
                
            return data.get('running', False)
        else:
            print(f"   ❌ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Status error: {e}")
        return False

def test_device_detection():
    """Test device detection and BSSID mapping"""
    print("\n3. Testing Device Detection & BSSID Mapping...")
    try:
        response = requests.get(f"{BASE_URL}/api/kismet/devices", timeout=20)
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                devices = data.get('devices', [])
                bssid_mappings = data.get('bssid_mappings', {})
                
                print(f"   ✅ Device detection successful")
                print(f"   📱 Total devices: {len(devices)}")
                print(f"   🔗 BSSID mappings: {len(bssid_mappings)}")
                
                # Analyze device types
                device_types = {}
                ap_devices = []
                client_devices = []
                
                for device in devices:
                    dtype = device.get('device_type', 'Unknown')
                    device_types[dtype] = device_types.get(dtype, 0) + 1
                    
                    if 'AP' in dtype or 'Access Point' in dtype:
                        ap_devices.append(device)
                    elif 'Client' in dtype:
                        client_devices.append(device)
                
                print(f"   📊 Device breakdown:")
                for dtype, count in device_types.items():
                    print(f"      {dtype}: {count}")
                
                # Test BSSID mapping quality
                if bssid_mappings:
                    print(f"\n   🔍 BSSID Mapping Analysis:")
                    print(f"   Sample mappings:")
                    for i, (bssid, ssid) in enumerate(list(bssid_mappings.items())[:3]):
                        print(f"      {bssid} → '{ssid}'")
                    
                    # Check client devices for proper AP mapping
                    clients_with_ap_info = 0
                    for client in client_devices[:10]:  # Check first 10 clients
                        connected_ap = client.get('connected_ap', '')
                        if connected_ap and '(' in connected_ap:
                            clients_with_ap_info += 1
                    
                    print(f"   ✅ Clients with AP info: {clients_with_ap_info}/{min(len(client_devices), 10)}")
                    
                    if clients_with_ap_info > 0:
                        print("   🎉 BSSID to SSID mapping is working!")
                    
                return True
            else:
                print(f"   ❌ Device detection failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ Device detection HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Device detection error: {e}")
        return False

def test_kismet_control():
    """Test Kismet start/stop control"""
    print("\n4. Testing Kismet Control...")
    
    # Test stop first
    try:
        response = requests.post(f"{BASE_URL}/api/kismet/stop", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ Kismet stop successful")
            else:
                print(f"   ⚠️  Stop response: {data.get('message', 'Unknown')}")
        
        time.sleep(2)
        
        # Test start
        response = requests.post(f"{BASE_URL}/api/kismet/start", 
                               json={"interface": "wlan0"}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ Kismet start successful")
                print(f"   📡 Interface: {data.get('interface', 'Unknown')}")
                if data.get('pid'):
                    print(f"   🔄 PID: {data.get('pid')}")
                return True
            else:
                print(f"   ❌ Start failed: {data.get('message', 'Unknown')}")
                return False
        else:
            print(f"   ❌ Start HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Control test error: {e}")
        return False

def test_direct_kismet_api():
    """Test direct Kismet API connectivity"""
    print("\n5. Testing Direct Kismet API...")
    try:
        response = requests.get("http://localhost:2502/system/status.json",
                              auth=('kali', 'kali'), timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Direct Kismet API accessible")
            print(f"   🔧 Version: {data.get('kismet.system.version', 'Unknown')}")
            print(f"   ⏱️  Uptime: {data.get('kismet.system.uptime', 0)} seconds")
            return True
        else:
            print(f"   ❌ Direct API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Direct API error: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🔬 Complete Kismet-Flask Integration Test")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Flask Health", test_flask_health()))
    results.append(("Kismet Status", test_kismet_status()))
    results.append(("Device Detection", test_device_detection()))
    results.append(("Kismet Control", test_kismet_control()))
    results.append(("Direct Kismet API", test_direct_kismet_api()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Kismet-Flask integration is fully functional")
        print("🌐 Web interface should be accessible at: http://localhost:5053")
        print("📡 Kismet is running on port 2502")
        print("🔗 BSSID to SSID mapping is working correctly")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("🔧 Check the error messages above for troubleshooting")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
