#!/usr/bin/env python3
"""
Test script to verify BSSID to SSID mapping functionality with error handling
"""

import requests
import json
import sys
import time

def test_kismet_bssid_mapping():
    """Test the enhanced Kismet device endpoint with BSSID to SSID mapping"""
    
    print("Testing Kismet BSSID mapping with improved error handling...")
    
    # Test the endpoint multiple times to check for consistency
    for attempt in range(3):
        print(f"\n=== Test Attempt {attempt + 1} ===")
        
        try:
            response = requests.get('http://localhost:5050/api/kismet/devices', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✓ Success: {data.get('success')}")
                print(f"✓ Device Count: {data.get('count', 0)}")
                print(f"✓ BSSID Mappings Found: {len(data.get('bssid_mappings', {}))}")
                
                if data.get('bssid_mappings'):
                    print("\n=== BSSID to SSID Mappings ===")
                    for bssid, ssid in data.get('bssid_mappings', {}).items():
                        print(f"  {bssid} -> {ssid}")
                
                # Show client devices with connections
                devices = data.get('devices', [])
                client_devices = [d for d in devices if 'Client' in d.get('type', '')]
                
                if client_devices:
                    print(f"\n=== Client Devices ({len(client_devices)} found) ===")
                    for device in client_devices[:5]:  # Show first 5
                        ap = device.get('connected_ap', 'N/A')
                        ssid = device.get('connected_ssid', 'N/A')
                        print(f"  {device.get('mac')} -> {ap} ({ssid})")
                else:
                    print("\n=== No client devices found ===")
                
                # Show access points
                ap_devices = [d for d in devices if 'AP' in d.get('type', '')]
                if ap_devices:
                    print(f"\n=== Access Points ({len(ap_devices)} found) ===")
                    for device in ap_devices[:5]:  # Show first 5
                        ssid = device.get('connected_ssid', 'N/A')
                        print(f"  {device.get('mac')} -> {ssid}")
                
                print(f"\n✓ Test {attempt + 1} completed successfully")
                
            elif response.status_code == 400:
                print(f"⚠ Kismet not running (HTTP 400)")
                data = response.json()
                print(f"Message: {data.get('message', 'Unknown')}")
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                print(response.text[:200])
                
        except requests.exceptions.ConnectionError:
            print("❌ Error: Could not connect to Flask server. Make sure it's running on localhost:5050")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        
        # Wait between attempts
        if attempt < 2:
            time.sleep(2)
    
    return True

def test_kismet_status():
    """Test Kismet status endpoint"""
    try:
        print("\n=== Testing Kismet Status ===")
        response = requests.get('http://localhost:5050/api/kismet/status', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Running: {data.get('running')}")
            print(f"PID: {data.get('pid')}")
            if data.get('device_count') is not None:
                print(f"Device Count: {data.get('device_count')}")
            if data.get('api_error'):
                print(f"API Error: {data.get('api_error')}")
        else:
            print(f"Status check failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"Status check error: {e}")

if __name__ == "__main__":
    test_kismet_status()
    test_kismet_bssid_mapping()
