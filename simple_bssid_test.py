#!/usr/bin/env python3
"""
Simple direct test of the current BSSID mapping implementation
"""

import requests
import json
import subprocess

def test_direct_kismet_api():
    """Test Kismet API directly"""
    try:
        print("=== Testing Direct Kismet API ===")
        
        # Get devices directly from Kismet
        response = requests.get(
            'http://localhost:2501/devices/last-time/0/devices.json',
            auth=('kali', 'kali'),
            timeout=5
        )
        
        if response.status_code == 200:
            devices = response.json()
            print(f"✅ Direct Kismet API: {len(devices)} devices found")
            
            # Look for Access Points and Client devices
            aps = []
            clients = []
            
            for device in devices:
                device_type = device.get('kismet.device.base.type', 'Unknown')
                mac = device.get('kismet.device.base.macaddr', 'Unknown')
                name = device.get('kismet.device.base.name', 'Unknown')
                
                if 'AP' in device_type or 'Access Point' in device_type:
                    # Try to get SSID from AP
                    dot11_device = device.get('dot11.device', {})
                    if dot11_device:
                        advertised_ssid_map = dot11_device.get('dot11.device.advertised_ssid_map', {})
                        ssid = 'Unknown SSID'
                        
                        if isinstance(advertised_ssid_map, dict):
                            for ssid_key, ssid_data in advertised_ssid_map.items():
                                if isinstance(ssid_data, dict):
                                    ssid = ssid_data.get('dot11.advertisedssid.ssid', ssid)
                                    if ssid:
                                        break
                        
                        aps.append({
                            'mac': mac,
                            'name': name,
                            'ssid': ssid,
                            'type': device_type
                        })
                
                elif 'Client' in device_type:
                    clients.append({
                        'mac': mac,
                        'name': name,
                        'type': device_type
                    })
            
            print(f"📡 Access Points found: {len(aps)}")
            for ap in aps[:3]:  # Show first 3
                print(f"   {ap['mac']} → {ap['ssid']} ({ap['name']})")
            
            print(f"📱 Client devices found: {len(clients)}")
            for client in clients[:3]:  # Show first 3
                print(f"   {client['mac']} ({client['name']})")
            
            return len(devices) > 0
            
        else:
            print(f"❌ Kismet API error: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_flask_api_simple():
    """Simple test of Flask API"""
    try:
        print("\n=== Testing Flask API (Simple) ===")
        
        # Test with a longer timeout
        response = requests.get('http://localhost:5050/api/kismet/status', timeout=15)
        
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Flask API Status: Running={status.get('running')}")
            print(f"   Device Count: {status.get('device_count', 'N/A')}")
            return True
        else:
            print(f"❌ Flask API error: HTTP {response.status_code}")
            print(f"   Response: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🔍 Simple BSSID Mapping Test")
    print("=" * 50)
    
    # Test direct Kismet API
    kismet_ok = test_direct_kismet_api()
    
    # Test Flask API status
    flask_ok = test_flask_api_simple()
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print(f"Direct Kismet API: {'✅ Working' if kismet_ok else '❌ Failed'}")
    print(f"Flask API Status: {'✅ Working' if flask_ok else '❌ Failed'}")
    
    if kismet_ok and flask_ok:
        print("\n💡 Both APIs are working. The BSSID mapping should be functional.")
        print("   Try accessing the web interface to see the client devices")
        print("   with 'BSSID (SSID)' format in the connected_ap field.")
    elif kismet_ok:
        print("\n⚠️  Kismet is working but Flask API has issues.")
        print("   Check Flask app logs for timeout or processing errors.")
    else:
        print("\n❌ Kismet API is not responding. Check Kismet configuration.")

if __name__ == "__main__":
    main()
